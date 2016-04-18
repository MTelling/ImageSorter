__author__ = 'Morten'
from PIL import Image
from PIL import ExifTags
import PIL
import os, shutil, hashlib

#Folder to start search from:
root_folder = "/Volumes/Tellling/Billeder"
#Folder to place Photos folder:
dest_folder = "/Users/Morten/Desktop/"
#Picture minimum size:
min_width = 500
min_height = 500
#Prepare hash list for detecting duplicates:
hash_list = []

def set_dir():
    try:
        os.chdir(root_folder)
    except OSError as e:
        print e


def get_year_month(imagepath):
    img = Image.open(imagepath)
    exif = {
        PIL.ExifTags.TAGS[k]: v
        for k, v in img._getexif().items()
        if k in PIL.ExifTags.TAGS
    }
    exif_split = exif['DateTime'].split(":")
    return [exif_split[0], exif_split[1]]


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
    global hash_list
    img = open(image).read()
    hash = hashlib.md5(img).hexdigest()
    if hash in hash_list:
        return False
    else:
        hash_list.append(hash)
        return True


def make_dir(folder_path):
    #Make directories to put images in
    try:
        os.makedirs(folder_path)
    except OSError:
        None


def move_image(image_path, count):
    #Get year and month from exif
    year = get_year_month(image_path)[0]
    month = get_year_month(image_path)[1]
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


def main():
    count = 0
    error_count = 0
    for (dirname, dirs, files) in os.walk('.'):
        for filename in files:
            if filename.lower().endswith('.jpg'):
                tmp_path = os.path.join(dirname, filename)
                if check_size(tmp_path) and check_duplicates(tmp_path):
                    try:
                        count += 1
                        move_image(tmp_path, count)
                    except:
                        error_count += 1
                        print tmp_path, "raised error"
                        error_image(tmp_path, error_count)
    print hash_list
    print count, "images were found and copied to the right directory"
    print error_count, "errors were raised and moved to the errors folder"


set_dir()
main()