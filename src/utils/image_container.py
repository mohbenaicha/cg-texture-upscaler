from app_config.config import *
from utils import *
from utils.logging import write_log_to_file, log_file


class ImageContainer:
    """
    This class reads images from and writing them to disk. It gets and sets
    the image objects (a PIL Image/wand Image/ cv2 array) but accessing the
    Images members through composition and is instatiated only once upon every
    batch export operation.
    """

    def __init__(
        self, img_index: int, src_path: str, trg_path: str, img_name: str, **kwargs
    ):
        self.img_index: int = img_index
        self.src_path: str = src_path
        self.trg_path: str = trg_path
        self.single_export_location: str = kwargs.get("single_export_location", None)

        self.src_image_name: Optional[str] = img_name
        self.src_format: Optional[str] = self.src_image_name[-3:]
        self.color_space: Optional[str] = kwargs.get("color_space", None)
        self.write_color_depth: Optional[str] = kwargs.get("export_color_depth", None)
        self.export_mode: Optional[str] = kwargs.get(
            "export_color_mode", None
        )  # RGB/RGBA/L/LA
        self.export_format: Optional[str] = kwargs.get("export_format", None)
        self.trg_image_dtype: Optional[str] = {
            "8": "uint8" if not self.export_format == "exr" else None,
            "16": "uint16" if not self.export_format == "exr" else "float16",
            "32": "float32",
        }[self.write_color_depth]
        self.color_mode: Optional[str] = kwargs.get(
            "color_mode", "true_color"
        )  # true_color, indexed
        self.device: Optional[str] = kwargs.get("device", "cuda")
        self.upscale_factor: int = confref.scale_map[kwargs.get("scale", None)]
        self.upscale_precision: str = confref.upscale_precision_levels[self.device][
            kwargs.get("upscale_precision", None)
        ]
        self.compression: Optional[str] = kwargs.get("compression", None)
        self.mipmaps: Optional[str] = kwargs.get("mipmaps", None)
        self.noise_factor: Optional[float] = kwargs.get("noise_level", None)
        self.numbering: Optional[str] = kwargs.get("numbering", None)
        self.prefix: Optional[str] = kwargs.get("prefix", None)
        self.suffix: Optional[str] = kwargs.get("suffix", None)
        self.flag_export_to_original: bool = kwargs.get("export_to_original", False)
        self.opencv_read_args: List[int] = [cv2.IMREAD_UNCHANGED]

        self.write_compression: Optional[str] = kwargs.get(
            "write_compression", None
        )  # automatic
        if self.export_format in ConfigReference.opencv_formats:
            self.handle_opencv_flags()
        self.export_naming: dict["str", "str"] = {
            "export_format": self.export_format,
            "numbering": kwargs.get("numbering", ""),
            "prefix": kwargs.get("prefix", ""),
            "suffix": kwargs.get("suffix", ""),
        }
        self.alpha_0: bool = False
        self.setup_dtype_mapping()

        self.alpha: Optional[Union[torch.Tensor, np.ndarray]] = None
        self.color_channels: Optional[Union[torch.Tensor, np.ndarray]] = None
        self.read_and_preprocess_image()

    def read_and_preprocess_image(self) -> None:
        src_path = os.path.join(self.src_path, self.src_image_name)
        if self.src_format in confref.opencv_formats:
            self.image = cv2.imread(src_path, cv2.IMREAD_UNCHANGED)
        else:
            self.image = Image.open(src_path)
            self.image = np.array(self.image)
        # extract datatype for future use
        self.src_dtype: str = str(self.image.dtype)
        self.mode: Optional[str] = self.get_mode_from_array()
        self.length = len(self.mode)
        # handle dimensions
        self.handle_dimensions(
            log_file
            # self.log_file
        )

    def preprocess_noisy_image(self) -> None:
        if self.noise_factor > 0.0:
            # get color channels from the noisy copy since linear-sRGB transformations are not
            # applied to alpha channels
            self.noisy_copy = np.copy(self.image)

            if self.mode == "RGBA":  # RGB + Alpha
                temp = np.copy(self.noisy_copy)[..., :3]
            elif self.mode == "LA":  # Greyscale + alpha
                temp = np.copy(self.noisy_copy)[..., :1]
            else:  # RGB or Greyscale
                temp = np.copy(self.noisy_copy)[..., :]

            # concatenate tranformed color channels with alpha channel TODO: is there a better way to avoid repeating the if/else statements
            if self.mode == "RGBA":
                self.noisy_copy = np.concatenate(
                    (temp, self.noisy_copy[..., 3:]), axis=2
                )
            elif self.mode == "LA":
                self.noisy_copy = np.concatenate(
                    (temp, self.noisy_copy[..., 1:]), axis=2
                )
            else:
                self.noisy_copy = temp
            del temp

            self.noisy_copy = self.output_dtype_mapping[
                f"{str(self.noisy_copy.dtype)}:{self.trg_image_dtype if self.export_format != 'exr' else 'float32'}"
            ](channels=self.noisy_copy)

            if "Linear In" in self.color_space:
                self.noisy_copy = self.output_dtype_mapping[
                    f"{self.noisy_copy.dtype}:float32"
                ](channels=self.noisy_copy)
                self.noisy_copy = np.vectorize(self.sRGB_to_linear)(
                    self.noisy_copy
                ).astype(self.noisy_copy.dtype)

            if self.mode == "L":
                self.noisy_copy = np.expand_dims(self.noisy_copy, 2)

    def check_all_values_equivalent(self):
        if self.image.max() == self.image.min():
            write_log_to_file(
                "WARNING",
                f"Using linear scaling to scale image {self.src_image_name}'s channels.",
                log_file,
            )
            self.determine_if_alpha_is_0()
            self.image = self.upscale_linear(
                self.image,
                self.upscale_factor,
                self.image.max(),
                self.upscale_precision,
            )
            self.linear_upscale_all_channels = True
            self.proceed_with_split = False
        else:
            self.linear_upscale_all_channels = False
            if (
                "A" in self.mode
            ):  # split channels to process by either the generator or through linear upscaling
                self.proceed_with_split = True
            else:  # if only rgb or grayscale channels exist, no split is required
                self.proceed_with_split = True

            # at this point, if noise is added, the noisy image is added before the channels to
            # be upscaled are processed further
        if self.noise_factor > 0.0:
            self.noisy_copy = deepcopy(self.image)
            self.preprocess_noisy_image()
        return self

    def split_image(self) -> Self:
        """
        Separates alpha from color channels creating two new members to represent the original image object.
        Also saves the images depth (data type) and removes the original image object from memory.
        """
        self.upscale_color_with_generator, self.upscale_alpha_with_generator = (
            True
            if (self.upscale_factor in [2, 4, 0.5] and self.proceed_with_split)
            else False,
            False,  # will handle separately
        )
        if self.proceed_with_split:
            # extract alpha information
            self.alpha = (
                self.image[:, :, self.length - 1 :]
                if ("A" in self.mode and "A" in self.export_mode)
                else None
            )
            self.upscale_alpha_with_generator = (
                True
                if (
                    type(self.alpha) == np.ndarray
                    and "A" in self.export_mode
                    and self.upscale_factor in [2, 4, 0.5]
                )
                else False
            )
            if self.upscale_alpha_with_generator:
                # ensure image channels and elements vary (masks in CG textures can exhibit such qualities)
                alpha_max, alpha_min = self.alpha.max(), self.alpha.min()
                # if the entire alpha channel is a single value, conduct a linear upscale
                if alpha_max == alpha_min:
                    write_log_to_file(
                        "WARNING",
                        f"Using linear scaling to scale image {self.src_image_name}'s alpha channel.",
                        log_file,
                    )
                    self.alpha = self.upscale_linear(
                        self.alpha,
                        self.upscale_factor,
                        alpha_max,
                        self.upscale_precision,
                    )
                    self.upscale_alpha_with_generator = False

                else:  # prepare alpha channel to be fed to the Generator
                    self.alpha = (
                        np.repeat(self.alpha, repeats=3, axis=2)
                        if not self.upscale_factor in [0.5, 1]
                        else self.alpha
                    )
            # exctract color information (rgb/grayscale)
            if self.mode == "RGBA":
                self.color_channels = self.image[:, :, : self.length - 1]  # rgb
            elif self.mode == "RGB":
                self.color_channels = self.image[:, :, :]  # rgb
            elif self.mode in ["LA"]:
                self.color_channels = self.image[:, :, 0:1]  # gray with 3 dimensions
            else:
                self.color_channels = np.expand_dims(
                    self.image[:, :], 2
                )  # grayscale with 2 dimensions expanded to 3

            # ensure channels image channels and elements vary (masks in CG textures can exhibit such qualities)
            color_max, color_min = self.color_channels.max(), self.color_channels.min()
            if color_max == color_min:
                write_log_to_file(
                    "WARNING",
                    f"Using linear scaling to scale image {self.src_image_name}'s color channel(s).",
                    log_file,
                )
                self.color_channels = self.upscale_linear(
                    self.color_channels,
                    self.upscale_factor,
                    color_max,
                    self.upscale_precision,
                )
                self.upscale_color_with_generator = False
            else:
                # the the color channels are to be fed to the generator, ensure the grayscale image
                # is expanded into 3 channels
                if self.mode == "L":  # i.e. either grayscale or grayscale+alpha
                    self.color_channels = np.repeat(
                        np.expand_dims(self.image, 2), repeats=3, axis=2
                    )
                elif self.mode == "LA":  # i.e. either grayscale or grayscale+alpha
                    self.color_channels = np.repeat(self.image, repeats=3, axis=2)
        else:
            if not "L" in self.mode:
                self.alpha = None
            self.color_channels = self.image
            # remove image from memory once channels are separated
        self.image = None
        return self

    def convert_datatype(self, input: bool = True) -> Self:
        """
        Converts uint8/uint16/float32 to float16/float32 types to be process by the generator.
        Also converts color space of input to sRGB the generator is trained on sRGB colors and
        does not linear images well. The it further the color space to linear post-upscale if
        so desired by the user.
        """
        if input:
            if (
                self.upscale_color_with_generator
            ):  # if color channels weren't upscaled using the linear algorithm
                self.color_channels = self.convert_input_image_dtype(
                    self.color_channels
                )
            if (
                self.upscale_alpha_with_generator
            ):  # if the alpha channel wasn't upscaled using the linear algorithm
                self.alpha = self.convert_input_image_dtype(self.alpha)
        else:
            self.image = self.convert_output_image_dtype(channels=self.image)
        return self

    def upscale_linear(
        self,
        channels: str,
        factor: int,
        fill_value: Union[np.uint8, np.uint32, np.float32],
        upscale_precision: float,
    ) -> np.ndarray:
        """
        If all values across image channels are the same, fill a new array with that value.
        """
        w, h, c = (
            (channels.shape) if len(channels.shape) == 3 else (*channels.shape, None)
        )

        return (
            np.ones(
                shape=(int(w * factor), int(h * factor))
                if not c
                else (int(w * factor), int(h * factor), c),
                dtype=channels.dtype,
            )
            * fill_value
        ).astype(upscale_precision[0])

    def recombine_channels(self) -> Self:
        """
        Recombines color and alpha channels using a lambda or np.concatente function.
        If an alpha channel exists and is 3 channels (generator output), channels are
        combined into a single channel based on a fixed weighting
        """
        t_alpha, t_color = type(self.alpha), type(self.color_channels)
        if not self.upscale_factor == 0.5:
            if not t_alpha == type(None):
                if len(self.alpha.shape) == 2:
                    self.alpha = (
                        np.expand_dims(self.alpha, axis=2)
                        if t_alpha == np.ndarray
                        else self.alpha.unsqueeze(dim=2)
                    )
            if len(self.color_channels.shape) == 2:
                self.color_channels = (
                    np.expand_dims(self.color_channels, axis=2)
                    if t_color == np.ndarray
                    else self.color_channels.unsqueeze(dim=2)
                )

            if self.upscale_alpha_with_generator:
                if not type(self.alpha) == type(None):
                    alpha_dims = len(self.alpha.shape)

                if alpha_dims == 2:
                    self.alpha = self.alpha.unsqueeze(0)
                if confref.split_alpha and t_alpha == torch.Tensor:
                    self.alpha = self.alpha.permute(2, 0, 1)

                self.alpha = (
                    self.alpha[0] * (0.2989)
                    + self.alpha[1] * (0.5870)
                    + self.alpha[2] * (0.1140)
                ).unsqueeze(0)
                if confref.split_alpha and t_alpha == torch.Tensor:
                    self.alpha.permute(2, 0, 1)
            else:
                if t_alpha == np.ndarray:
                    temp, self.alpha = np.transpose(self.alpha, axes=(2, 0, 1)), None
                    self.alpha, temp = temp, None

            if self.upscale_color_with_generator:
                if confref.split_color and t_color == torch.Tensor:
                    self.color_channels = self.color_channels.permute(2, 0, 1)
            else:
                if t_color == np.ndarray:
                    temp, self.color_channels = (
                        np.transpose(self.color_channels, axes=(2, 0, 1)),
                        None,
                    )
                    self.color_channels, temp = temp, None
            if t_alpha == torch.Tensor:
                self.alpha = (
                    self.alpha.detach().cpu()
                    if self.device == "cuda"
                    else self.alpha.to(dtype=torch.float32)
                )
                self.alpha = self.alpha.numpy()
            if t_color == torch.Tensor:
                self.color_channels = (
                    self.color_channels.detach().cpu()
                    if self.device == "cuda"
                    else self.color_channels.to(dtype=torch.float32)
                )
                self.color_channels = self.color_channels.numpy()

        if not t_alpha == type(None):
            self.image = np.concatenate(
                (self.color_channels, self.alpha),
                axis=(0 if self.upscale_factor != 0.5 else 2),
            )
        else:
            self.image = self.color_channels

        temp, self.image = (
            self.image.transpose(1, 2, 0) if self.upscale_factor != 0.5 else self.image,
            None,
        )
        self.image, temp = temp, None
        self.color_channels, self.alpha = None, None
        return self

    def linear_to_sRGB(
        self, p: Union[np.float32, np.float16]
    ) -> Union[np.float16, np.float32, np.float64]:
        """
        Converts a np.array's elements from sRGB color space to linear sRGB color space
        Transformaion equation based on: https://www.nayuki.io/page/srgb-transform-library
        """
        inv_gamma = 1 / 2.4
        if p <= 0.0031308:
            p *= 12.92
        else:
            p = (1.055 * (p**inv_gamma)) - 0.055
        return p

    def sRGB_to_linear(
        self, p: Union[np.float32, np.float16]
    ) -> Union[np.float16, np.float32, np.float64]:
        """
        Converts a np.array's elements from linear sRGB color space to sRGB color space.
        Transformaion equation based on: https://www.nayuki.io/page/srgb-transform-library
        """
        gamma = 2.4
        if p <= 0.04045:
            p /= 12.92
        else:
            p = ((p + 0.055) / 1.055) ** gamma
        return p

    def handle_gamma_correction(self, gamma: float) -> Self:
        """
        perceived value = ( ( pixel value / max value ) ** ( 1 / gamma ) ) * max value
        """
        if self.upscale_color_with_generator:
            cc_dtype = self.color_channels.dtype
            if not gamma == 1.0:
                if cc_dtype == "uint8":
                    type_ = "uint8"
                    max_value = 255
                elif cc_dtype == "uint16":
                    type_ = "uint16"
                    max_value = 65535
                elif cc_dtype == "float16":
                    type_ = "float16"
                    max_value = 1.0
                elif cc_dtype == "float32":
                    type_ = "float32"
                    max_value = 1.0
                else:
                    type_ = "float64"
                    max_value = 1.0

                self.color_channels = (
                    (self.color_channels / max_value) ** (1 / gamma)
                ) * max_value

                # before color channels are fed to the Generator
                if type(self.color_channels) == np.ndarray:
                    self.color_channels.astype(confref.supported_dtypes["array"][type_])
                else:
                    # self.color_channels are corrected by the inverse of the gamma
                    # after color channels upscaled, they are tensors
                    self.color_channels.to(confref.supported_dtypes["tensor"][type_])

        return self

    def normalize_uint(self, image: np.ndarray, minmax_norm: bool = False) -> None:
        """
        Normalize value in a np.array between 0 and 1 or -1 and 1
        """
        dtype = image.dtype
        if not minmax_norm:
            return image / (255 if dtype == "uint8" else 65535)
        else:
            min, max = image.min(), image.max()
            b = 0
            return (1 - b) * (image - min) / (max - min) - b

    def convert_input_image_dtype(self, channels: np.ndarray) -> torch.Tensor:
        """
        Convert the input image to a level of float precision that is compatible with torch
        types.
        """
        if channels.dtype == np.uint8:
            channels = self.normalize_uint(channels)
        elif channels.dtype == np.uint16:
            channels = self.normalize_uint(channels)

        # to reduce method bloat, the color space sRGB-Linear conversion is subsumed under data type conversion
        # as a technical note, no color space conversion is actually happening since sRGB is a standard RGB color
        # space
        if "Linear In" in self.color_space:
            channels = np.vectorize(self.linear_to_sRGB)(channels)
        return channels.astype(self.upscale_precision[0])

    def convert_output_image_dtype(
        self, channels: np.ndarray, input_dtype: str = None, out_dtype: str = None
    ) -> np.ndarray:
        """
        Convert (scale) the upscaled image to the proper export datatype as
        indicated in the app_config.ConfigReference class.
        """
        # unlike for the PNG format, the IMWRITE function requires float arrays and exports half or float precision based on the cv2.IMWRITE flag speficier when saving the image
        trg_dtype = (
            self.trg_image_dtype if not self.export_format == "exr" else "float32"
        )

        # see the method above for details
        if "Linear Out" in self.color_space:
            channels = np.vectorize(self.sRGB_to_linear)(channels)
            input_dtype = channels.dtype

        # the self.output_dtype_mapping dictionary contains lambdas that are called on the channels passed in
        return self.output_dtype_mapping[
            f"{str(channels.dtype if not input_dtype else input_dtype)}:{str(trg_dtype if not out_dtype else out_dtype)}"
        ](channels)

    def convert_RGB_to_grayscale(self, channels: np.ndarray) -> np.ndarray:
        return np.expand_dims(cv2.cvtColor(channels, cv2.COLOR_BGR2GRAY), 2)

    def apply_dds_mipmap_fix(self) -> Self:
        if self.mipmaps != "none":
            if len(self.image) == 3:
                self.alpha = np.ones_like(self.image[0], dtype="uint8")
                write_log_to_file(
                    log_type="Warning",
                    message="Added an alpha channel with a transparency value of 1/255"
                    "So that mipmaps are written correctly.",
                    log_file=log_file,
                )
                self.image = np.concatenate(arrays=(self.image, self.alpha), axis=0)
            elif len(self.image == 4):
                self.image = np.copy(self.image)
                self.image[3][np.where(self.image[3] == 0)] += 1
        return self

    def write_image(self, master: ctk.CTkFrame, verbose: bool) -> None:
        from utils.export_utils import handle_naming

        im_name = handle_naming(self.export_naming, self.src_image_name, self.img_index)

        if self.flag_export_to_original:
            save_path = os.path.join(self.trg_path, im_name)
        else:
            save_path = os.path.join(self.single_export_location, im_name)

        if self.export_format in confref.opencv_formats:
            self.write_opencv_image(save_path)
        else:
            self.write_wand_image(save_path, im_name, log_file)
        write_log_to_file("INFO", f"Saved {im_name} to {save_path}", log_file)
        if not master and verbose:
            (f"\n[INFO] Saved {im_name} to {save_path}\n")

    def write_wand_image(
        self, save_path, im_name: str, log_file: TextIOWrapper
    ) -> None:
        self.determine_if_alpha_is_0()
        with wand_image.from_array(self.image) as img:
            img.format = self.export_format

            # .dds automatic vs general manual compression setting
            if self.compression == "automatic":
                if self.alpha_0:
                    img.compression = "dxt1"
                else:
                    img.compression = "dxt5"
            else:
                img.compression = (
                    self.compression if not self.compression == "none" else "no"
                )
            # bmp specific information TODO: add warning about color mode being changed
            if self.export_format == "bmp" and self.compression == "rle":
                img.type = "palette"
                write_log_to_file(
                    "WARNING",
                    f"{im_name} saved under {save_path} is converted to paletted color mode"
                    "to export using rle compression. True color has been indexed to 256 colors."
                    "To avoid this behaviour in the future, set bmp compression to none.",
                    log_file,
                )
            # the other color types pertain to grayscale/true color
            elif self.export_format != "dds":
                if self.export_mode == "L":
                    img.type = "grayscale"
                # elif self.export_mode == 'LA':
                #     img.type = "grayscalealpha"
                elif self.export_mode == "RGB":
                    img.type = "truecolor"
                elif self.export_mode == "RGBA":
                    img.type = "truecoloralpha"

            if self.mipmaps:
                self.handle_mipmaps(self.mipmaps, img)

            img.save(filename=save_path)

    def write_opencv_image(self, save_path: str) -> None:
        cv2.imwrite(filename=save_path, img=self.image, params=self.opencv_write_flgs)

    def get_mode_from_array(self) -> None:
        """
        Determines image channel mode from the length of a np.array object using a naive yet practical approach.
        """
        shape = self.image.shape
        if len(shape) == 2:
            return "L"
        else:
            if shape[2] == 4:
                return "RGBA"
            elif shape[2] == 3:
                return "RGB"
            elif shape[2] == 2:
                return "LA"
            else:
                return None

    def add_alpha(self, channels: np.ndarray, opacity: float):
        alpha = np.ones(channels.shape[:2], dtype=channels.dtype)
        channels = np.concatenate(
            (
                channels,
                np.expand_dims(alpha, 2)
                * opacity
                * (
                    (255 if self.trg_image_dtype == "uint8" else 65535)
                    if not "float" in self.trg_image_dtype
                    else 1
                ),
            ),
            axis=2,
        ).astype(channels.dtype)
        return channels

    def handle_write_channel_mode(self, channels: np.ndarray) -> np.ndarray:
        no_channels = channels.shape[2]
        if no_channels == 1:  # grey
            if not "L" in self.export_mode:  # write as RGB
                channels = np.repeat(channels, 3, 2)
                if "A" in self.export_mode:  # write as RGBA
                    channels = self.add_alpha(channels=channels, opacity=1.0)
        elif no_channels == 2:  # grey + alpha
            if "L" in self.export_mode:  # write in greyscale
                channels = (
                    channels[..., :1]
                    if not "A" in self.export_mode
                    else channels[..., :]
                )
            else:  # write in RGB
                temp = np.repeat(channels[:, :, 0], 3)
                channels = (
                    temp
                    if not "A" in self.export_mode
                    else np.concat((temp, channels[1]), 2)
                )
        elif no_channels == 3:  # RGB
            if "L" in self.export_mode:  # write in greyscale
                channels = self.convert_RGB_to_grayscale(channels)
            if "A" in self.export_mode:  # write as RGBA
                channels = self.add_alpha(channels=channels, opacity=1.0)
        elif no_channels == 4:  # RGBA
            if "L" in self.export_mode:  # write in greyscale
                channels = (
                    self.convert_RGB_to_grayscale(channels[..., :3])
                    if not "A" in self.export_mode
                    else (
                        np.concatenate(
                            (
                                self.convert_RGB_to_grayscale(channels[..., :3]),
                                channels[..., 3:],
                            ),
                            axis=2,
                        )
                    )
                )
            else:  # write in RGB
                channels = (
                    channels[..., :3] if not "A" in self.export_mode else channels
                )
        return channels

    def handle_channel_order(self) -> Self:
        if (
            len(self.image.shape) == 2
        ):  # applies images to be written in  greyscale without an alpha (come in the shape of (W,H))
            self.image = np.expand_dims(self.image, 2)
        statement = "self.image[..., :{0}] = self.image[..., 2::-1]".format(
            "3" if self.image.shape[2] == 4 else ""
        )

        if self.length > 2:
            if self.src_format in confref.opencv_formats:
                if not confref.write_lib_map[self.export_format] == "opencv":
                    exec(statement)
            else:
                if confref.write_lib_map[self.export_format] == "opencv":
                    exec(statement)
        return self

    def handle_dimensions(self, log_file: TextIOWrapper) -> Self:
        """
        Reshapes an image by adding a single row and/or column of pixel to make
        a multiple of 2.
        """
        shape = list(self.image.shape)
        w_mod, h_mod = shape[0] % 2, shape[1] % 2
        if w_mod != 0 or h_mod != 0:
            write_log_to_file(
                "WARNING",
                f"Image {self.src_image_name} has dimensions {shape[0]}x{shape[1]}. Upscaling this image"
                "Will affect UV mapping.",
                log_file,
            )
            # check if the width and/or height is a multiple of 2
            shape[0] += 1 if w_mod != 0 else 0
            shape[1] += 1 if h_mod != 0 else 0
            write_log_to_file(
                "INFO",
                f"Reshaped image {self.src_image_name} to dimensions {shape[0]}x{shape[1]} to allow for processing.",
                log_file,
            )
            self.image = cv2.resize(
                src=self.image, dsize=shape[:2], interpolation=cv2.INTER_LANCZOS4
            )
        return self

    def handle_noise(self) -> Self:
        from utils.export_utils import unsharp_mask
        no_channels = self.image.shape[2]
        self.noisy_copy = unsharp_mask(
            image=cv2.resize(
                src=self.noisy_copy,
                dsize=tuple(
                    int(dim * self.upscale_factor)
                    for dim in self.noisy_copy.shape[:-1][::-1]
                ),
                interpolation=cv2.INTER_LANCZOS4,
            ),
            threshold=0.0,
            amount=15,
            input_dtype=str(self.noisy_copy.dtype),
        )
        if len(self.noisy_copy.shape) == 2:
            self.noisy_copy = np.expand_dims(self.noisy_copy, axis=2)
        self.noisy_copy = self.convert_output_image_dtype(
            self.noisy_copy, self.noisy_copy.dtype, self.image.dtype
        )
        # A more sophisticated algorithm can be used to retain only the lightest/darkest patterns in the original texture and add them back as noise to the AI-upscaled texture
        mask = self.noisy_copy < self.image*(self.noise_factor)
        np.copyto(self.image, self.noisy_copy, where=mask)
        self.noisy_copy = None
        return self

    def handle_opencv_flags(self) -> None:
        if self.export_format == "png":
            self.opencv_write_flgs = [
                cv2.IMWRITE_PNG_COMPRESSION,
                int(ExportConfig.compression),  # compression level (0 to 9)
            ]
        elif self.export_format == "jpg":
            self.opencv_write_flgs = [
                cv2.IMWRITE_JPEG_QUALITY,
                int(ExportConfig.compression),  # image quality (0-100)
            ]
        else:
            self.opencv_write_flgs = [
                cv2.IMWRITE_EXR_COMPRESSION,
                EXR_COMPRESSION_TYPES.__members__[
                    ExportConfig.compression
                ].value,  # compression (nominal)
                cv2.IMWRITE_EXR_TYPE,
                EXR_DEPTH.__members__[
                    {"16": "HALF", "32": "FLOAT"}[ExportConfig.export_color_depth]
                ].value,  # color depth (16, 32 bit floats)
            ]

    def handle_mipmaps(self, mipmaps: str, img):
        """
        img: a wand image object
        """
        from utils.export_utils import calc_mipmaps

        if not mipmaps == "none":
            num_mipmaps = calc_mipmaps(mipmaps, img)
            img.options["dds:mipmaps"] = num_mipmaps
        else:
            img.options["dds:mipmaps"] = "0"

    def determine_if_alpha_is_0(self) -> None:
        if ("A" in self.mode) and (self.compression == "automatic"):
            max_, min_ = (
                self.image.transpose(2, 0, 1)[-1].max(),
                self.image.transpose(2, 0, 1)[-1].min(),
            )
            self.alpha_0 = True if max_ == min_ == 255 else False
        elif not "A" in self.mode:
            self.alpha_0 = True

    def setup_dtype_mapping(self):
        # warn of truncation: float64 -> float32/16 , uint16/8 | float32 -> float16, uint16/8 | uint16 -> uint8
        self.output_dtype_mapping = {
            "float16:float32": lambda channels: np.clip(channels, 0.0, 1.0).astype(
                "float32"
            ),
            "float16:uint8": lambda channels: (
                np.clip(channels, 0.0, 1.0) * 255
            ).astype("uint8"),
            "float16:uint16": lambda channels: (
                np.clip(channels, 0.0, 1.0) * 65535
            ).astype("uint16"),
            "float16:float16": lambda channels: np.clip(channels, 0.0, 1.0).astype(
                "float16"
            ),
            "float32:float16": lambda channels: np.clip(channels, 0.0, 1.0).astype(
                "float16"
            ),
            "float32:float32": lambda channels: np.clip(channels, 0.0, 1.0).astype(
                "float32"
            ),
            "float32:uint8": lambda channels: (
                np.clip(channels, 0.0, 1.0) * 255
            ).astype("uint8"),
            "float32:uint16": lambda channels: (
                np.clip(channels, 0.0, 1.0) * 65535
            ).astype("uint16"),
            "float64:float32": lambda channels: np.clip(channels, 0.0, 1.0).astype(
                "float32"
            ),
            "float64:float16": lambda channels: np.clip(channels, 0.0, 1.0).astype(
                "float16"
            ),
            "float64:uint16": lambda channels: (
                np.clip(channels, 0.0, 1.0) * 65535
            ).astype("uint16"),
            "float64:uint8": lambda channels: (np.clip(channels, 0.0, 1.0) * 255).astype("uint8"),
            "uint8:uint8": lambda channels: channels,
            "uint8:uint16": lambda channels: ((channels.astype("uint16")) * 255),
            "uint8:float32": lambda channels: self.normalize_uint(
                image=channels
            ).astype("float32"),
            "uint16:uint16": lambda channels: channels,
            "uint16:uint8": lambda channels: (channels / 255).astype("uint8"),
            "uint16:float32": lambda channels: self.normalize_uint(
                image=channels
            ).astype("float32"),
        }
