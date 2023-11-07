# export frame

original_dir =       (
                     "  Export each image to its   \n"
                     "   original directory        \n"
)

browse =             (
                    "  Select a single folder   \n" 
                    "  to export images to      \n"
)

loading_bar =         ""
export =             "  Commence upscaling and export (CTRL + E)  "
copy =               (" Only copy the currently selected files  \n" 
                      " to the selected directory (export       \n"
                      " options will not be applied)            \n")
theme =              "  Change between dark and light themes  "
increase_gui_scale = "  Increase the scale of GUI elements (experimental)  "
decrease_gui_scale = "  Decrease the scale of GUI elements (experimental)  "

# export options frame

scale =             (
                    " Scale the width and heigth of the     \n"
                    " texture(s) by the chosen scale.       \n"  
                    " i.e. a texture with a resolution of   \n"   
                    " [512x256] with a scale of 2x because  \n" 
                    " a [1024x1024] resolution image        \n"
                    " Engine-supported texture                "
)

format =            "   Format in which to save selected the images  "

compression =       (
                     " TGA: RLE, None                                                                                      \n"
                     " DDS: DXT-1, DXT-3, DXT-5, None                                                                      \n"
                     " DXT-1 (no alpha)                                                                                    \n"
                     " DXT-3 (supports alpha)                                                                              \n"
                     " DXT-5 (produces a quality alpha than DXT-5)                                                         \n"
                     " BMP: RLE, None (if RLE is chosen, the image will be saved in pallete mode (with 255 indexed colors) \n"
                     " EXR: RLE, ZIP, ZIPS, PIZ (lossless, good for noisy images), PXR24, B44, B44A, DWAA, DWAB, None        "
)
png_compression =   (
                     " PNG compression level: \n"
                     " 0 = no compression     \n"
                     " 1 = low compression    \n"
                     " 9 = high compression     "
)

jpg_compression =   (
                    " JPG  quality:                                                 \n"
                    " 1 results in the lowest quality but also size of the image    \n"
                    " 100 results in the highest quality but also size of the image   "
)

denoise =          (" Level of noise to add. Noise is added from the original  \n"
                    " image, not from an AI model. The more noise that is      \n"
                    " added the lower the quality of the final image             "
        )
mipmaps =          (" Used for DDS compression. Ex: A 50% mip level will       \n"
                    " generate half the possible mipmaps for a texture, i.e.   \n"
                    " if a texture's resolution is 512x512 only the            \n"
                    " [256x256, 128x128, 64x64, 32x32] mip maps are generated.   "
)
prefix =           (" Add a prefix to each file name:  \n   " 
                    " [prefix]filename.extension            ")
suffix =            (" Add a suffix to each file name:   \n"    
                    " filename[suffix].extension        \n")

numbered_checkbox = ("  Add a unique number to each file name  \n"
                     " to avoid overwriting:                   \n"
                     " ground_texture_[uniquenumber].extension \n"  
                     " ground_texture_[uniquenumber].extension \n" 
                     " ground_texture_[uniquenumber].extension   ")

# UI/app config frame
load_config = "  Load a search and export configuration.  "
save_config = "  Save the current search and export configuration.  "
theme = "  Change between light and dark themes.  "
ui_scale = "  This feature is still in the experimental stage.  "

# search_filter_frame
and_filters = ""
or_filters = ""
clear_all_filters = "  Clear search filters (Esc)  "
apply_to_current_list = "  Apply filters to files in the listbox (Enter)  "
apply_to_chosen_dir = "  Apply filters to files in the chosen directory (Shift + Enter)  "

# listbox frame
refresh =           "  Refresh the listbox to display files from the selected source directory (F5)  "
remove_selected =   "  Remove selected files from the listbox (Delete)  "
remove_unselected = "  Remove unselected files from the listbox (Shift + Delete)  "
clear_all =         "  Remove all the files in the listbox  "
select_all =        "  Select all files in the listbox (CTRL + A)  "
deselect_all =      "  Deselect all files in the listbox  (Esc)  "


# fof_frame
file =      "  Load a single image file  "
folder =    "  Load a folder of image files (CTRL + O)  "
recursive = ("         (USE WITH CAUTION)   \n"     
            " Load images from the selected \n"     
            " folder and all subfolders       ")

# additional settings frame

browsermode =       (" Selecting an image in the listbox    \n"
                     " using the mouse or up and down       \n"
                     " arrow keys will automatically open   \n"
                     " it in the image viewer.                ")

device =           ("  The device to use for upscaling                  \n " 
                    " the selected texture(s). CPU upscaling            \n "
                    " is far slower than GPU upscaling. Refer           \n "
                    " to the device guide for setting up GPU upscaling.    ")

color_space =      (" NOTE: In and Out mean VERY DIFFERENT things:    \n\n"
                    " Linear In and sRGB In are guidance you give     \n"
                    " to the application based on the way your images \n"
                    " are written. The applicaion cannot determine    \n"
                    " on its own.                                     \n\n"
                    " Linear Out and sRGB Out are handled by the      \n"
                    " so if you want the upscaled image written in    \n"
                    " in linear RGB colors, select Linear Out and     \n"
                    " the like if you want them written in sRGB.      \n"
                    
)
gamma_adjustment = (
                    " If your images are written with a gamma that isn't 1.0    \n"
                    " and the upscaled images look off, adjust this setting.    \n"
)
color_mode =       (" Export images as RGB or greyscale images.     \n "
                    " Note: DDS formats do no support the greyscale \n "
                    " color mode.                                   \n ")

color_depth =       (" The the processed images will be \n"
                     " exported based on the chosen bit \n" 
                     " depth, or based on the highest   \n" 
                     " supported bit depth for the      \n"
                     " selected chosen format.          \n" 
                     " Per channel pixel depth:         \n"
                     " PNG: 8, 16 \n"
                     " JPG: 8 \n"
                     " TGA: 8 \n"
                     " DDS: 8 \n"
                     " BMP: 8 \n"
                     " EXR: 16, 32 \n"
                    )
upscale_precision = (" Recommended: normal precision. High \n" 
                     " precision uses significantly more   \n"
                     " video memory and takes longer to    \n"
                     " process and doesn't split images to \n"
                     " avoid running out of video memory.    ")

split_large_image = (" (Recommended) If an image is too large \n"
                     " for your video memory, it will be split\n" 
                     " into individual images, upscaled, then \n"
                     " he two new images are recombined.        ")
pad_size =         (" Recommended: 10%. The size of the margines   \n" 
                    " to use when splitting the image to be        \n"
                    " processed a larger pad size results in a     \n"
                    " better final image but comes at greater      \n" 
                    " memory cost. Too large of a pad size may     \n"
                    " result in distortions or bluriness.            ")
