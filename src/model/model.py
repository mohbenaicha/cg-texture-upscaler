import torch
from model.arch import Generator
from model.arch_ts import Generator as Generator_TS
from model.utils import prune_model_for_inference


class RESRGAN:
    """
    Real ESRGAN pipeline orchestrator
    """

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

        self.gen.to(self.device)
        self.quantize = False
        self.prune = True

    def load_weights(self, model_path):

        loadnet = torch.load(model_path)
        if "params" in loadnet:
            self.gen.load_state_dict(loadnet["params"], strict=True)
        elif "params_ema" in loadnet:
            self.gen.load_state_dict(loadnet["params_ema"], strict=True)
        else:
            self.gen.load_state_dict(loadnet, strict=True)

        self.gen.eval()

        if self.prune:
            self.gen = prune_model_for_inference(self.gen, pruning_amount=0.2)

        if self.quantize:
            self.gen = torch.quantization.quantize_dynamic(
                self.gen,
                {torch.nn.Conv2d},  # only conv2d in Real-ESRGAN
                dtype=torch.qint8,
            )


class RESRGAN_TS:
    def __init__(self, device):
        self.device = device

        # Load the TorchScript model from model_path

    def load_weights(self, model_path):
        self.gen = torch.jit.load(model_path).to(self.device)
        self.gen.eval()
