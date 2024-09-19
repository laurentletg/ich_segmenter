# To install a package in slicer python environment, use the following command:
# pip install --user package_name
import os
from glob import glob
import re
import time
import yaml
from pathlib import Path
from threading import RLock

import qt, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import slicerio # cannot install in slicer
import SegmentStatistics
import ScreenCapture

import pandas as pd
import numpy as np

import nrrd
import nibabel as nib

# TODO: add all constants to the config file
CONFIG_FILE_PATH = os.path.join(Path(__file__).parent.resolve(), "config.yaml")

TIMER_MUTEX = RLock()
#comment

class SemiAutoPheToolThresholdWindow(qt.QWidget):
   def __init__(self, segmenter, parent = None):
      super(SemiAutoPheToolThresholdWindow, self).__init__(parent)
      
      self.segmenter = segmenter
      self.LB_HU_value = segmenter.LB_HU
      self.UB_HU_value = segmenter.UB_HU

      layout = qt.QVBoxLayout()
      self.textLabel = qt.QLabel("Threshold bounds: ")
      self.textLabel.setStyleSheet("font-weight: bold")
      layout.addWidget(self.textLabel)

      self.minimumLabel = qt.QLabel("Minimum")
      layout.addWidget(self.minimumLabel)
      
      self.semiAutoPHE_LB_HU_spinbox = qt.QSpinBox()
      self.semiAutoPHE_LB_HU_spinbox.valueChanged.connect(self.LB_HU_valueChanged)
      layout.addWidget(self.semiAutoPHE_LB_HU_spinbox)
      self.semiAutoPHE_LB_HU_spinbox.setMinimum(-32000)
      self.semiAutoPHE_LB_HU_spinbox.setMaximum(29000)
      self.semiAutoPHE_LB_HU_spinbox.setValue(self.LB_HU_value)

      self.maximumLabel = qt.QLabel("Maximum")
      layout.addWidget(self.maximumLabel)
      
      self.semiAutoPHE_UB_HU_spinbox = qt.QSpinBox()
      self.semiAutoPHE_UB_HU_spinbox.valueChanged.connect(self.UB_HU_valueChanged)
      layout.addWidget(self.semiAutoPHE_UB_HU_spinbox)
      self.semiAutoPHE_UB_HU_spinbox.setMinimum(-32000)
      self.semiAutoPHE_UB_HU_spinbox.setMaximum(29000)
      self.semiAutoPHE_UB_HU_spinbox.setValue(self.UB_HU_value)

      self.continueButton = qt.QPushButton('Continue')
      self.continueButton.clicked.connect(self.pushContinue)
      layout.addWidget(self.continueButton)

      self.cancelButton = qt.QPushButton('Cancel')
      self.cancelButton.clicked.connect(self.pushCancel)
      layout.addWidget(self.cancelButton)

      self.setLayout(layout)
      self.setWindowTitle("Semi-automatic PHE Tool")
      self.resize(400, 200)

   def UB_HU_valueChanged(self):
      self.UB_HU_value = self.semiAutoPHE_UB_HU_spinbox.value
      self.segmenter.ApplyThresholdPHE(self.LB_HU_value, self.UB_HU_value)

   def LB_HU_valueChanged(self):
      self.LB_HU_value = self.semiAutoPHE_LB_HU_spinbox.value
      self.segmenter.ApplyThresholdPHE(self.LB_HU_value, self.UB_HU_value)

   def pushContinue(self):
       self.segmenter.setUpperAndLowerBoundHU(self.LB_HU_value, self.UB_HU_value)
       
       self.instructionsWindow = SemiAutoPheToolInstructionsWindow(self.segmenter)
       self.instructionsWindow.show()
       
       self.close()

   def pushCancel(self):
       self.segmenter.ClearPHESegment()
       self.close()

class SemiAutoPheToolInstructionsWindow(qt.QWidget):
   def __init__(self, segmenter, parent = None):
      super(SemiAutoPheToolInstructionsWindow, self).__init__(parent)
      
      self.segmenter = segmenter

      layout = qt.QVBoxLayout()
      self.textLabel = qt.QLabel("Instructions:")
      self.textLabel.setStyleSheet("font-weight: bold")
      layout.addWidget(self.textLabel)

      self.minimumLabel = qt.QLabel("Click <b>Continue</b> and draw a generous boundary of the ICH and PHE complex. Note that the boundary may be drawn in multiple views. When you are finished drawing the boundary, click on <b>Show Result</b> in the main extension menu. "
                                    + "The HU thresholds and manual fine-tuning of included voxels are left to the annotator\'s discretion. "
                                    + "\n(If a popup message about visibility shows up, click <b>No</b>.)")
      self.minimumLabel.setWordWrap(True)
      layout.addWidget(self.minimumLabel)

      self.continueButton = qt.QPushButton('Continue')
      self.continueButton.clicked.connect(self.pushContinue)
      layout.addWidget(self.continueButton)

      self.cancelButton = qt.QPushButton('Cancel')
      self.cancelButton.clicked.connect(self.pushCancel)
      layout.addWidget(self.cancelButton)

      self.setLayout(layout)
      self.setWindowTitle("Semi-automatic PHE Tool")
      self.resize(400, 200)

   def pushContinue(self):
       self.segmenter.ApplySemiAutomaticThresholdAlgorithm()
       self.close()

   def pushCancel(self):
       self.segmenter.ClearPHESegment()
       self.close()

class SEGMENTER_V2(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "SEGMENTER_V2"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["Delphine Pilon, An Ni Wu, Emmanuel Montagnon, Laurent Letourneau-Guillon"]  # TODO: replace with "Firstname Lastname (Organization)"
    # TODO: update with short description of the module and a link to online module documentation
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#SEGMENTER_V2">module documentation</a>.
"""
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
Module supported by funding from : 
1. Fonds de Recherche du Québec en Santé and Fondation de l’Association des Radiologistes du Québec
Radiology Research funding (299979) and Clinical Research Scholarship–Junior 1 Salary Award (311203)
2. Foundation of the Radiological Society of North America - Seed Grant (RSD2122)
3. Quebec Bio-Imaging Network, 2022 pilot project grant (Project no 21.24)
4. Support professoral du Département de radiologie, radio-oncologie et médecine nucléaire de l’Université de Montréal, Radiology departement  Centre Hospitalier de l’Université de Montréal (CHUM) and CHUM Research Center (CRCHUM) start-up funds

Thanks to the Slicer community for the support and the development of the software.

"""

class Timer():
    def __init__(self, number=None):
        with TIMER_MUTEX:
            self.number = number
            self.total_time = 0
            self.inter_time = 0
            # counting flag to allow to PAUSE the time
            self.flag = False # False = not counting, True = counting (for pause button)


    def start(self):
        with TIMER_MUTEX:
            if self.flag == False:
                # start counting flag (to allow to pause the time if False)
                self.flag = True
                self.start_time = time.time()
            
            
    def stop(self):
        with TIMER_MUTEX:
            if self.flag == True:
                self.inter_time = time.time() - self.start_time
                self.total_time += self.inter_time
                self.flag = False


class SEGMENTER_V2Widget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False
        # LLG CODE BELOW
        self.predictions_names= None


        # ----- ANW Addition  ----- : Initialize called var to False so the timer only stops once
        self.called = False
        self.called_onLoadPrediction = False
        self.segmentationNode = None



    def get_config_values(self):
        with open(CONFIG_FILE_PATH, 'r', encoding = 'utf-8') as file:
            self.config_yaml = yaml.safe_load(file)
        print("DEBUG configuration values for labels.")
        for label in self.config_yaml["labels"]:
            print(20*"-")
            print(label)
            print(20*"-")


    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ### Segment editor widget
        self.layout.setContentsMargins(4, 0, 4, 0)

        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/ICH_SEGMENTER_V2.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = SEGMENTER_V2Logic()


        # CONFIG - could be removed
        self.get_config_values()
        self.DEFAULT_VOLUME_DIR = self.config_yaml['default_volume_directory']
        self.CurrentFolder = self.DEFAULT_VOLUME_DIR
        self.DEFAULT_SEGMENTATION_DIR = self.config_yaml['default_segmentation_directory']
        print(f'Default directory location: {self.DEFAULT_SEGMENTATION_DIR}')
        self.VOLUME_FILE_TYPE = self.config_yaml['volume_extension']
        self.SEGM_FILE_TYPE = self.config_yaml['segmentation_extension']
        self.VOL_REGEX_PATTERN = self.config_yaml['regex_format_volume_load']
        self.VOL_REGEX_PATTERN_PT_ID_INSTUID_SAVE = self.config_yaml['regex_format_volume_save']
        self.SEGM_REGEX_PATTERN = self.config_yaml['regex_format_segmentation_load']
        self.OUTLIER_THRESHOLD_LB = self.config_yaml['OUTLIER_THRESHOLD']['LOWER_BOUND']
        self.OUTLIER_THRESHOLD_UB = self.config_yaml['OUTLIER_THRESHOLD']['UPPER_BOUND']


        self.LB_HU = self.config_yaml["labels"][0]["lower_bound_HU"]
        self.UB_HU = self.config_yaml["labels"][0]["upper_bound_HU"]

        # CONNECTION
        self.ui.PauseTimerButton.setText('Pause')
        self.ui.pushButton_uint8casting.connect('clicked(bool)', self.onPushButton_uint8casting)
        self.ui.getDefaultDir.connect('clicked(bool)', self.getDefaultDir)
        self.ui.BrowseFolders.connect('clicked(bool)', self.onBrowseFoldersButton)
        self.ui.SlicerDirectoryListView.clicked.connect(self.getCurrentTableItem)
        self.ui.SaveSegmentationButton.connect('clicked(bool)', self.onSaveSegmentationButton)
        self.ui.BrowseFolders_2.connect('clicked(bool)', self.onBrowseFolders_2Button)
        self.ui.LoadPrediction.connect('clicked(bool)', self.load_mask_v2)
        self.ui.Previous.connect('clicked(bool)', self.onPreviousButton)
        self.ui.Next.connect('clicked(bool)', self.onNextButton)
        self.ui.pushButton_Paint.connect('clicked(bool)', self.onPushButton_Paint)
        self.ui.pushButton_ToggleVisibility.connect('clicked(bool)', self.onPushButton_ToggleVisibility)
        self.ui.PushButton_segmeditor.connect('clicked(bool)', self.onPushButton_segmeditor)
        self.ui.pushButton_Erase.connect('clicked(bool)', self.onPushButton_Erase)
        self.ui.pushButton_Smooth.connect('clicked(bool)', self.onPushButton_Smooth)
        self.ui.pushButton_Small_holes.connect('clicked(bool)', self.onPushButton_Small_holes)
        self.ui.pushButton_SemiAutomaticPHE_Launch.connect('clicked(bool)', self.onPushButton_SemiAutomaticPHE_Launch)
        self.ui.pushButton_SemiAutomaticPHE_ShowResult.connect('clicked(bool)', self.onPushButton_SemiAutomaticPHE_ShowResult)
        self.ui.dropDownButton_label_select.currentIndexChanged.connect(self.onDropDownButton_label_select)
        self.ui.PauseTimerButton.connect('clicked(bool)', self.togglePauseTimerButton)
        self.ui.StartTimerButton.connect('clicked(bool)', self.toggleStartTimerButton)
        self.ui.pushButton_ToggleFill.connect('clicked(bool)', self.toggleFillButton)
        self.ui.SegmentWindowPushButton.connect('clicked(bool)', self.onSegmentEditorPushButton)
        self.ui.UB_HU.valueChanged.connect(self.onUB_HU)
        self.ui.LB_HU.valueChanged.connect(self.onLB_HU)
        self.ui.pushDefaultMin.connect('clicked(bool)', self.onPushDefaultMin)
        self.ui.pushDefaultMax.connect('clicked(bool)', self.onPushDefaultMax)
        self.ui.pushButton_undo.connect('clicked(bool)', self.onPushButton_undo)
        self.ui.testButton.connect('clicked(bool)', self.save_statistics)
        self.ui.pushButton_check_errors_labels.connect('clicked(bool)', self.check_for_outlier_labels)
        self.ui.pushButton_test1.connect('clicked(bool)', self.keyboard_toggle_fill)
        self.ui.pushButton_test2.connect('clicked(bool)', self.onpushbuttonttest2)
        self.ui.pushButton_get_line_measure.connect('clicked(bool)', self.get_line_measure)
        self.ui.pushButton_screenshot.connect('clicked(bool)', self.get_screenshot)

        # Set annotator details
        self.ui.Annotator_name.setText(self.config_yaml['annotator_name'])
        self.ui.AnnotatorDegree.setCurrentIndex(self.config_yaml['annotator_degree'])
        self.ui.RevisionStep.setCurrentIndex(self.config_yaml['revision_step'])
        self.annotator_name = self.ui.Annotator_name.text
        self.annotator_degree = self.ui.AnnotatorDegree.currentText
        self.revision_step = self.ui.RevisionStep.currentText

        # KEYBOARD SHORTCUTS
        keyboard_shortcuts = []
        for i in self.config_yaml["KEYBOARD_SHORTCUTS"]:
            shortcutKey = i.get("shortcut")
            callback_name = i.get("method")
            callback = getattr(self, callback_name)
            keyboard_shortcuts.append((shortcutKey, callback))

        print(f'keyboard_shortcuts: {keyboard_shortcuts}')


        for (shortcutKey, callback) in keyboard_shortcuts:
            shortcut = qt.QShortcut(slicer.util.mainWindow())
            shortcut.setKey(qt.QKeySequence(shortcutKey))
            shortcut.connect("activated()", callback)



        #LABELS
        for label in self.config_yaml["labels"]:
            self.ui.dropDownButton_label_select.addItem(label["name"])

        self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(False)
        self.disablePauseTimerButton()
        self.disableSegmentAndPaintButtons()

        self.enableStartTimerButton()

        self.ui.ThresholdLabel.setStyleSheet("font-weight: bold")
        self.ui.SemiAutomaticPHELabel.setStyleSheet("font-weight: bold")

        self.ui.UB_HU.setMinimum(-32000)
        self.ui.LB_HU.setMinimum(-32000)
        self.ui.UB_HU.setMaximum(29000)
        self.ui.LB_HU.setMaximum(29000)

        self.ui.pushButton_ToggleFill.setStyleSheet("background-color : indianred")
        self.ui.SegmentWindowPushButton.setStyleSheet("background-color : lightgray")
        self.ui.pushButton_ToggleVisibility.setStyleSheet("background-color : lightgreen")
        self.ui.lcdNumber.setStyleSheet("background-color : black")

        # Change the value of the upper and lower bound of the HU
        self.ui.UB_HU.setValue(self.UB_HU)
        self.ui.LB_HU.setValue(self.LB_HU)

        ### ANW ICH TYPE/LOCATION CONNECTIONS
        self.listichtype = [self.ui.ichtype1, self.ui.ichtype2, self.ui.ichtype3, self.ui.ichtype4, self.ui.ichtype5,
                            self.ui.ichtype6, self.ui.ichtype7, self.ui.ichtype8, self.ui.ichtype9]
        self.listichloc = [self.ui.ichloc1, self.ui.ichloc2, self.ui.ichloc3, self.ui.ichloc4, self.ui.ichloc5,
                           self.ui.ichloc6, self.ui.ichloc7, self.ui.ichloc8, self.ui.ichloc9, self.ui.ichloc10]

        self.listEMs = [self.ui.EM_barras_density, self.ui.EM_barras_margins, self.ui.EM_black_hole, self.ui.EM_blend,
                        self.ui.EM_fl_level, self.ui.EM_hypodensity, self.ui.EM_island, self.ui.EM_satellite, self.ui.EM_swirl]


        self.flag_ICH_in_labels = False
        self.flag_PHE_in_labels = False
        for label in self.config_yaml["labels"]:
            if "ICH" in label["name"].upper() or "HEMORRHAGE" in label["name"].upper() or "HÉMORRAGIE" in label["name"].upper() or "HEMORRAGIE" in label["name"].upper() or "HAEMORRHAGE" in label["name"].upper():
                self.flag_ICH_in_labels = True
            if "PHE" in label["name"].upper() or "EDEMA" in label["name"].upper() or "OEDEME" in label["name"].upper() or "OEDÈME" in label["name"].upper():
                self.flag_PHE_in_labels = True

        # Initialize timers
        self.timers = []
        timer_index = 0
        for label in self.config_yaml["labels"]:
            self.timers.append(Timer(number=timer_index))
            timer_index = timer_index + 1

        self.MostRecentPausedCasePath = ""

        if not self.flag_ICH_in_labels:
            self.ui.MRMLCollapsibleButton.setVisible(False)
        if not self.flag_PHE_in_labels:
            self.ui.SemiAutomaticPHELabel.setVisible(False)
            self.ui.pushButton_SemiAutomaticPHE_Launch.setVisible(False)
            self.ui.pushButton_SemiAutomaticPHE_ShowResult.setVisible(False)


        if self.annotator_name and self.revision_step:
            self.createFolders()

    def setUpperAndLowerBoundHU(self, inputLB_HU, inputUB_HU):
      self.LB_HU = inputLB_HU
      self.UB_HU = inputUB_HU
      self.ui.UB_HU.setValue(self.UB_HU)
      self.ui.LB_HU.setValue(self.LB_HU)

    def enableSegmentAndPaintButtons(self):
        self.ui.pushButton_Paint.setEnabled(True)
        self.ui.pushButton_Erase.setEnabled(True)
        self.ui.pushButton_SemiAutomaticPHE_Launch.setEnabled(True)

    def disableSegmentAndPaintButtons(self):
        self.ui.pushButton_Paint.setEnabled(False)
        self.ui.pushButton_SemiAutomaticPHE_Launch.setEnabled(False)
        self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(False)
        self.ui.pushButton_Erase.setEnabled(False)

    def getDefaultDir(self):
      self.DEFAULT_VOLUME_DIR = qt.QFileDialog.getExistingDirectory(None, "Open default directory", self.DEFAULT_VOLUME_DIR, qt.QFileDialog.ShowDirsOnly)

    def onPushButton_uint8casting(self):
      """
      Check for dtype in nrrd or nifti files and cast to uint8 if not already - this causes issues
      in Slicer 5.6 (vector error). Segmentation file should anyway be uint8, not float.

      """
      # message box to confirm overwriting
      print(self.predictions_paths[0])
      reply = qt.QMessageBox.question(None, 'Message', 'Casiting to uint8. Do you want to overwrite the original segmentation files?', qt.QMessageBox.Yes | qt.QMessageBox.No, qt.QMessageBox.No)
      if reply == qt.QMessageBox.No:
          raise ValueError('The segmentation files were not overwritten.')
      else:
          self.cast_segmentation_to_uint8()

    def cast_segmentation_to_uint8(self):

      for case in self.predictions_paths:
          # Load the segmentation
          input_path = os.path.basename(case)
          if input_path.endswith('.nii') or input_path.endswith('.nii.gz'):
              segm = nib.load(case)
              segm_data_dtype = segm.dataobj
              print(f'infile: {input_path}, dtype: {segm_data_dtype}')
              if segm_data_dtype != np.uint8:
                  segm_data = segm.get_fdata()
                  segm_data = segm_data.astype(np.uint8)
                  segm_nii = nib.Nifti1Image(segm_data, segm.affine, segm.header)
                  nib.save(segm_nii, case)
                  print(f'converted file {input_path} to uint8')
          elif input_path.endswith('seg.nrrd'):
              segm_data, header = nrrd.read(case)
              print(f'infile: {input_path}, dtype: {segm_data.dtype}')
              if segm_data.dtype != np.uint8:
                  segm_data = segm_data.astype(np.uint8)
                  header['type'] = 'unsigned char'
                  nrrd.write(case, segm_data, header = header)
                  print(f'converted file {input_path} to uint8')
          else:
              raise ValueError('The input segmentation file must be in nii, nii.gz or nrrd format.')

    def onBrowseFoldersButton(self):
      # LLG get dialog window to ask for directory
      self.CurrentFolder= qt.QFileDialog.getExistingDirectory(None,"Open a folder", self.DEFAULT_VOLUME_DIR, qt.QFileDialog.ShowDirsOnly)
      self.updateCurrentFolder()
      # LLG GET A LIST OF cases WITHIN CURRENT FOLDERS (SUBDIRECTORIES). List comp to get only the case
      self.CasesPaths = sorted(glob(f'{self.CurrentFolder}{os.sep}{self.VOLUME_FILE_TYPE}'))

      print(os.path.basename(self.CasesPaths[0]))
      try:
          self.Cases = sorted([re.findall(self.VOL_REGEX_PATTERN,os.path.split(i)[-1])[0] for i in self.CasesPaths])
      except IndexError:
          print('issue with regex')

      self.update_UI_case_list()

    def update_UI_case_list(self):
      self.ui.SlicerDirectoryListView.clear()
      # Populate the SlicerDirectoryListView
      self.ui.SlicerDirectoryListView.addItems(self.Cases)
      self.currentCase_index = 0  # THIS IS THE CENTRAL THING THAT HELPS FOR CASE NAVIGATION
      self.updateCaseAll()
      self.loadPatient()

    def updateCaseAll(self):
      # All below is dependent on self.currentCase_index updates,
      self.currentCase = self.Cases[self.currentCase_index]
      self.currentCasePath = self.CasesPaths[self.currentCase_index]
      self.updateCurrentPatient()
      # Highlight the current case in the list view (when pressing on next o)
      self.ui.SlicerDirectoryListView.setCurrentItem(self.ui.SlicerDirectoryListView.item(self.currentCase_index))

    def getCurrentTableItem(self):
      # ----- ANW Addition ----- : Reset timer when change case and uncheck all checkboxes
      self.resetTimer()
      self.uncheckAllBoxes()
      self.clearTexts()

      # When an item in SlicerDirectroyListView is selected the case number is printed
      # below we update the case index and we need to pass one parameter to the methods since it takes 2 (1 in addition to self)
      self.updateCaseIndex(self.ui.SlicerDirectoryListView.currentRow) # Index starts at 0
      # Update the case index
      self.currentCase_index = self.ui.SlicerDirectoryListView.currentRow
      # Same code in onBrowseFoldersButton, need to update self.currentCase
      # note that updateCaseAll() not implemented here - it is called when a case is selected from the list view or next/previous button is clicked
      self.currentCase = self.Cases[self.currentCase_index]
      self.currentCasePath = self.CasesPaths[self.currentCase_index]
      self.updateCurrentPatient()
      self.loadPatient()

      # ----- ANW Addition ----- : Reset timer when change case, also reset button status
      self.resetTimer()

    def updateCaseIndex(self, index):
      # ----- ANW Modification ----- : Numerator on UI should start at 1 instead of 0 for coherence
      self.ui.FileIndex.setText('{} / {}'.format(index+1, len(self.Cases)))

    def updateCurrentFolder(self):
      self.ui.CurrentFolder.setText('Current folder : \n...{}'.format(self.CurrentFolder[-80:]))

    def updateCurrentPatient(self):
      self.ui.CurrentPatient.setText(f'Current case : {self.currentCase}')
      self.updateCaseIndex(self.currentCase_index)

    def updateCurrentSegmenationLabel(self):
      self.ui.CurrentSegmenationLabel.setText('Current segment : {}'.format(self.segment_name))

    def loadPatient(self):
      timer_index = 0
      self.timers = []
      for label in self.config_yaml["labels"]:
          self.timers.append(Timer(number = timer_index))
          timer_index = timer_index + 1

      # reset dropbox to index 0
      self.ui.dropDownButton_label_select.setCurrentIndex(0)

      # timer reset if we come back to same case
      self.called = False

      slicer.mrmlScene.Clear()
      slicer.util.loadVolume(self.currentCasePath)
      self.VolumeNode = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')[0]
      self.updateCaseAll()
      self.ui.CurrentSegmenationLabel.setText('New patient loaded - No segmentation created!')
      # Adjust windowing (no need to use self. since this is used locally)
      Vol_displayNode = self.VolumeNode.GetDisplayNode()
      Vol_displayNode.AutoWindowLevelOff()
      Vol_displayNode.SetWindow(85)
      Vol_displayNode.SetLevel(45)

      # Set to red view
      slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)

      # Center image
      slicer.util.setSliceViewerLayers(background=self.VolumeNode, fit=True)

      self.newSegmentation()
      self.subjectHierarchy()

    # Getter method to get the segmentation node name    - Not sure if this is really useful here.
    @property
    def segmentationNodeName(self):
        return f'{self.currentCase}_segmentation'

    def newSegments(self):
      pass

    def onPushButton_NewMask(self):
      self.newSegments()

    def onPreviousButton(self):
      # ----- ANW Addition ----- : Reset timer when change case and uncheck all checkboxes
      self.resetTimer()
      self.uncheckAllBoxes()
      self.clearTexts()

      #Code below avoid getting in negative values.
      self.currentCase_index = max(0, self.currentCase_index-1)
      self.updateCaseAll()
      self.loadPatient()

    def onNextButton(self):
      # ----- ANW Addition ----- : Reset timer when change case and uncheck all checkboxes
      self.resetTimer()
      self.uncheckAllBoxes()
      self.clearTexts()

      # ----- ANW Modification ----- : Since index starts at 0, we need to do len(cases)-1 (instead of len(cases)+1).
      # Ex. if we have 10 cases, then len(case)=10 and index goes from 0-9,
      # so we have to take the minimum between len(self.Cases)-1 and the currentCase_index (which is incremented by 1 everytime we click the button)
      self.currentCase_index = min(len(self.Cases)-1, self.currentCase_index+1)
      self.updateCaseAll()
      self.loadPatient()


    def newSegmentation(self):
      # Create segment editor widget and node
      self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      self.segmentEditorNode = self.segmentEditorWidget.mrmlSegmentEditorNode()
      # Create segmentation node (keep it local since we add a new segmentation node)
      # Not for reference in other methods
      segmentationNode=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
      # Set segmentation node name
      segmentationNode.SetName(self.segmentationNodeName)
      # Set segmentation node to segment editor
      self.segmentEditorWidget.setSegmentationNode(segmentationNode)
      # Set master volume node to segment editor
      self.segmentEditorWidget.setSourceVolumeNode(self.VolumeNode)
      # set refenrence geometry to Volume node (important for the segmentation to be in the same space as the volume)
      segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.VolumeNode)
      self.createNewSegments()

      # restart the current timer
      self.timers[self.current_label_index] = Timer(number=self.current_label_index)
      # reset tool
      self.segmentEditorWidget.setActiveEffectByName("No editing")

    # Load all segments at once
    # TODO REMOVE THE NAME IN EACH SEGMENTS SINCE THIS IS NOT REALLY NEEDED. WOULD NEED TO MODIFY THE QC SCRIPT ALSO
    def createNewSegments(self):
        for label in self.config_yaml["labels"]:
            self.onNewLabelSegm(label["name"], label["color_r"], label["color_g"], label["color_b"], label["lower_bound_HU"], label["upper_bound_HU"])

        first_label_name = self.config_yaml["labels"][0]["name"]
        first_label_segment_name = f"{self.currentCase}_{first_label_name}"
        self.onPushButton_select_label(first_label_segment_name, self.config_yaml["labels"][0]["lower_bound_HU"], self.config_yaml["labels"][0]["upper_bound_HU"])

    def newSegment(self, segment_name=None):

      self.segment_name = f"{self.currentCase}_{segment_name}"
      srcNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      self.srcSegmentation = srcNode.GetSegmentation()

      # Below will create a new segment if there are no segments in the segmentation node, avoid overwriting existing segments
      if not self.srcSegmentation.GetSegmentIDs(): # if there are no segments in the segmentation node
        self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
        self.segmentationNode.GetSegmentation().AddEmptySegment(self.segment_name)

      # if there are segments in the segmentation node, check if the segment name is already in the segmentation node
      if any([self.segment_name in i for i in self.srcSegmentation.GetSegmentIDs()]):
            pass
      else:
            self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
            self.segmentationNode.GetSegmentation().AddEmptySegment(self.segment_name)

      return self.segment_name

    def subjectHierarchy(self):
        # Get the subject hierarchy node
        shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
        # Get scene item ID first because it is the root item:
        sceneItemID = shNode.GetSceneItemID()
        # Get the scene item ID (check if the scene item exists)
        subjectItemID = shNode.GetItemChildWithName(shNode.GetSceneItemID(), self.currentCase)
        if not subjectItemID:
            subjectItemID = shNode.CreateSubjectItem(shNode.GetSceneItemID(), self.currentCase)
        # TODO: this will need to be updated when moving to multiple studies per patient (or done in a separate script)
        # Creat a folder to include a study (if more than one study)
        # check if the folder exists and if not create it (avoid recreating a new one when reloading a mask)
        Study_name = 'Study to be updated'
        folderID = shNode.GetItemChildWithName(subjectItemID, Study_name)
        if not folderID:
            folderID = shNode.CreateFolderItem(subjectItemID, Study_name)
        # set under the subject
        shNode.SetItemParent(folderID, subjectItemID)
        # get all volume nodes
        VolumeNodes = slicer.util.getNodesByClass('vtkMRMLVolumeNode')
        VolumeNodeNames = [i.GetName() for i in VolumeNodes]
        # Get all child (itemID = CT or MR series/sequences)
        for i in VolumeNodeNames:
            itemID = shNode.GetItemChildWithName(sceneItemID, i)
            shNode.SetItemParent(itemID, folderID)
        # same thing for segmentation nodes
        SegmentationNodes = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')
        SegmentationNodeNames = [i.GetName() for i in SegmentationNodes]
        # move all segmentation nodes to the subject

        for i in SegmentationNodeNames:
            itemID = shNode.GetItemChildWithName(sceneItemID, i)
            shNode.SetItemParent(itemID, folderID)


    def onPushButton_segmeditor(self):
      slicer.util.selectModule("SegmentEditor")

    def onNewLabelSegm(self, label_name, label_color_r, label_color_g, label_color_b, label_LB_HU, label_UB_HU):
      segment_name = self.newSegment(label_name)
      self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      self.segmentationNode.UndoEnabledOn()
      Segmentation = self.segmentationNode.GetSegmentation()
      self.SegmentID = Segmentation.GetSegmentIdBySegmentName(segment_name)
      segment = Segmentation.GetSegment(self.SegmentID)
      segment.SetColor(label_color_r/255,label_color_g/255,label_color_b/255)
      self.onPushButton_select_label(segment_name, label_LB_HU, label_UB_HU)

    def onPushButton_select_label(self, segment_name, label_LB_HU, label_UB_HU):
      self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      Segmentation = self.segmentationNode.GetSegmentation()
      self.SegmentID = Segmentation.GetSegmentIdBySegmentName(segment_name)
      self.segmentEditorNode.SetSelectedSegmentID(self.SegmentID)
      self.updateCurrentSegmenationLabel()
      self.LB_HU = label_LB_HU
      self.UB_HU = label_UB_HU
      self.onPushButton_Paint()

      if (self.MostRecentPausedCasePath != self.currentCasePath and self.MostRecentPausedCasePath != ""):
        self.timers[self.current_label_index] = Timer(number=self.current_label_index) # new path, new timer

      self.timer_router()

    def onPushButton_SemiAutomaticPHE_Launch(self):
      flag_PHE_label_exists = False
      PHE_label = None
      PHE_label_index = 0
      for label in self.config_yaml["labels"]:
          if label["name"] == "PHE":
              flag_PHE_label_exists = True
              PHE_label = label
              break
          PHE_label_index = PHE_label_index + 1
      assert flag_PHE_label_exists

      PHE_segment_name = f"{self.currentCase}_PHE"
      self.onPushButton_select_label(PHE_segment_name, PHE_label["lower_bound_HU"], PHE_label["upper_bound_HU"])
      self.ui.dropDownButton_label_select.setCurrentIndex(PHE_label_index)
      toolWindow = SemiAutoPheToolThresholdWindow(self)
      toolWindow.show()

    def onPushButton_SemiAutomaticPHE_ShowResult(self):
      self.segmentationNode.GetDisplayNode().SetVisibility(True)
      self.onPushButton_Erase()
      self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(False)

    def ApplyThresholdPHE(self, inLB_HU, inUB_HU):
      self.segmentEditorWidget.setActiveEffectByName("Threshold")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("MinimumThreshold",f"{inLB_HU}")
      effect.setParameter("MaximumThreshold",f"{inUB_HU}")
      effect.self().onApply()

    def ApplySemiAutomaticThresholdAlgorithm(self):
      self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(True)

      self.segmentationNode.GetDisplayNode().SetVisibility(False)

      self.segmentEditorWidget.setActiveEffectByName("Threshold")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("MinimumThreshold",f"{self.LB_HU}")
      effect.setParameter("MaximumThreshold",f"{self.UB_HU}")
      effect.self().onApply()

      self.segmentEditorWidget.setActiveEffectByName("Scissors")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("Operation","EraseOutside")
      effect.setParameter("Shape","FreeForm")

    def ClearPHESegment(self):
      flag_PHE_label_exists = False
      PHE_label = None
      PHE_label_index = 0
      for label in self.config_yaml["labels"]:
          if label["name"] == "PHE":
              flag_PHE_label_exists = True
              PHE_label = label
              break
          PHE_label_index = PHE_label_index + 1
      assert flag_PHE_label_exists

      segm_name = f"{self.currentCase}_PHE"
      self.srcSegmentation.RemoveSegment(segm_name)
      self.onNewLabelSegm(PHE_label["name"], PHE_label["color_r"], PHE_label["color_g"], PHE_label["color_b"], PHE_label["lower_bound_HU"], PHE_label["upper_bound_HU"])

    def startTimer(self):
      with TIMER_MUTEX:
        self.counter = 0
        # Add flag to avoid counting time when user clicks on save segm button
        self.flag2 = True

        # ----- ANW Addition ----- : Code to keep track of time passed with lcdNumber on UI
        # Create a timer
        self.timer = qt.QTimer()
        self.timer.timeout.connect(self.updatelcdNumber)

        # Start the timer and update every second
        self.timer.start(100) # 1000 ms = 1 second

        # Call the updatelcdNumber function
        self.updatelcdNumber()

    def updatelcdNumber(self):
      # Get the time
      with TIMER_MUTEX:
        if self.flag2: # add flag to avoid counting time when user clicks on save segm button
                # the timer sends a signal every second (1000 ms).
            self.counter += 1  # the self.timer.timeout.connect(self.updatelcdNumber) function is called every second and updates the counter

        self.ui.lcdNumber.display(self.counter/10)


    def stopTimer(self):
      with TIMER_MUTEX:
        # If already called once (i.e when user pressed save segm button but forgot to annotator name), simply return the time
        if self.called:
            return self.total_time
        else:
            try:
                self.total_time = self.counter/10
                self.timer.stop()
                self.flag2 = False  # Flag is for the timer to stop counting
                self.called = True
                #   self.time_allocation()
                return self.total_time
            except AttributeError as e:
                print(f'!!! YOU DID NOT START THE COUNTER !!! :: {e}')
                return None

    def resetTimer(self):
      with TIMER_MUTEX:
        # making flag to false : stops the timer
        self.flag2 = False # For case after the first one the timer stops until the user clicks on the
        self.counter = 0
        self.ui.lcdNumber.display(0)

        # reset button status
        self.enableStartTimerButton()
        self.disablePauseTimerButton()
        self.ui.PauseTimerButton.setText('Pause')
        if (self.ui.PauseTimerButton.isChecked()):
            self.ui.PauseTimerButton.toggle()

        self.disableSegmentAndPaintButtons()

    def enableStartTimerButton(self):
        self.ui.StartTimerButton.setEnabled(True)
        self.ui.StartTimerButton.setStyleSheet("background-color : yellowgreen")
        if (self.ui.StartTimerButton.isChecked()):
            self.ui.StartTimerButton.toggle()

    def disablePauseTimerButton(self):
        self.ui.PauseTimerButton.setStyleSheet("background-color : silver")
        self.ui.PauseTimerButton.setEnabled(False)

    def toggleStartTimerButton(self):
      if (self.ui.SlicerDirectoryListView.count > 0):
        if self.ui.StartTimerButton.isChecked():
            self.startTimer()
            self.timer_router()

            self.ui.StartTimerButton.setEnabled(False)
            self.ui.StartTimerButton.setStyleSheet("background-color : silver")

            self.ui.PauseTimerButton.setEnabled(True)
            self.ui.PauseTimerButton.setStyleSheet("background-color : indianred")

            self.enableSegmentAndPaintButtons()
      else:
        self.ui.StartTimerButton.toggle()

    def togglePauseTimerButton(self):
      # if button is checked - Time paused
      if self.ui.PauseTimerButton.isChecked():
          # setting background color to light-blue
          self.ui.PauseTimerButton.setStyleSheet("background-color : lightblue")
          self.ui.PauseTimerButton.setText('Restart')
          self.timer.stop()
          for indiv_timer in self.timers:
              indiv_timer.stop()
          self.flag = False

          self.MostRecentPausedCasePath = self.currentCasePath

          self.disableSegmentAndPaintButtons()
          self.onPushButton_Erase()

      # if it is unchecked
      else:
          # set background color back to light-grey
          self.ui.PauseTimerButton.setStyleSheet("background-color : indianred")
          self.ui.PauseTimerButton.setText('Pause')
          self.timer.start(100)
          self.timer_router()
          self.flag = True

          self.enableSegmentAndPaintButtons()

    # for the timer Class not the LCD one
    def timer_router(self):
      self.timers[self.current_label_index].start()
      self.flag = True

      timer_index = 0
      for timer in self.timers:
          if timer_index != self.current_label_index:
              timer.stop()
          timer_index = timer_index + 1

    def checkboxChanged(self):
      self.checked_ichtype = []
      self.checked_ichloc = []
      self.checked_ems = []
      for i in self.listichtype:
          if i.isChecked():
              ichtype = i.text
              self.checked_ichtype.append(ichtype)
      for j in self.listichloc:
          if j.isChecked():
              ichloc = j.text
              self.checked_ichloc.append(ichloc)
      for k in self.listEMs :
          if k.isChecked():
              em = k.text
              self.checked_ems.append(em)
      self.checked_ichtype = ';'.join(self.checked_ichtype)
      self.checked_ichloc = ';'.join(self.checked_ichloc)
      self.checked_ems = ';'.join(self.checked_ems)
      return self.checked_ichtype, self.checked_ichloc, self.checked_ems

    def uncheckAllBoxes(self):
      self.allcheckboxes = self.listichtype + self.listichloc + self.listEMs
      for i in self.allcheckboxes:
          i.setChecked(False)

    def clearTexts(self):
      self.ui.ichtype_other.clear()
      self.ui.EM_comments.clear()


    #### SAVING FILES ####
    def createFolders(self):
      """
      Create the top output directory
      """
      self.revision_step = self.ui.RevisionStep.currentText
      if len(self.revision_step) != 0:
          self.output_dir = os.path.join(self.CurrentFolder,
                                         f'Output_{self.annotator_name}_{self.revision_step[0]}')  # only get the number
          if not os.path.exists(self.output_dir):
              os.makedirs(self.output_dir)

      else:
          msgboxtime = qt.QMessageBox()
          msgboxtime.setText(
              "Segmentation not saved : revision step is not defined!  \n Please save again with revision step!")
          msgboxtime.exec()

    def save_node_with_isfile_check_qt_msg_box(self, file_path, node):
      """
      Create folder if it does not exist and save the node to the file_path.
      If the file already exists, a qt message box will ask the user if they want to replace the file.
      """
      folder_path = os.path.dirname(file_path)
      if not os.path.exists(folder_path):
          os.makedirs(folder_path)

      if not os.path.isfile(file_path):
          slicer.util.saveNode(node, file_path)
      else:
          msg = qt.QMessageBox()
          msg.setWindowTitle('Save As')
          msg.setText(f'The file {file_path} already exists \n Do you want to replace the existing file?')
          msg.setIcon(qt.QMessageBox.Warning)
          msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
          msg.exec()
          if msg.clickedButton() == msg.button(qt.QMessageBox.Ok):
              slicer.util.saveNode(node, file_path)
              return f'File saved as {file_path}'
          else:
              return "File not saved"

    def onSaveSegmentationButton(self):
      #TODO: refactor this methods and it is way too long
      self.time = self.stopTimer()
      for timer in self.timers:
            timer.stop()
      self.annotator_name = self.ui.Annotator_name.text
      self.annotator_degree = self.ui.AnnotatorDegree.currentText
      output_file_pt_id_instanceUid = re.findall(self.VOL_REGEX_PATTERN_PT_ID_INSTUID_SAVE,os.path.basename(self.currentCasePath))[0]


      #### CHECKBOX SAVING - TO BE REFACTORED ####
      # get ICH types and locations
      self.checked_ichtype, self.checked_icvhloc, self.checked_ems = self.checkboxChanged()
      self.ichtype_other = self.ui.ichtype_other.text
      self.em_comments = self.ui.EM_comments.text

      # Create folders if not exist
      self.createFolders()

      # Run the code to remove outliers
      print('*** Running outlier removal ***')
      self.check_for_outlier_labels()

      # Get the segmentation node (the current one)
      self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]

      #### SAVING CSV TIME #####
      # Save if annotator_name is not empty and timer started:
      if self.annotator_name and self.time is not None:
          # Save time to csv
          print("Saving time to csv")
          tag_str = "Case number, Annotator Name, Annotator degree, Revision step, Time"
          for label in self.config_yaml["labels"]:
                tag_str = tag_str + ", " + label["name"] + " time"
          if self.flag_ICH_in_labels:
                tag_str = tag_str + ", ICH type, ICH location, Expansion markers, Other ICH type, Other expansion markers"
          print('constructing data string')
          # TODO: refactor this to be more generic and use the config file values.
          data_str = self.currentCase
          data_str = data_str + ", " + self.annotator_name
          data_str = data_str + ", " + self.annotator_degree
          data_str = data_str + ", " + self.revision_step[0]
          data_str = data_str + ", " + str(self.ui.lcdNumber.value)
          for timer in self.timers:
                data_str = data_str + ", " + str(timer.total_time)
          if self.flag_ICH_in_labels:
                data_str = data_str + ", " + self.checked_ichtype
                data_str = data_str + ", " + self.checked_ichloc
                data_str = data_str + ", " + self.checked_ems
                data_str = data_str + ", " + self.ichtype_other
                data_str = data_str + ", " + self.em_comments

          self.outputTimeFile = os.path.join(self.output_dir, 'annotation times',
                                             '{}_Case_{}_time_{}.csv'.format(self.annotator_name, output_file_pt_id_instanceUid, self.revision_step[0]))
          print(f'line 961 - outputTimeFile: {self.outputTimeFile}')
          time_folder = os.path.dirname(self.outputTimeFile)

          if not os.path.exists(time_folder):
              print("Creating directory: ", time_folder)
              os.makedirs(time_folder)

          if not os.path.isfile(self.outputTimeFile):
              with open(self.outputTimeFile, 'w') as f:
                  f.write(tag_str)
                  f.write("\n")
                  f.write(data_str)
          else:
              with open(self.outputTimeFile, 'a') as f:
                  f.write("\n")
                  f.write(data_str)


          ### SAVING SEGMENTATION FILES ####

          self.outputSegmFile = os.path.join(self.output_dir,'segmentations',
                                                 "{}_{}_{}.seg.nrrd".format(output_file_pt_id_instanceUid, self.annotator_name, self.revision_step[0]))
          print(f'line 980 - outputTimeFile: {self.outputTimeFile}')
          print(f'Saving segmentation to {self.outputSegmFile}')

          # get the directory of the output segmentation file (needed in the method to check for remaining labels)
          self.output_seg_dir = os.path.dirname(self.outputSegmFile)
          print(f'output_seg_dir: {self.output_seg_dir}')
          if not self.output_seg_dir:
              os.makedirs(self.output_seg_dir)

          self.save_node_with_isfile_check_qt_msg_box(self.outputSegmFile, self.segmentationNode)

          # reloading the .seg.nrrd file and check if the label name : value match
          self.check_match_label_name_value()

      # If annotator_name empty or timer not started.
      else:
          if not self.annotator_name:
              msgboxtime = qt.QMessageBox()
              msgboxtime.setText("Segmentation not saved : no annotator name !  \n Please save again with your name!")
              msgboxtime.exec()
          elif self.time is None:
              msgboxtime2 = qt.QMessageBox()
              msgboxtime2.setText("Error: timer is not started for some unknown reason. Restart and save again. File not saved!")
              msgboxtime2.exec()


      # Save volumes
      self.save_statistics()
      # Update the color of the segment
      self.update_current_case_paths_by_segmented_volumes()



    def msg2_clicked(self, msg2_button):
      if msg2_button.text == 'OK':
          slicer.util.saveNode(self.segmentationNode, self.outputSegmFile)
      else:
          return

    def msg3_clicked(self, msg3_button):
      if msg3_button.text == 'OK':
          slicer.util.saveNode(self.labelmapVolumeNode, self.outputSegmFileNifti)
      else:
          return

    def msg4_clicked(self, msg4_button):
      if msg4_button.text == 'OK':
          slicer.util.saveNode(self.VolumeNode, self.outputVolfile)
      else:
          return

    def onBrowseFolders_2Button(self):
      self.predictionFolder= qt.QFileDialog.getExistingDirectory(None,"Open a folder", self.DEFAULT_SEGMENTATION_DIR, qt.QFileDialog.ShowDirsOnly)

      self.predictions_paths = sorted(glob(os.path.join(self.predictionFolder, f'{self.SEGM_FILE_TYPE}')))


    def msg_warnig_delete_segm_node_clicked(self):
      if slicer.util.getNodesByClass('vtkMRMLSegmentationNode'):
        slicer.mrmlScene.RemoveNode(slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0])


    def load_mask_v2(self):
      # Get list of prediction names
      msg_warning_delete_segm_node =qt.QMessageBox() # Typo correction
      msg_warning_delete_segm_node.setText('This will delete the current segmentation. Do you want to continue?')
      msg_warning_delete_segm_node.setIcon(qt.QMessageBox.Warning)
      msg_warning_delete_segm_node.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
      # if clikc ok, then delete the current segmentatio
      msg_warning_delete_segm_node.setDefaultButton(qt.QMessageBox.Cancel)
      response = msg_warning_delete_segm_node.exec() # calls remove node if ok is clicked
      if response == qt.QMessageBox.Ok:
          self.msg_warnig_delete_segm_node_clicked()

      else:
          return

      try:
            self.predictions_names = sorted([re.findall(self.SEGM_REGEX_PATTERN,os.path.split(i)[-1]) for i in self.predictions_paths])
            self.called = False # restart timer
      except AttributeError as e:
            msgnopredloaded=qt.QMessageBox() # Typo correction
            msgnopredloaded.setText('Please select the prediction directory!')
            msgnopredloaded.exec()
            # Then load the browse folder thing for the user
            self.onBrowseFolders_2Button()

      self.currentPredictionPath = ""
      for p in self.predictions_paths:
          if self.currentCase in p:
              self.currentPredictionPath = p
              break

      if self.currentPredictionPath != "":
          # Then load the prediction segmentation
          slicer.util.loadSegmentation(self.currentPredictionPath)
          self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
          self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
          self.segmentEditorNode =  self.segmentEditorWidget.mrmlSegmentEditorNode()
          self.segmentEditorWidget.setSegmentationNode(self.segmentationNode)
          self.segmentEditorWidget.setSourceVolumeNode(self.VolumeNode)
          # set refenrence geometry to Volume node
          self.segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.VolumeNode)
          nn = self.segmentationNode.GetDisplayNode()
          # set Segmentation visible:
          nn.SetAllSegmentsVisibility(True)
          self.segmentationNode.GetDisplayNode().SetOpacity2DFill(0)

          self.convert_nifti_header_segment()

          #### ADD SEGMENTS THAT ARE NOT IN THE SEGMENTATION ####

      else:
          msg_no_such_case = qt.QMessageBox()
          msg_no_such_case.setText('There are no mask for this case in the directory that you chose!')
          msg_no_such_case.exec()

      # update subject hierarchy
      self.subjectHierarchy()


    def convert_nifti_header_segment(self):

        # Check if the first segment starts with Segment_1 (e.g. loaded from nnunet).
        # If so change the name and colors of the segments to match the ones in the config file
        first_segment_name = self.segmentationNode.GetSegmentation().GetNthSegment(0).GetName()
        print(f'first_segment_name :: {first_segment_name}')
        if first_segment_name.startswith("Segment_"):
            # iterate through all segments and rename them

            for i in range(self.segmentationNode.GetSegmentation().GetNumberOfSegments()):
                segment_name = self.segmentationNode.GetSegmentation().GetNthSegment(i).GetName()
                print(f' src segment_name :: {segment_name}')
                for label in self.config_yaml["labels"]:
                    if label["value"] == int(segment_name.split("_")[-1]):
                        self.segmentationNode.GetSegmentation().GetNthSegment(i).SetName(label['name'])
                        # set color
                        self.segmentationNode.GetSegmentation().GetNthSegment(i).SetColor(label["color_r"] / 255,
                                                                                          label["color_g"] / 255,
                                                                                          label["color_b"] / 255)

        self.add_missing_nifti_segment()

    def add_missing_nifti_segment(self):
        for label in self.config_yaml['labels']:
            name = label['name']
            segment_names = [self.segmentationNode.GetSegmentation().GetNthSegment(node).GetName() for node in
                             range(self.segmentationNode.GetSegmentation().GetNumberOfSegments())]
            if not name in segment_names:
                self.segmentationNode.GetSegmentation().AddEmptySegment(name)
                segmentid = self.segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(name)
                segment = self.segmentationNode.GetSegmentation().GetSegment(segmentid)
                segment.SetColor(label["color_r"] / 255,
                                 label["color_g"] / 255,
                                 label["color_b"] / 255)


    def update_current_case_paths_by_segmented_volumes(self):
        print(self.output_seg_dir)
        segmentations = glob(os.path.join(self.output_seg_dir, '*.seg.nrrd'))
        print(len(segmentations))
        print(self.SEGM_REGEX_PATTERN)
        print(os.path.basename(segmentations[0]))
        segmented_IDs = [re.findall(self.SEGM_REGEX_PATTERN, os.path.basename(segmentation))[0] for segmentation in
                       segmentations]

        self.ui.SlicerDirectoryListView.clear()
        for case in self.CasesPaths:
          case_id = re.findall(self.VOL_REGEX_PATTERN, case)[0]
          item = qt.QListWidgetItem(case_id)
          if not case_id in segmented_IDs:
              item.setForeground(qt.QColor('red'))

          elif case_id in segmented_IDs:
              item.setForeground(qt.QColor('green'))
          self.ui.SlicerDirectoryListView.addItem(item)

    def onpushbuttonttest2(self):
      pass

    def onSegmentEditorPushButton(self):

      if self.ui.SegmentWindowPushButton.isChecked():
          self.ui.SegmentWindowPushButton.setStyleSheet("background-color : gray")
          self.ui.SegmentWindowPushButton.setText('Undock Segment Editor')
          slicer.modules.segmenteditor.widgetRepresentation().setParent(None)
          slicer.modules.segmenteditor.widgetRepresentation().show()

      # if it is unchecked (default)
      else:
          self.ui.SegmentWindowPushButton.setStyleSheet("background-color : lightgray")
          self.ui.SegmentWindowPushButton.setText('Dock Segment Editor')
          slicer.modules.segmenteditor.widgetRepresentation().setParent(slicer.util.mainWindow())

    def onPushDefaultMin(self):
      with open(CONFIG_FILE_PATH, 'r') as file:
        fresh_config = yaml.safe_load(file)
        self.config_yaml["labels"][self.current_label_index]["lower_bound_HU"] = fresh_config["labels"][self.current_label_index]["lower_bound_HU"]
        self.setUpperAndLowerBoundHU(self.config_yaml["labels"][self.current_label_index]["lower_bound_HU"], self.config_yaml["labels"][self.current_label_index]["upper_bound_HU"])

    def onPushDefaultMax(self):
      with open(CONFIG_FILE_PATH, 'r') as file:
        fresh_config = yaml.safe_load(file)
        self.config_yaml["labels"][self.current_label_index]["upper_bound_HU"] = fresh_config["labels"][self.current_label_index]["upper_bound_HU"]
        self.setUpperAndLowerBoundHU(self.config_yaml["labels"][self.current_label_index]["lower_bound_HU"], self.config_yaml["labels"][self.current_label_index]["upper_bound_HU"])

    def onPushButton_undo(self):
      self.segmentEditorWidget.undo()

    def onDropDownButton_label_select(self, value):
      self.current_label_index = value
      label = self.config_yaml["labels"][value]
      self.setUpperAndLowerBoundHU(label["lower_bound_HU"], label["upper_bound_HU"])

      label_name = label["name"]
      try:
        segment_name = f"{self.currentCase}_{label_name}"
        self.onPushButton_select_label(segment_name, label["lower_bound_HU"], label["upper_bound_HU"])
      except:
        pass

    def onPushButton_Paint(self):
        self.segmentEditorWidget.setActiveEffectByName("Paint")
        # Note it seems that sometimes you need to activate the effect first with :
        # Assign effect to the segmentEditorWidget using the active effect
        self.effect = self.segmentEditorWidget.activeEffect()
        self.effect.activate()
        self.effect.setParameter('BrushSphere',1)
        # Seems that you need to activate the effect to see it in Slicer
        # Set up the mask parameters (note that PaintAllowed...was changed to EditAllowed)
        self.segmentEditorNode.SetMaskMode(slicer.vtkMRMLSegmentationNode.EditAllowedEverywhere)
        #Set if using Editable intensity range (the range is defined below using object.setParameter)
        self.segmentEditorNode.SetMasterVolumeIntensityMask(True)
        self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(self.LB_HU, self.UB_HU)
        self.segmentEditorNode.SetOverwriteMode(slicer.vtkMRMLSegmentEditorNode.OverwriteAllSegments)


    def keyboard_toggle_fill(self):
      print('keyboard_toggle_fill')
      if self.ui.pushButton_ToggleFill.isChecked():
          self.ui.pushButton_ToggleFill.toggle()
          self.toggleFillButton()
      else:
          self.ui.pushButton_ToggleFill.toggle()
          self.toggleFillButton()


    def toggleFillButton(self):
      if  self.ui.pushButton_ToggleFill.isChecked():
          self.ui.pushButton_ToggleFill.setStyleSheet("background-color : lightgreen")
          self.ui.pushButton_ToggleFill.setText('Fill: ON')
          self.segmentationNode.GetDisplayNode().SetOpacity2DFill(100)
      else:
          self.ui.pushButton_ToggleFill.setStyleSheet("background-color : indianred")
          self.ui.pushButton_ToggleFill.setText('Fill: OFF')
          self.segmentationNode.GetDisplayNode().SetOpacity2DFill(0)

    def onPushButton_ToggleVisibility(self):
      if self.ui.pushButton_ToggleVisibility.isChecked():
          self.ui.pushButton_ToggleVisibility.setStyleSheet("background-color : indianred")
          self.ui.pushButton_ToggleVisibility.setText('Visibility: OFF')
          self.segmentationNode.GetDisplayNode().SetAllSegmentsVisibility(False)
      else:
          self.ui.pushButton_ToggleVisibility.setStyleSheet("background-color : lightgreen")
          self.ui.pushButton_ToggleVisibility.setText('Visibility: ON')
          self.segmentationNode.GetDisplayNode().SetAllSegmentsVisibility(True)

    def togglePaintMask(self):
        if self.ui.pushButton_TogglePaintMask.isChecked():
            self.ui.pushButton_TogglePaintMask.setStyleSheet("background-color : lightgreen")
            self.ui.pushButton_TogglePaintMask.setText('Paint Mask ON')
            self.segmentEditorNode.SetMaskMode(slicer.vtkMRMLSegmentationNode.EditAllowedEverywhere)


    def onPushButton_segmeditor(self):
      slicer.util.selectModule("SegmentEditor")

    def onPushButton_Erase(self):
      self.segmentEditorWidget.setActiveEffectByName("Erase")
      # Note it seems that sometimes you need to activate the effect first with :
      # Assign effect to the segmentEditorWidget using the active effect
      self.effect = self.segmentEditorWidget.activeEffect()
      # Seems that you need to activate the effect to see it in Slicer
      self.effect.activate()
      self.segmentEditorNode.SetMasterVolumeIntensityMask(False)

    def onPushButton_Smooth(self):
      # pass
      # Remove masking
      self.segmentEditorNode.SetMasterVolumeIntensityMask(False)
      # Smoothing
      self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      self.segmentEditorWidget.setActiveEffectByName("Smoothing")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("SmoothingMethod", "MEDIAN")
      effect.setParameter("KernelSizeMm", 3)
      effect.self().onApply()



    def onPushButton_Small_holes(self):
      # pass
      # Remove masking
      self.segmentEditorNode.SetMasterVolumeIntensityMask(False)
      # Fill holes smoothing
      self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      self.segmentEditorWidget.setActiveEffectByName("Smoothing")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("SmoothingMethod", "MORPHOLOGICAL_CLOSING")
      effect.setParameter("KernelSizeMm", 3)
      effect.self().onApply()

    def onLB_HU(self):
      try:
        self.LB_HU=self.ui.LB_HU.value
        self.segmentEditorNode.SetMasterVolumeIntensityMask(True)
        self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(self.LB_HU, self.UB_HU)
        self.config_yaml["labels"][self.current_label_index]["lower_bound_HU"] = self.LB_HU
      except:
        pass

    def onUB_HU(self):
      try:
        self.UB_HU=self.ui.UB_HU.value
        self.segmentEditorNode.SetMasterVolumeIntensityMask(True)
        self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(self.LB_HU, self.UB_HU)
        self.config_yaml["labels"][self.current_label_index]["upper_bound_HU"] = self.UB_HU
      except:
        pass

    def check_match_label_name_value(self):
      #TODO: refactor this method using the qc script
      """"
      Check match between lable name and values
      # seg.nrrd file = outputSegmFile
      # seg nifti file = outputSegmFileNifti
      # volume nifti file = outputVolfile
      #
      """
      # get the current label name
      # read with slicerio
      print('-'*20)
      print(f'self.currentCase::{self.currentCase}')
      print(f'self.outputSegmFile ::{self.outputSegmFile}')
      segmentation_info = slicerio.read_segmentation(self.outputSegmFile)
      print('-' * 20)
      print('Segmentation info :')
      print(segmentation_info)

      # get the segment names
      segment_names = slicerio.segment_names(segmentation_info)
      print('-'*20)
      print('segment names:')
      print(segment_names)

      print('-' * 20)
      print(f'lenght of segment names {len(segment_names)}')
      if len(segment_names) != len(self.config_yaml['labels']):
          raise ValueError('Number of segments not equal to number of labels in the config file')


      for i in segment_names:
          if self.currentCase not in i:
              raise ValueError(f'Case IC not found in segmentation segment name {i}')
          else:
              if 'ich' in i.lower():
                  ich_name = i
              elif 'ivh' in i.lower():
                  ivh_name = i
              elif 'phe' in i.lower():
                  phe_name = i
              else:
                  raise ValueError('Segment name not recognized')

      # #TODO: put in the config file
      segment_names_to_labels = [(ich_name, 1), (ivh_name, 2), (phe_name, 3)]
      voxels, header = nrrd.read(self.outputSegmFile)
      # I think this function corrects the segment names and labels
      extracted_voxels, extracted_header = slicerio.extract_segments(voxels, header, segmentation_info,
                                                                     segment_names_to_labels)
      # Below could be refactored to a function that take an arbitrary number of segment names and labels (e.g. generic qc script)


      # Overwrite the nrrd file
      print(f'Writing a copy of the slicerio corrected segmentation file  {self.outputSegmFile} with the corrected labels and names')
      output_file_pt_id_instanceUid = re.findall(self.VOL_REGEX_PATTERN_PT_ID_INSTUID_SAVE,os.path.basename(self.currentCasePath))[0]
      output_dir_segmentation_file_corrected = os.path.join(self.DEFAULT_VOLUME_DIR, 'Segmentation_file_corrected_slicerio')
      if not os.path.isdir(output_dir_segmentation_file_corrected):
          os.makedirs(output_dir_segmentation_file_corrected)
      output_path = os.path.join(output_dir_segmentation_file_corrected, f'Slicerio_corrected_segmentation_{output_file_pt_id_instanceUid}.seg.nrrd')

      try:
          print('-' * 20)
          print('*' * 20)
          print('Segment0')
          print(extracted_header['Segment0_LabelValue'])
          print(extracted_header['Segment0_Name'])
          print('*' * 20)
          print('Segment1')
          print(extracted_header['Segment1_LabelValue'])
          print(extracted_header['Segment1_Name'])
          print('*' * 20)
          print('Segment2')
          print(extracted_header['Segment2_LabelValue'])
          print(extracted_header['Segment2_Name'])

          assert extracted_header['Segment0_LabelValue'] == 1
          assert extracted_header['Segment0_Name'] == ich_name
          assert extracted_header['Segment1_LabelValue'] == 2
          assert extracted_header['Segment1_Name'] == ivh_name
          assert extracted_header['Segment2_LabelValue'] == 3
          assert extracted_header['Segment2_Name'] == phe_name
          print('-' * 20)
          nrrd.write(output_path, extracted_voxels, extracted_header)
          print(f'PASSED: Match segmentation labels and names for case {self.currentCase}')



      except AssertionError as e:  # TODO : check for segment index also
          # # Correct segmentation labels and names. Not that this requires pynnrd directly.
          print('Correcting segmentation labels and names for case {}'.format(self.currentCase))
          print(e)
          print('Segmentation name {} to label value {}'.format(extracted_header['Segment0_Name'], extracted_header['Segment0_LabelValue']))
          header['Segment0_LabelValue'] = 1
          header['Segment0_Name'] = ich_name
          print('Segmentation name {} to label value {}'.format(extracted_header['Segment1_Name'], extracted_header['Segment1_LabelValue']))
          header['Segment1_LabelValue'] = 2
          header['Segment1_Name'] = ivh_name
          print('Segmentation name {} to label value {}'.format(extracted_header['Segment2_Name'], extracted_header['Segment2_LabelValue']))
          header['Segment2_LabelValue'] = 3
          header['Segment2_Name'] = phe_name
          nrrd.write(output_path, extracted_voxels, extracted_header)
          print(f'Corrected: changed the  segmentation labels and names matches for case {ID}')


    def check_for_outlier_labels(self):
      # Create a label map from the segmentation
      # Get the volume node and segmentation node
      volumeNode = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')[0]
      segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.VolumeNode)

      volumeArray = slicer.util.arrayFromVolume(self.VolumeNode)

      # Loop through each segment
      segmentIDs = segmentationNode.GetSegmentation().GetSegmentIDs()
      for segmentID in segmentIDs:
          # Export the current segment to a new labelmap
          labelMapVolumeNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
          slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(segmentationNode, [segmentID],
                                                                            labelMapVolumeNode, self.VolumeNode)
          labelArray = slicer.util.arrayFromVolume(labelMapVolumeNode)
          print(segmentID)
          # Check and correct the values
          array_range = labelArray[(volumeArray < self.OUTLIER_THRESHOLD_LB) | (volumeArray > self.OUTLIER_THRESHOLD_UB)]
          if array_range.any():
              print('Voxels to correct')
              labelArray[(volumeArray < self.OUTLIER_THRESHOLD_LB) | (volumeArray > self.OUTLIER_THRESHOLD_UB)] = 0
              slicer.util.updateVolumeFromArray(labelMapVolumeNode, labelArray)

              # Clear the original segment
              segmentationNode.GetSegmentation().RemoveSegment(segmentID)

              # Import the corrected labelmap back to this segment
              slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelMapVolumeNode,
                                                                                    segmentationNode)
          else:
              print('No correction needed')
          # Cleanup this temporary node
          slicer.mrmlScene.RemoveNode(labelMapVolumeNode.GetDisplayNode().GetColorNode())
          slicer.mrmlScene.RemoveNode(labelMapVolumeNode)
          # Make sure the segmentation node matches the reference volume geometry
          self.segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.VolumeNode)

    def save_statistics(self):
      volumeNode=slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')[0]
      segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(volumeNode)
      segStatLogic = SegmentStatistics.SegmentStatisticsLogic()
      segStatLogic.getParameterNode().SetParameter("Segmentation", segmentationNode.GetID())
      segStatLogic.getParameterNode().SetParameter("ScalarVolume", volumeNode.GetID())
      segStatLogic.getParameterNode().SetParameter("LabelSegmentStatisticsPlugin.obb_origin_ras.enabled",str(True))
      segStatLogic.getParameterNode().SetParameter("LabelSegmentStatisticsPlugin.obb_diameter_mm.enables",str(True))
      segStatLogic.getParameterNode().SetParameter("LabelSegmentStatisticsPlugin.obb_direction_ras_x_.enabled", str(True))
      segStatLogic.getParameterNode().SetParameter("LabelSegmentStatisticsPlugin.obb_direction_ras_y_.enabled",str(True))
      segStatLogic.getParameterNode().SetParameter("LabelSegmentStatisticsPlugin.obb_direction_ras_z_.enabled", str(True))
      segStatLogic.getParameterNode().SetParameter("LabelSegmentStatisticsPLugin.obb_diameter_mm.enables", str(True))
      segStatLogic.computeStatistics()
      output_file_pt_id_instanceUid = re.findall(self.VOL_REGEX_PATTERN_PT_ID_INSTUID_SAVE, os.path.basename(self.currentCasePath))[0]

      outputFilename = 'Volumes_{}_{}_{}.{}'.format(output_file_pt_id_instanceUid, self.annotator_name, self.revision_step[0], 'csv')
      print('segment statistics output file name: ', outputFilename)
      output_dir_volumes_csv = os.path.join(self.output_dir, 'csv_volumes')
      if not os.path.exists(output_dir_volumes_csv):
          os.makedirs(output_dir_volumes_csv)
      outputFilename = os.path.join(output_dir_volumes_csv, outputFilename)
      if not os.path.isfile(outputFilename):
          segStatLogic.exportToCSVFile(outputFilename)
          print(f'Wrote segmentation file here {outputFilename}')
      else:
          msg = qt.QMessageBox()
          msg.setWindowTitle('Save As')
          msg.setText(f'The file {outputFilename} already exists \n Do you want to replace the existing file?')
          msg.setIcon(qt.QMessageBox.Warning)
          msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
          msg.exec()
          if msg.clickedButton() == msg.button(qt.QMessageBox.Ok):
              segStatLogic.exportToCSVFile(outputFilename)
              print(f'Wrote segmentation file here {outputFilename}')


      segStatLogic.exportToCSVFile(outputFilename)
      stats = segStatLogic.getStatistics()

      # Read the csv and clean it up
      df = pd.read_csv(outputFilename)
      df.set_index('Segment')
      df = df[['Segment', 'LabelmapSegmentStatisticsPlugin.volume_cm3']]
      df.rename(columns={'LabelmapSegmentStatisticsPlugin.volume_cm3': "Volumes"}, inplace=True)
      df['ID'] = df['Segment'].str.extract("(ID_[a-zA-Z0-90]+)_")
      df['Category'] = df['Segment'].str.extract("_([A-Z]+)$")
      df.to_csv(outputFilename, index=False)

    def get_line_measure(self):
      annotator_name = self.ui.Annotator_name.text
      revision_step = self.ui.RevisionStep.currentIndex
      markupsLogic = slicer.modules.markups.logic()
      if markupsLogic:
          print(f'Found markupsLogic')
          lineNode = slicer.util.getNodesByClass("vtkMRMLMarkupsLineNode")[1]
          length = lineNode.GetLineLengthWorld()
          print(f'Length of line: {length}')
          #save to csv specific for line measurement
          output_dir = os.path.join(self.output_dir,
                                             f'Output_line_measure_{annotator_name}_{revision_step}')  # only get the number
          if not os.path.exists(output_dir):
              os.makedirs(output_dir)

          output_file_pt_id_instanceUid = re.findall(self.VOL_REGEX_PATTERN_PT_ID_INSTUID_SAVE, os.path.basename(self.currentCasePath))[0]
          outputFilename = 'Line_measure_{}_{}_{}.{}'.format(output_file_pt_id_instanceUid, annotator_name, revision_step, 'csv')
          outputFilename = os.path.join(output_dir, outputFilename)
          df = pd.DataFrame({'id': output_file_pt_id_instanceUid, 'annotator':annotator_name, 'revision_step':revision_step, 'length': [length]})
          df.to_csv(outputFilename, index=False)

          # Save a screenshot of the line measurement
          # screenshot = qt.QPixmap.grabWidget(slicer.util.mainWindow())
          # screenshot.save()

          view = slicer.app.layoutManager().sliceWidget('Red').sliceView()
          cap = ScreenCapture.ScreenCaptureLogic()
          output_screen_capture_filename = os.path.join(output_dir, f'line_measure_{output_file_pt_id_instanceUid}_{annotator_name}_{revision_step}.png')
          cap.captureImageFromView(view, output_screen_capture_filename)
      else:
          msg = qt.QMessageBox()
          msg.setWindowTitle('Warning')
          msg.setText('No line measurement found!')
          msg.exec()

    def get_screenshot(self):
        view = slicer.app.layoutManager().sliceWidget('Red').sliceView()
        cap = ScreenCapture.ScreenCaptureLogic()
        output_screen_capture_filename = os.path.join(self.output_dir, f'screenshot_{self.currentCase}.png')
        cap.captureImageFromView(view, output_screen_capture_filename)
        comments = self.ui.textEdit_screenshot.toPlainText()
        output_dir = os.path.joint(self.output_dir, 'screenshots')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(os.path.join(self.output_dir, f'screenshot_comments_{self.currentCase}.txt'), 'w') as f:
            f.write(comments)








class SEGMENTER_V2Logic(ScriptedLoadableModuleLogic):
    pass

class SEGMENTER_V2Test(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear()

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_SEGMENTER_V21()

  def test_SEGMENTER_V21(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")

    # Get/create input data

    pass
