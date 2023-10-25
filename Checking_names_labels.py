import slicer
import os,re
import nrrd
import nibabel as nib
import yaml
import logging

# TODO: load the config file
# TODO: load the segmentation file in nrrd
# TODO: check the name valuie match of the labels in the segmentation file
# TODO: if there is a mismatch, correct the labels in the segmentation file

# TODO: nifti code - remember these were evaluated using labelmaps
# TODO: load the segmentation file in nifti
# TODO: check the name value match of the labels in the segmentation file (use the header)
# What is the difference between a labelmap and a segmentation in nrrd in slicer?



###### LOGGING ######
# Set a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create a filehandler with debug level
file_handler = logging.FileHandler('Checking_names_labels.log')
file_handler.setFormatter(formatter)

# create a streamhandler with warning level
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)

# set formatters
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# add handlers to logger
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

#####################


class SegmentationNrrdCheck(SEGMENTER_V2Widget):
    """
    This class is used to check the segmentation nrrd and nifti files file for proper match between names and labbels
    The main method should be called while saving the semgmenatation (onSaveSegmentationButton)
    because the file needs to be checked using the nrrd package (it seems there is no way to do it in slicer!)
    """
    def __init__(self, parent=None):
        # should get self.outputSegmFile (around line 841)
        self.seg_path = seg_path
        self.config_file = config_file
        self.config_yaml = None

    def get_config_values(self):
        with open(self.config_file, 'r') as file:
            self.config_yaml = yaml.safe_load(file)
            logger.info("Loaded configuration values for labels.")
            print("Configuration values for labels.")
            for label in self.config_yaml["labels"]:
                print(20 * "-")
                print(label)
            print(20 * "-")

    def get_case_ID(self):


    def load_nrrd(self):
        seg_nrrd, seg_header = nrrd.read(self.seg_path)
        logger.info("Loaded segmentation file in nrrd format.")
        return seg_nrrd, seg_header

    def load_nifti(self):
        seg_nifti = nib.load(self.seg_path)
        #get the header
        seg_header = seg_nifti.header
        logger.info("Loaded segmentation file in nifti format.")
        return seg_nifti



seg_path= '/Users/laurentletourneau-guillon/Library/CloudStorage/GoogleDrive-laurentletg@gmail.com/My Drive/GDRIVE RECHERCHE/GDRIVE PROJECTS/RSNA ICH IVH DATASET/4_DATA/Revision 03_2023 ICH_IVH/raw_data/Labels_NRRD_unordered/Labels_ANW_PHE_0/ID_bb94c6c7_ANW_PHE_0.seg.nrrd'
config_file = '/Users/laurentletourneau-guillon/Dropbox (Personal)/CHUM/RECHERCHE/2020ICHHEMATOMAS/2023 ICH_SEGMENTER_V2/ICH_SEGMENTER_V2/ICH_SEGMENTER_V2/label_config.yml'
test = Segmentation_Nrrd_Check(seg_path, config_file)

test.get_config_values()

