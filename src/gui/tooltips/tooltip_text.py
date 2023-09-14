# export frame
original_dir = "  Export each image to its  \n  original directory  "
browse = "  Select a single folder  \n  to export images to  "
loading_bar = ""
export = "  Commence upscaling and export (CTRL + E)  "
copy = "  Only copy the currently selected files  \n  to the selected directory (export  \n  options will not be applied)  "
theme = "  Change between dark and light themes  "
increase_gui_scale = "  Increase the scale of GUI elements (experimental)  "
decrease_gui_scale = "  Decrease the scale of GUI elements (experimental)  "

# export options frame
device = " The device to use for upscaling  \n  the selected texture(s). CPU upscaling  \n  is far slower than GPU upscaling. Refer  \n  to the device guide for setting up GPU upscaling."
scale = " Scale the width and heigth of the  \n  texture(s) by the chosen scale.  \n  I.e. a texture with a resolution of [512x256]  \n  with a scale of 2x because a [1024x1024]  \n  resolution image  "
format = " Engine-supported texture format  "
compression = "  PNG: None \n TGA: RLE \n DDS: DXT-1 (no alpha), DXT-3 (supports alpha), DXT-5 (produces a quality alpha than DXT-5)  "
denoise = " Level of noise to add. Noise is added from the original  \n  image, not from an AI model. The more noise that is  \n  added the lower the quality of the final image  \n  "
mipmaps = "  Used for DDS compression. Ex: A 50% mip level will  \n  generate half the possible mipmaps for a texture, i.e.  \n  if a texture's resolution is 512x512 only the  \n  [256x256, 128x128, 64x64, 32x32] mip maps are generated."
prefix = "  Add a prefix to each file name:  \n    [prefix]filename.extension  "
suffix = "  Add a suffix to each file name:  \n    filename[suffix].extension  "
numbered_checkbox = "  Add a unique number to each file name  \n  to avoid overwriting:  \n    ground_texture_[uniquenumber].extension  \n    ground_texture_[uniquenumber].extension  \n    ground_texture_[uniquenumber].extension  "

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
apply_to_chosen_dir = (
    "  Apply filters to files in the chosen directory (Shift + Enter)  "
)

# listbox frame
refresh = "  Refresh the listbox to display files from the  \n  selected source directory (F5)  "
remove_selected = "  Remove selected files from the listbox (Delete)  "
remove_unselected = "  Remove unselected files from the listbox (Shift + Delete)  "
clear_all = "  Remove all the files in the listbox  "
select_all = "  Select all files in the listbox (CTRL + A)  "
deselect_all = "  Deselect all files in the listbox  (Esc)  "


# fof_frame
file = "  Load a single image file  "
folder = "  Load a folder of image files (CTRL + O)  "
recursive = "         (USE WITH CAUTION)  \n     Load images from the selected  \n     folder and all subfolders  "
