# CG Texture Upscaler

This repo contains the source code for the official CG Texture Upscaler, a tool and utility for upscaling computer graphics textures using the RealESRGAN that uses transfer learning and that was also further trained on thousands of computer graphics textures. More details on how it works and how it was made can be found https://www.mohamedbenaicha.com/upscaler

**To use in a Python environment:**

1. ```git pull https://github.com/mohbenaicha/cg-texture-upscaler.git```
2. Setup a new Python environment using ```pip install -r requirements.txt```
3. Based on the version of the application you wish you try, add ONE of the following:
    * CPU-based upscaling: ```pip install torch torchvision torchaudio```
    * GPU-based upscaling: ```pip3 install pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117 (not tested on Cuda 11.8)```
4. Download the model weights from: https://drive.google.com/file/d/1ZOM7wYJGj1BiHemL9jAgzKX-AiaDQXH7/view?usp=sharing
5. Extract the ```saved_models.rar``` folders into ```/cg-texture-upscaler``` folder
6. Run ```python gui_main.py``` using the interpreter in the newly-setup environment  

**To use the release version:**

1. Download the initial release here: https://www.mohamedbenaicha.com/upscaler
2. Simply run through the ```CGTextureUpscaler.exe``` (your AV may prompt you to give it r/w/x permissions)

*Additional notes:*

1. ```cli_main.py``` code was added primarily as a placeholder
2. The shortcut reference is available in this github repo
3. Once tests are fully developed, the will be pushed and an official release will follow
