import torch
from model.arch_ts import Generator  # Adjust this according to your actual model imports

def convert_and_save_model(scale, model_name):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Instantiate the generator model
    gen = Generator(
        num_in_ch=3,
        num_out_ch=3,
        num_feat=64,
        num_block=23,
        num_grow_ch=32,
        scale=scale,
    )
    gen.to(device)
    
    # Convert the model to TorchScript
    scripted_model = torch.jit.script(gen)
    
    # Save the TorchScript model
    save_path = f"{model_name}_ts.pt"
    torch.jit.save(scripted_model, save_path)
    print(f"Model {model_name} has been converted to TorchScript and saved as {save_path}.")

if __name__ == "__main__":
    # Example for converting different models
    convert_and_save_model(scale=8, model_name="RealESRGAN_x8.pth")
    convert_and_save_model(scale=4, model_name="RealESRGAN_x4.pth")
    convert_and_save_model(scale=2, model_name="RealESRGAN_x2.pth")
