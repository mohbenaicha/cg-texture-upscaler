import os, shutil

texture_types = ["_d", "_diff", "_diffuse", "_albedo", "albedo", "_alb", "alb", "_color", "_clr"]

def match_tex_type(file, tex_types=texture_types):
    """
    Checks to see if any of the texture types are contained in the file name
    """
    return any([file in tex_type for tex_type in tex_types])

if __name__ == "__main__":
    dest_folder = "shared"
    
    os.makedirs(os.path.join(dest_folder))
    for (root,dirs,files) in os.walk('image_repo', topdown=True):
        for f in files:
            # change to whatever texture containing base material information including diffuse/base color/albedo textures 
            if match_tex_type(file=f):
                shutil.copyfile((
                    os.path.join(root, f), 
                    os.path.join(dest_folder, f))
                )
                