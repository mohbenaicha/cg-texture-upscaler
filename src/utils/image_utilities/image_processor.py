from utils.image_utilities.interfaces import IImageProcessor

class ImageProcessor(IImageProcessor):
    def __init__(self, container):
        self.container = container # orchestrator/container that has image and config
    
    def preprocess_image(self):
        raise NotImplementedError
    def postprocess_image(self):
        raise NotImplementedError
    def process_image(self):
        # calls upscale or downscale based on parent config
        raise NotImplementedError
    def upscale(self, method):
        # calls resrgan_upscale or linear_upscale based on parent config
        raise NotImplementedError
    def downscale(self, method):
        # downscales image
        raise NotImplementedError
    def resrgan_upscale():
        raise NotImplementedError
    def linear_upscale():
        raise NotImplementedError