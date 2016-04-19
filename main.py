__author__ = 'Morten'
from PIL import Image
from PIL import ExifTags
import PIL
import os, shutil, hashlib, time

#Folder to start search from:
root_folder = "/Users/Morten/Desktop/Test"
#Folder to place Photos folder:
dest_folder = "/Users/Morten/Desktop/"
#Picture minimum size:
min_width = 500
min_height = 500
#Prepare hash list for detecting duplicates:
hash_dict = {}
#Prepare camera dict
cameras = {}
#Prepare allowed types
allowed_types = {"jpg":True}

def set_dir():
    try:
        os.chdir(root_folder)
    except OSError as e:
        print e

def get_exif(imagepath):
    img = Image.open(imagepath)
    exif = {
        PIL.ExifTags.TAGS[k]: v
        for k, v in img._getexif().items()
        if k in PIL.ExifTags.TAGS
    }

    return exif

def get_year_month(exif):
    exif_split = exif['DateTime'].split(":")
    return [exif_split[0], exif_split[1]]

def check_camera_type(exif):
    try:
        model = exif["Model"]
    except:
        model = "None"

    try:
        make = exif["Make"]
    except:
        make = "None"

    try:
        lens_model = exif["LensModel"]
    except:
        lens_model = "None"

    if not cameras.has_key(model):
        cameras[model] = (make, lens_model)

def check_size(image):
    try:
        img = Image.open(image)
        width = img.size[0]
        height = img.size[1]
        if width > min_width and height > min_height:
            return True
        else:
            return False
    except:
        print "Couldn't open image with path", image
        return False


def check_duplicates(image):
    global hash_dict
    img = open(image).read()
    hash = hashlib.md5(img).hexdigest()
    if hash_dict.has_key(hash):
        return False
    else:
        hash_dict[hash] = True
        return True


def make_dir(folder_path):
    #Make directories to put images in
    try:
        os.makedirs(folder_path)
    except OSError:
        None


def move_image(image_path, count):
    exif = get_exif(image_path)

    check_camera_type(exif)
    
    #Get year and month from exif
    year = get_year_month(exif)[0]
    month = get_year_month(exif)[1]
    #Make path from year and month
    path = dest_folder + "Photos/" + str(year) + "/" + str(month)
    #Make folders in path - returns none if already exists
    make_dir(path)
    #Move image to related path
    try:
        shutil.copyfile(image_path, path + "/img_" + str(count) + ".jpg")
    except:
        print "Error moving image", image_path


def error_image(image_path, count):
    #Set path to error folder
    path = dest_folder + "Photos/Errors"
    #Make error folder. If already exists go to next
    make_dir(path)
    #Move image to related path
    try:
        shutil.copyfile(image_path, path + "/img_" + str(count) + ".jpg")
    except:
        print "Error moving image", image_path

def is_allowed_filetype(filename):
    filetype = filename.lower().split('.')
    return allowed_types.has_key(filetype[len(filetype) - 1])


def main():
    set_dir()
    count = 0
    error_count = 0
    for (dirname, dirs, files) in os.walk('.'):
        for filename in files:
            if is_allowed_filetype(filename):
                tmp_path = os.path.join(dirname, filename)
                if check_size(tmp_path) and check_duplicates(tmp_path):
                    try:
                        move_image(tmp_path, count)
                        count += 1
                    except:
                        print tmp_path, "raised error"
                        error_image(tmp_path, error_count)
                        error_count += 1
    print count, "images were found and copied to the right directory"
    print error_count, "errors were raised and moved to the errors folder"
    print cameras


main()