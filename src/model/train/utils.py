import torch
import os
import config
import numpy as np
from PIL import Image
import cv2
import torch
from torchvision import transforms
from torchvision.utils import save_image
import matplotlib.pyplot as plt

def gradient_penalty(critic, real, fake, device):
    BATCH_SIZE, C, H, W = real.shape
    alpha = torch.rand((BATCH_SIZE, 1, 1, 1)).repeat(1, C, H, W).to(device)
    interpolated_images = real * alpha + fake.detach() * (1 - alpha)
    interpolated_images.requires_grad_(True)

    # Calculate critic scores
    mixed_scores = critic(interpolated_images)

    # Take the gradient of the scores with respect to the images
    gradient = torch.autograd.grad(
        inputs=interpolated_images,
        outputs=mixed_scores,
        grad_outputs=torch.ones_like(mixed_scores),
        create_graph=True,
        retain_graph=True,
    )[0]
    gradient = gradient.view(gradient.shape[0], -1)
    gradient_norm = gradient.norm(2, dim=1)
    gradient_penalty = torch.mean((gradient_norm - 1) ** 2)
    return gradient_penalty


def save_checkpoint(model, optimizer, filename="my_checkpoint.pth.tar"):
    print("=> Saving checkpoint")
    checkpoint = {
        "state_dict": model.state_dict(),
        "optimizer": optimizer.state_dict(),
    }
    torch.save(checkpoint, filename)


def load_checkpoint(checkpoint_file, model, optimizer, lr):
    print(f"=> Loading checkpoint: {checkpoint_file}")
    checkpoint = torch.load(checkpoint_file, map_location=config.DEVICE)
    # model.load_state_dict(checkpoint)
    model.load_state_dict(checkpoint["state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer"])

    # If we don't do this then it will just have learning rate of old checkpoint
    # and it will lead to many hours of debugging \:
    for param_group in optimizer.param_groups:
        param_group["lr"] = lr


def plot_examples(low_res_folder, gen):
    files = os.listdir(low_res_folder)

    gen.eval()
    for file in files:
        image = Image.open(os.path.join(low_res_folder, file))
        with torch.no_grad():
            upscaled_img = gen(
                config.test_transform(image=np.asarray(image))["image"]
                .unsqueeze(0)
                .to(config.DEVICE)
            )
        save_image(upscaled_img, f"saved/{file}")
    gen.train()


def load_model(device, scale, iter):
    from model import RESRGAN
    model = RESRGAN(device=device, scale=scale)
    model.load_weights(f"saved_weights/{iter}{config.CHECKPOINT_GEN[-18:]}")
    return model.gen.to(config.DEVICE)


def make_patches(data_dir):
    transt = transforms.ToTensor()
    transp = transforms.ToPILImage()

    for img in os.listdir(data_dir):
        if ".png" in img: # the train images were all batch converted to PNG using Image Magick before hand
            img_t = transt(Image.open(img))
            if img_t.data.size()[0] > 1 and img_t.data.size()[1] >= 2048 and img_t.data.size()[2] >= 2048:
                #print(img_t.size())
                #torch.Tensor.unfold(dimension, size, step)
                #slices the images into 8*8 size patches
                patches = img_t.data.unfold(1,1024,1024).unfold(2,1024,1024)
                for i in range(2):
                    for j in range(2):
                        save_image(patches[:,i,j,:,:], img[:-4]+f"_____{i}{j}.png")



def delete_small_images(data_dir):
    for file in os.listdir(data_dir):
        path = os.path.join(data_dir, file)
        image = cv2.imread(path)
        if image.shape[1] < 65 or image.shape[2] < 65:
            os.remove(path)