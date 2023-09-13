import os
import sys
import torch
import argparse
import config
from torch import nn
from torch import optim
from utils import gradient_penalty, load_checkpoint, save_checkpoint, plot_examples, load_model
from loss import VGGLoss
from torch.utils.data import DataLoader
from model import initialize_weights, Generator, Discriminator
from tqdm import tqdm
from dataset import MyImageFolder
from torch.utils.tensorboard import SummaryWriter

torch.backends.cudnn.benchmark = True

parser = argparse.ArgumentParser(
                    prog='ProgramName',
                    description='What the program does',
                    epilog='Text at the bottom of help')
parser.add_argument('--predict', action='store_true')
parser.add_argument('--iter', type=int, default=None)
parser.add_argument('--bs', type=int, default=None)
parser.add_argument('--weights', type=str, default=None)
parser.add_argument('--denoise', action="store_true")
parser.add_argument('--scale', type=int, default=4)
parser.add_argument('--load_model', action="store_true")


def train_fn(
    loader,
    disc,
    gen,
    opt_gen,
    opt_disc,
    l1,
    vgg_loss,
    g_scaler,
    d_scaler,
    writer,
    tb_step,
):
    loop = tqdm(loader, leave=True)

    for idx, (src, trg) in enumerate(loop):
        trg = trg.to(config.DEVICE)
        src = src.to(config.DEVICE)

        with torch.cuda.amp.autocast():
            fake = gen(src)
            critic_real = disc(trg)
            critic_fake = disc(fake.detach())
            gp = gradient_penalty(disc, trg, fake, device=config.DEVICE)
            loss_critic = (
                -(torch.mean(critic_real) - torch.mean(critic_fake))
                + config.LAMBDA_GP * gp
            )

        opt_disc.zero_grad()
        d_scaler.scale(loss_critic).backward()
        d_scaler.step(opt_disc)
        d_scaler.update()

        # Train Generator: min log(1 - D(G(z))) <-> max log(D(G(z))
        with torch.cuda.amp.autocast():
            l1_loss = 1e-2 * l1(fake, trg)
            # gen_loss = 1e-2 * l1(fake, trg) # only activate when initially training the generator
            adversarial_loss = 5e-3 * -torch.mean(disc(fake))
            loss_for_vgg = vgg_loss(fake, trg)
            gen_loss = l1_loss + loss_for_vgg + adversarial_loss
            
        opt_gen.zero_grad()
        g_scaler.scale(gen_loss).backward()
        g_scaler.step(opt_gen)
        g_scaler.update()

        writer.add_scalar("Critic loss", loss_critic.item(), global_step=tb_step)
        tb_step += 1

        if idx % 100 == 0 and idx > 0:
            plot_examples("test_images/", gen)

        loop.set_postfix(
            gp=gp.item(),
            critic=loss_critic.item(),
            l1=l1_loss.item(),
            vgg=loss_for_vgg.item(),
            adversarial=adversarial_loss.item(),
            gen_loss = gen_loss.item()
        )

    return tb_step


def main(args):
    dataset = MyImageFolder(root_dir="data/")
    print(f"Training with batch size:::: {args.bs if args.bs else config.BATCH_SIZE}")
    loader = DataLoader(
        dataset,
        batch_size= args.bs if args.bs else config.BATCH_SIZE,
        shuffle=True,
        pin_memory=True,
        num_workers=config.NUM_WORKERS,
    )
    gen = Generator(in_channels=3).to(config.DEVICE)
    disc = Discriminator(in_channels=3).to(config.DEVICE)
    initialize_weights(gen)
    opt_gen = optim.Adam(gen.parameters(), lr=config.LEARNING_RATE, betas=(0.0, 0.9))
    opt_disc = optim.Adam(disc.parameters(), lr=config.LEARNING_RATE, betas=(0.0, 0.9))
    writer = SummaryWriter("logs")
    tb_step = 0
    l1 = nn.L1Loss()
    gen.train()
    disc.train()
    vgg_loss = VGGLoss()

    g_scaler = torch.cuda.amp.GradScaler()
    d_scaler = torch.cuda.amp.GradScaler()
    iteration = args.iter if args.iter else config.ITERATION

    if args.load_model:
        gen = load_model(device=config.DEVICE,scale=args.scale, iter = iteration)
        opt_gen = optim.Adam(gen.parameters(), lr=config.LEARNING_RATE, betas=(0.0, 0.9))
        for param_group in opt_gen.param_groups:
            param_group["lr"] = config.LEARNING_RATE
        gen.train()
        
        load_checkpoint(
            f"{iteration}{config.CHECKPOINT_GEN[-13:]}",
            gen,
            opt_gen,
            config.LEARNING_RATE,
        )
        load_checkpoint(
            f"saved_weights/{iteration}{config.CHECKPOINT_DISC[-19:]}",
            disc,
            opt_disc,
            config.LEARNING_RATE,
        )
        print(f'resuming from iter:::: {iteration}')
    
    
    for epoch in range(1, config.NUM_EPOCHS):
        tb_step = train_fn(
            loader,
            disc,
            gen,
            opt_gen,
            opt_disc,
            l1,
            vgg_loss,
            g_scaler,
            d_scaler,
            writer,
            tb_step,
        )

        
        if config.SAVE_MODEL and epoch % 40 == 0:
            iteration += 1
            print(f"Saving new version of models @ epoch {epoch}")
            save_checkpoint(gen, opt_gen, filename=f"{iteration}{config.CHECKPOINT_GEN[-18:]}")
            save_checkpoint(disc, opt_disc, filename=f"{iteration}{config.CHECKPOINT_DISC[-19:]}")
        


if __name__ == "__main__":

    try_model = False
    args = parser.parse_args()
    assert args.scale == 2 or args.scale == 4, sys.exit(1)
    
    if args.predict:#try_model:
        test_image = os.listdir("test_images")
        print(f"Making predictions for images: \n {test_image}")
        # Will just use pretrained weights and run on images
        # in test_images/ and save the ones to SR in saved/
        iteration = args.iter #config.ITERATION
        gen = load_model(device=config.DEVICE,scale=args.scale, iter = iteration)
        gen.eval()
        opt_gen = optim.Adam(gen.parameters(), lr=config.LEARNING_RATE, betas=(0.0, 0.9))        
        plot_examples("test_images/", gen)
    else:
        torch.cuda.empty_cache()
        # This will train from scratch
        main(args)
