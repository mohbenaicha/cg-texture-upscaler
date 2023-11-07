import torch
from model.arch import Generator

class RESRGAN:
    def __init__(self, device, scale=4):
        self.device = device
        self.scale = scale
        self.gen = Generator(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=scale,
        )

    def load_weights(self, model_path):

        loadnet = torch.load(model_path)
        if "params" in loadnet:
            self.gen.load_state_dict(loadnet["params"], strict=True)
        elif "params_ema" in loadnet:
            self.gen.load_state_dict(loadnet["params_ema"], strict=True)
        else:
            self.gen.load_state_dict(loadnet, strict=True)
        self.gen.eval()
        self.gen.to(self.device)
