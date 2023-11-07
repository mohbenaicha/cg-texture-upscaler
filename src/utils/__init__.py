from io import TextIOWrapper
import sys
import os
import shutil
from typing import List, Dict, Optional, Union, Any
from typing_extensions import Self
from datetime import date, datetime
import time
from copy import deepcopy
import math
import customtkinter as ctk
from PIL import Image, UnidentifiedImageError, ImageFilter, ImageEnhance
from wand.image import Image as wand_image
import cv2
import numpy as np
import torch
from gui.message_box import CTkMessagebox
from utils.events import enable_UI_elements
from model.arch import Generator
from caches.cache import image_paths_cache as im_cache
from app_config.config import ConfigReference as confref, ExportConfig, EXR_DEPTH, EXR_COMPRESSION_TYPES
# from utils.export_utils import log_file
import torchvision.transforms.functional as F
from PIL.DdsImagePlugin import DdsImageFile
from PIL.TgaImagePlugin import TgaImageFile
from PIL.JpegImagePlugin import JpegImageFile
from PIL.BmpImagePlugin import BmpImageFile

# to be able to read wand-exported image files
from PIL import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True
imTypes = Union[DdsImageFile, TgaImageFile, JpegImageFile, BmpImageFile, np.array]
