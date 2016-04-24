import sys
from PySide import QtGui
from PySide.QtCore import *
from PIL import Image
from PIL import ExifTags
import PIL
import os
import shutil
import hashlib
import time
from PySide.QtGui import QMessageBox

class Window(QtGui.QWidget):

    root_folder = None
    dest_folder = None

    def __init__(self):
        super(Window, self).__init__()

        self.init_ui()

    def init_ui(self):

        vbox = QtGui.QVBoxLayout()

        #Create label for root folder selection
        root_folder_description = QtGui.QHBoxLayout()
        description_label = QtGui.QLabel("Select folder to start from:")
        description_label.setFont(QtGui.QFont('SansSerif', 14))
        root_folder_description.addWidget(description_label)

        #Create textbox and button to select root folder
        folder_selection = QtGui.QHBoxLayout()
        self.choose_root_btn = self.button("Browse...")
        root_folder_txt = QtGui.QLineEdit()
        folder_selection.addWidget(root_folder_txt)
        folder_selection.addWidget(self.choose_root_btn)

        #Add all components to the overlying vbox. 
        vbox.addLayout(root_folder_description)
        vbox.addLayout(folder_selection)

#############################################################################
        self.progress_bar = QtGui.QProgressBar()
        

        self.progress_bar.setTextVisible(True)
    

        vbox.addWidget(self.progress_bar)
####################################################################

        
        vbox.addStretch(1)

        #Open window
        self.resize(450,450)
        self.center()


        self.setLayout(vbox)
        self.setWindowTitle('ImageSorter')

####################################################################


        #TEST HERE:
        self.connect(self.choose_root_btn, SIGNAL("clicked()"), self.process_data)

        self.image_sorter = ImageSorter(self, 
            root_folder="/Users/Morten/Desktop/Test", 
            dest_folder="/Users/Morten/Desktop/",
            min_width = 500,
            min_height = 500,
            allowed_types=["jpg"] )

        self.connect(self.image_sorter, SIGNAL("count_completed(qint32)"), self.done_counting, Qt.DirectConnection)

        self.connect(self.image_sorter, SIGNAL("update_progress(qint16)"), self.update_progress_bar, Qt.DirectConnection)

        self.connect(self.image_sorter, SIGNAL("finished()"), self.sorting_done, Qt.DirectConnection)

#####################################################################

        self.show()


    def button(self, text):
        button = QtGui.QPushButton(text)
        button.setFont(QtGui.QFont('SansSerif', 12))
        return button

    def center(self):
        
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def process_data(self):
        self.image_sorter.start()
        print "started"

    def done_counting(self, message):
        print message

    def update_progress_bar(self, percent):
        self.progress_bar.setValue(percent)

    def sorting_done(self):
        print "DONE!"

    #Overrides normal close event. Makes sure you don't mistakenly close while running.
    def closeEvent(self, event):
        if self.image_sorter.isRunning():
            event.ignore()
        else:
            event.accept()








class ImageSorter(QThread):
    #Folder to start search from:
    root_folder = None
    #Folder to place Photos folder:
    dest_folder = None
    #Picture minimum size:
    min_width = 0
    min_height = 0
    #Prepare allowed types
    allowed_types = None

    #Prepare hash list for detecting duplicates:
    hash_dict = {}
    #Prepare camera dict
    cameras = {}
    #Duplicate count
    duplicates = 0

    gui = None

    def __init__(self, parent=None, *args, **kw):
        super(ImageSorter, self).__init__(parent)
        self.set_variables(*args, **kw)

    def set_variables(self, root_folder, dest_folder, min_width, min_height, allowed_types):
        self.root_folder = root_folder
        self.dest_folder = dest_folder
        self.min_width = min_width
        self.min_height = min_height
        self.allowed_types = allowed_types



    def set_dir(self):
        try:
            os.chdir(self.root_folder)
        except OSError as e:
            print e

    def get_exif(self, img):
        try:
            exif = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in img._getexif().items()
                if k in PIL.ExifTags.TAGS
            }
        except:
            exif = {"Model":"No Exif"}

        return exif

    def get_year_month(self, exif):
        exif_split = exif['DateTime'].split(":")
        return [exif_split[0], exif_split[1]]

    def check_camera_type(self, exif):
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

        if not self.cameras.has_key(model):
            self.cameras[model] = (make, lens_model)

        return model

    def check_size(self, img):
        try:
            width = img.size[0]
            height = img.size[1]
            if width > self.min_width and height > self.min_height:
                return True
            else:
                return False
        except:
            #TODO: Should raise an exception here. 
            None


    def check_duplicates(self, image):
        #TODO: Do these need to be specified global? 
        #TODO: should it really only read 10000? 
        img = open(image).read(10000)
        hash = hashlib.md5(img).hexdigest()
        if self.hash_dict.has_key(hash):
            self.duplicates += 1
            return False
        else:
            self.hash_dict[hash] = True
            return True


    def make_dir(self, folder_path):
        #Make directories to put images in
        try:
            os.makedirs(folder_path)
        except OSError:
            None


    def move_image(self, image_path, camera_type, count, exif):
        #Get year and month from exif
        date = self.get_year_month(exif)
        year = date[0]
        month = date[1]
        #Make path from year and month
        path = ''.join([self.dest_folder , "Photos/" , camera_type , "/" , str(year) , "/" , str(month)])
        #Make folders in path - returns none if already exists
        self.make_dir(path)
        #Move image to related path
        try:
            shutil.copyfile(image_path, path + "/img_" + str(count) + ".jpg")
        except:
            print "Error moving image", image_path


    def handle_error(self, image_path, count):
        #Set path to error folder
        path = self.dest_folder + "Photos/Errors"
        
        #Make error folder.
        self.make_dir(path)

        #Move image to related path
        try:
            shutil.copyfile(image_path, path + "/img_" + str(count) + ".jpg")
        except:
            print "Error moving image", image_path

    def is_allowed_filetype(self, filename):
        filetype = filename.lower().split('.')
        return (filetype[len(filetype) - 1] in self.allowed_types)


    def run(self):
        print "Running on folder:", self.root_folder
        start = time.time()
        self.set_dir()
        count = 0
        total_count = 0
        error_count = 0
        file_count=0
        
        #Count all images. 
        print "Counting all files in directory..."
        for (dirname, dirs, files) in os.walk('.'):
            for filename in files:
                file_count+=1

        self.emit(SIGNAL("count_completed(qint32)"), file_count)

        #Remember total count. 
        total_count = file_count
        update_frequency = total_count / 25

        print "Sorting initiated:"
        for (dirname, dirs, files) in os.walk('.'):
            for filename in files:
                
                #Calculation for percent finished. 
                file_count -= 1

                if file_count%update_frequency == 0:
                    percent = (((total_count-file_count)*100)/total_count)
                    print percent, "% finished"
                    self.emit(SIGNAL("update_progress(qint16)"), percent)

                if self.is_allowed_filetype(filename):
                    tmp_path = os.path.join(dirname, filename)
                    try: 
                        img = Image.open(tmp_path)
                        exif = self.get_exif(img)

                        
                        if self.check_size(img) and self.check_duplicates(tmp_path):
                            camera_type = self.check_camera_type(exif)
                            
#################################################################################################################
                            time.sleep(0.02)
#################################################################################################################

                            try:
                                self.move_image(tmp_path, camera_type, count, exif)
                                count += 1
                            except:
                                #print tmp_path, "raised error"
                                self.handle_error(tmp_path, error_count)
                                error_count += 1
                    except:
                        x=1
        print count, "images were found and copied to the right directory"
        print error_count, "errors were raised and moved to the errors folder"
        print self.duplicates, "duplicates were found"
        print "Exuction time", time.time() - start




def main():
    app = QtGui.QApplication(sys.argv)

    window = Window()
    sys.exit(app.exec_())


main()