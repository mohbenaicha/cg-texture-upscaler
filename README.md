# CG Texture Upscaler

This repo contains the source code for the official CG Texture Upscaler, a tool and utility for upscaling computer graphics textures using the RealESRGAN that uses transfer learning and that was also further trained on thousands of computer graphics textures. More details on how it works, results and how it was made can be found https://www.mohamedbenaicha.com/upscaler

**To use in a Python environment:**

1. ```git pull https://github.com/mohbenaicha/cg-texture-upscaler.git```
2. Setup a new Python environment using ```pip install -r requirements.txt``` for GPU-based upscaling:
   * for CPU upscaling, comment out the GPU-based torch libraries and uncommment the CPU-based ones
3. Download the model weights from: 
   * standard weights https://drive.google.com/file/d/1ZOM7wYJGj1BiHemL9jAgzKX-AiaDQXH7/view?usp=sharing
   * weights for jit compiled network: https://drive.google.com/file/d/1F3LETd42BIMiLw2GcGEITyqmw25fW91h/view?usp=sharing (need to uncomment lines in the load_model() in export_utils.py)
4. Extract the ```saved_models.rar``` folders into ```/cg-texture-upscaler``` folder. They should end up in a saved_models folder (extract the jit-compiled weights in there like wise if using those)
5. Run ```python main.py``` using the interpreter in the newly-setup environment  

**To use the release version:**

1. Download the initial release here: https://www.mohamedbenaicha.com/upscaler
2. Simply run through the ```CGTextureUpscaler.exe``` (your AV may prompt you to give it r/w/x permissions upon launch or upon export)

**To use the release version cli:**

1. Download the initial release here: https://www.mohamedbenaicha.com/upscaler
2. Simply run through the ```CGTextureUpscaler.exe``` with the supported command line arguments stated in the guide ```Using the CLI.txt```.

*Additional notes:*

1. The shortcut reference is available in this github repo
2. Once tests are fully developed, the stable version will be pushed and an official release will follow.
