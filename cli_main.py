from typing import Dict
import torch
from model import RESRGAN, RESRGAN, export_images
import argparse

# TODO: integrate in following patch
torch.set_num_threads(8)
parser = argparse.ArgumentParser()
parser.add_argument("--scale", "-s", type=int, default=2)
parser.add_argument("--weights", "-w", action="store_true")
parser.add_argument("--device", "-d", type=str, default="cuda")


def main(args: Dict[str, int|str|float]) -> int:
    '''
    args:
        args (dict): a dictionary of parsed command line arguments with strings as keys and Union(str, int, float, bool) as values
    '''
    device = torch.device(args.device)
    model = RESRGAN(device, scale=args.scale)

    if args.weights:
        model.load_weights(f"saved_models/{args.scale}x.pth", download=False)

    export_images("inputs/", model.gen.eval(), device=args.device)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
