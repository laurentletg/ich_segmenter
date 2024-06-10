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

import pandas as pd
import numpy as np

import nrrd
import nibabel as nib


# MB - Required for sct integration and more comprehensive processing
import sys
import subprocess
import csv
import argparse
import copy
import vtk
from functools import partial
import random
# from render_manager import RenderManager
# from PyQt5.QtWidgets import QApplication, QMainWindow

# TODO: add all constants to the config file
CONFIG_FILE_PATH = os.path.join(Path(__file__).parent.resolve(), "config.yaml")

TIMER_MUTEX = RLock()

class SEGMENTER_V2(ScriptedLoadableModule):
    ###
    #
    # Uses ScriptedLoadableModule base class, available at:
    # https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    #
    ###

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "SEGMENTER_V2"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Delphine Pilon, An Ni Wu, Maxime Bouthillier, "
                                "Emmanuel Montagnon, Laurent Letourneau-Guillon"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
            This is an example of scripted loadable module bundled in an extension.
            See more information in 
            <a href="https://github.com/organization/projectname#SEGMENTER_V2">module documentation</a>.
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

    # mb adding for mouse customized at startup
    # Get the interactor from the 'Yellow' slice view
    self.interactor1 = slicer.app.layoutManager().sliceWidget(
        'Yellow').sliceView().interactor()
    self.interactor2 = slicer.app.layoutManager().sliceWidget(
        'Red').sliceView().interactor()

    # # Apply the custom interactor style
    styleYellow = slicer.app.layoutManager().sliceWidget('Yellow')
    self.styleYellow = CustomInteractorStyle(sliceWidget=styleYellow)
    self.interactor1.SetInteractorStyle(self.styleYellow)

    styleRed = slicer.app.layoutManager().sliceWidget('Red')
    self.styleRed = CustomInteractorStyle(sliceWidget=styleRed)
    self.interactor2.SetInteractorStyle(self.styleRed)



    # # mb adding for mouse customized at startup
    # # Get the interactor from the 'Yellow' slice view
    # self.interactor = slicer.app.layoutManager().sliceWidget(
    #     'Yellow').sliceView().interactor()
    # # self.interactor = slicer.app.layoutManager().sliceWidget(
    # #     'Red').sliceView().interactor()
    #
    # # # Apply the custom interactor style
    # self.style = CustomInteractorStyle()
    # self.interactor.SetInteractorStyle(self.style)




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
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/SEGMENTER_V4.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = SEGMENTER_V2Logic()
    self.get_config_values()
    
    self.DefaultDir = self.config_yaml['default_volume_directory']
    self.DEFAULT_SEGMENTATION_DIR = self.config_yaml['default_segmentation_directory']
    print(f'Default directory location: {self.DEFAULT_SEGMENTATION_DIR}')

    #maxime
    self.OUTPUT_DIR = self.config_yaml['output_directory']
    self.EXTENSION_DIR = self.config_yaml['extension_directory']
    self.GT_DIR = self.config_yaml['GTReferences_folder']

    #for ui case list
    # self.yamlListeOfCasesFlag = False
    self.yamlListName = []
    self.yamlListPath = []
    self.lenDirectoryCases = 0
    self.countAssess = 1
    self.indexYaml = -1

    #assessment of segmentation
    self.assessOrigDict = {}
    self.assessModifDict = {}

    self.VOLUME_FILE_TYPE = self.config_yaml['volume_extension']
    self.SEGM_FILE_TYPE = self.config_yaml['segmentation_extension']
    self.VOL_REGEX_PATTERN = self.config_yaml['regex_format_volume_load']
    self.VOL_REGEX_PATTERN_PT_ID_INSTUID_SAVE = self.config_yaml['regex_format_volume_save']
    self.SEGM_REGEX_PATTERN = self.config_yaml['regex_format_segmentation_load']
    # self.OUTLIER_THRESHOLD_LB = self.config_yaml['OUTLIER_THRESHOLD']['LOWER_BOUND']
    # self.OUTLIER_THRESHOLD_UB = self.config_yaml['OUTLIER_THRESHOLD']['UPPER_BOUND']

    ###maxime adding
    self.CONTRAST = self.config_yaml['contrast']
    self.FOLDER_FORMAT = self.config_yaml['folder_organization']
    # slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutSideBySideView)
    # Displays the selected color view at module startup
    if self.config_yaml['slice_view_color'] == "Yellow":
        slicer.app.layoutManager().setLayout(
            slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpYellowSliceView)
    if self.config_yaml['slice_view_color'] == "Red":
        slicer.app.layoutManager().setLayout(
            slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
    self.file_extension = self.config_yaml['volume_extension']

    # self.LB_HU = self.config_yaml["labels"][0]["lower_bound_HU"]
    # self.UB_HU = self.config_yaml["labels"][0]["upper_bound_HU"]
    
  
    self.ui.PauseTimerButton.setText('Pause')
    self.ui.pushButton_uint8casting.connect('clicked(bool)', self.onPushButton_uint8casting)
    self.ui.getDefaultDir.connect('clicked(bool)', self.getDefaultDir)
    self.ui.BrowseFolders.connect('clicked(bool)', self.onBrowseFoldersButton)
    self.ui.SlicerDirectoryListView.clicked.connect(self.getCurrentTableItem)
    self.ui.SaveSegmentationButton.connect('clicked(bool)', self.onSaveSegmentationButton)
    self.ui.BrowseFolders_2.connect('clicked(bool)', self.onBrowseFolders_2Button)
    #maxime
    # self.ui.SelecOutputFolder('clicked(bool)', self.SelecOutputFolder)
    self.ui.SelectOutputFolder.connect('clicked(bool)', self.onSelectOutputFolder)
    self.ui.createSegmentationButton.connect('clicked(bool)', self.onCreateSegmentationButton)
    self.ui.toggleSegmentationVersions.connect('clicked(bool)', self.onToggleSegmentationVersions)
    self.ui.assessSegmentationButton.connect('clicked(bool)', self.onAssessSegmentationButton)
    self.ui.getResultButton.connect('clicked(bool)', self.onGetResult)
    self.ui.selectGTReferences.connect('clicked(bool)', self.selectGTReferences)
    self.ui.toggleInterpolation.connect('clicked(bool)', self.onToggleInterpolation)

    #maxime navigation event
    # Track if segmentation is modified
    # Track if segmentation is modified
    self.segmentationModified = False
    self.observer_tags = {}
    # self.get_current_segment_id()
    self.loadMask = False
    self.itemClicked = False
    self.toggleSegmentation = False
    self.interpolation = self.config_yaml["interpolation"]

    # Connect segmentation modified event
    # self.observeSegmentationNode()



    self.ui.LoadPrediction.connect('clicked(bool)', self.load_mask_v2)
    self.ui.Previous.connect('clicked(bool)', self.onPreviousButton)
    self.ui.Next.connect('clicked(bool)', self.onNextButton)
    self.ui.pushButton_Paint.connect('clicked(bool)', self.onPushButton_Paint)
    self.ui.pushButton_ToggleVisibility.connect('clicked(bool)', self.onPushButton_ToggleVisibility)
    self.ui.PushButton_segmeditor.connect('clicked(bool)', self.onPushButton_segmeditor)  
    self.ui.pushButton_Erase.connect('clicked(bool)', self.onPushButton_Erase)  
    self.ui.pushButton_Smooth.connect('clicked(bool)', self.onPushButton_Smooth)  
    self.ui.pushButton_Small_holes.connect('clicked(bool)', self.onPushButton_Small_holes)  
    # self.ui.pushButton_SemiAutomaticPHE_Launch.connect('clicked(bool)', self.onPushButton_SemiAutomaticPHE_Launch)
    # self.ui.pushButton_SemiAutomaticPHE_ShowResult.connect('clicked(bool)', self.onPushButton_SemiAutomaticPHE_ShowResult)

    ###MAXIME THIS FIXES THE SELF CURRENT INDEX VALUE PROBLEM BUT ERASE PAINT
    # BUTTON
    self.ui.dropDownButton_label_select.currentIndexChanged.connect(self.onDropDownButton_label_select)

    self.ui.PauseTimerButton.connect('clicked(bool)', self.togglePauseTimerButton)
    self.ui.StartTimerButton.connect('clicked(bool)', self.toggleStartTimerButton)
    self.ui.pushButton_ToggleFill.connect('clicked(bool)', self.toggleFillButton)
    self.ui.SegmentWindowPushButton.connect('clicked(bool)', self.onSegmendEditorPushButton)
    # self.ui.UB_HU.valueChanged.connect(self.onUB_HU)
    # self.ui.LB_HU.valueChanged.connect(self.onLB_HU)
    # self.ui.pushDefaultMin.connect('clicked(bool)', self.onPushDefaultMin)
    # self.ui.pushDefaultMax.connect('clicked(bool)', self.onPushDefaultMax)
    self.ui.pushButton_undo.connect('clicked(bool)', self.onPushButton_undo)
    self.ui.testButton.connect('clicked(bool)', self.save_statistics)
    self.ui.pushButton_check_errors_labels.connect('clicked(bool)', self.check_for_outlier_labels)
    self.ui.pushButton_test1.connect('clicked(bool)', lambda: print('hello'))
    self.ui.pushButton_test2.connect('clicked(bool)', self.onpushbuttonttest2)


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
        print("self config yaml labels", self.config_yaml["labels"] )
        print("labels", label)
        self.ui.dropDownButton_label_select.addItem(label["name"])
        print("in set up label[name]", label["name"])

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
    #
    # # # Change the value of the upper and lower bound of the HU
    # # self.ui.UB_HU.setValue(self.UB_HU)
    # # self.ui.LB_HU.setValue(self.LB_HU)
    #
    # ### ANW ICH TYPE/LOCATION CONNECTIONS
    self.listichtype= [self.ui.ichtype1, self.ui.ichtype2, self.ui.ichtype3, self.ui.ichtype4, self.ui.ichtype5,
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



  # def setUpperAndLowerBoundHU(self, inputLB_HU, inputUB_HU):
  #     self.LB_HU = inputLB_HU
  #     self.UB_HU = inputUB_HU
  #     self.ui.UB_HU.setValue(self.UB_HU)
  #     self.ui.LB_HU.setValue(self.LB_HU)
  
  def enableSegmentAndPaintButtons(self):
    print("\n ENTERING enableSegmentAndPaintButtons \n")
    self.ui.pushButton_Paint.setEnabled(True)
    self.ui.pushButton_Erase.setEnabled(True)
    self.ui.pushButton_SemiAutomaticPHE_Launch.setEnabled(True)


  def saving_shortcut(self):
      print("entering sving shortcut pressed")
      self.onSaveSegmentationButton()


  def disableSegmentAndPaintButtons(self):
    print("\n ENTERING disableSegmentAndPaintButtons \n")
    self.ui.pushButton_Paint.setEnabled(False)
    self.ui.pushButton_SemiAutomaticPHE_Launch.setEnabled(False)
    self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(False)
    self.ui.pushButton_Erase.setEnabled(False)
    
  def getDefaultDir(self):
      print("\n ENTERING getDefaultDir \n")
      self.DefaultDir = qt.QFileDialog.getExistingDirectory(None,"Open default directory", self.DefaultDir, qt.QFileDialog.ShowDirsOnly)


  #maxime modif
      # maxime

  # Define a callback function for the observer

  def observeSegmentationNode(self):
      print("\n ENTERING observeSegmentationNode \n")
      segmentationNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLSegmentationNode')
      # print("segmentation node", segmentationNode)

      def segmentModifiedCallback(segment, event, segmentation_node):
          # print("segmentModifiedCallback event", event)
          print("Segment modified:", segment.GetName())
          self.segmentationModified = True
          print("self segmentation modified", self.segmentationModified)

      if segmentationNode:
          # Get the active segment
          segments = segmentationNode.GetSegmentation()
          # print("segments", segments)
          # Get number of segments
          num_segments = segments.GetNumberOfSegments()
          print("num of segments", num_segments)

          # Iterate through segments and collect names
          segment_names = []

          # Create a dictionary to store observer tags
          # observer_tags = {}

          for i in range(num_segments):
              segment = segments.GetNthSegment(i)
              segment_name = segment.GetName()
              segment_names.append(segment.GetName())

              # Add observer to the segment
              observer_tag = segment.AddObserver(
                  vtk.vtkCommand.ModifiedEvent,
                  partial(segmentModifiedCallback, segment))
              self.observer_tags[segment_name] = observer_tag

          print("segment names", segment_names)



      # segment_id = segmentationNode.GetDisplayNode().GetID()
      #
      # active_segment_ids = vtk.vtkStringArray()
      # segmentationNode.GetActiveSegmentIDs(active_segment_ids)
          # active_segment_id = active_segment_ids.GetValue(0) if (active_segment_ids.GetNumberOfValues()) else None

      print("setting observer")

      # segment_node = segmentationNode.GetSegmentation().GetSegment(segment_id)
      # if segment_node:
      #     observer_tag = segment_node.AddObserver(
      #         vtk.vtkCommand.ModifiedEvent, self.onSegmentationModified)
      #     return observer_tag
      # else:
      #     print("Segment not found")
      #     return None
      # segmentation = segmentationNode.GetSegmentation()

      # segmentationNodeObserverTag = segmentationNode.AddObserver(
      #     vtk.vtkCommand.ModifiedEvent, self.onSegmentationModified)
      # segmentationObserverTag = segmentationNode.AddObserver(
      #     vtk.vtkCommand.ModifiedEvent,
      #     self.onSegmentationModified)
      # self.segmentationNodeObserverTag = segmentationNodeObserverTag
      # self.segmentationObserverTag = segmentationObserverTag



      # segmentationNodeObserverTag = segmentationNode.AddObserver(
      #     vtk.vtkCommand.ModifiedEvent, self.onSegmentationModified)
      # print(f"Observer added with tag: {segmentationNodeObserverTag}")
      # segmentObserverTag = segmentationNode.AddObserver(
      #     vtkSegmentation.vtkSegmentationNode.SegmentModifiedEvent,
      #     onSegmentModified)
      # print(f"Observer added with tag: {segmentObserverTag}")
      # Get the event ID for SegmentModifiedEvent
      # segmentModifiedEvent = vtk.vtkCommand.ModifiedEvent  # Assuming general ModifiedEvent
      #
      # # Add an observer to the segmentation node
      # segmentObserverTag = segmentationNode.AddObserver(
      #     segmentModifiedEvent, self.onSegmentationModified)
      # print(f"Observer added with tag: {segmentObserverTag}")

      print(" MMMMMMMMMM observeSegmentation Node self segmentation modified",
            self.segmentationModified)
      print("observer setted")

  # def onSegmentationModified(self, caller, event):
  #     print(" \n dddddddddddd segmentation modified \n ")
  #     self.segmentationModified = True

  # def navigateCase(self, segmentModifiedCallback=None):
  #     print(" entered navigateCase", self.segmentationModified)
  #     if self.segmentationModified:
  #         print("segmentation modified to true")
  #         save = qt.QMessageBox.question(slicer.util.mainWindow(),
  #                                        'Save Segmentation?',
  #                                        'Do you want to save the current segmentation before navigating?',
  #                                        qt.QMessageBox.Yes | qt.QMessageBox.No)
  #         print("leaving qt message box")
  #         if save == qt.QMessageBox.Yes:
  #             print("qt message box save")
  #             self.onSaveSegmentationButton()
  #             self.segmentationModified = False
  #
  #         for element in self.observer_tags:
  #             print("element observer tags", element)
  #             # Add observer to the segment
  #             del element
  #
  #         self.observer_tags = {}
  #
  #     return None

  # import slicer
  # from PySide2 import QtWidgets as qt

  def navigateCase(self, direction):
      print("Entered navigateCase")
      print("direction", direction)

      # Check if segmentation is modified
      if self.segmentationModified:
          print("Segmentation modified")

          # # Ask user to save segmentation
          # save = qt.QMessageBox.question(slicer.util.mainWindow(),
          #                                'Save Segmentation?',
          #                                'Do you want to save the current segmentation before navigating?',
          #                                qt.QMessageBox.Yes | qt.QMessageBox.No)
          # print("Message box closed")

          def show_message_box():
              # Create a QMessageBox
              message_box = qt.QMessageBox(slicer.util.mainWindow())
              message_box.setWindowTitle('Save Segmentation?')
              message_box.setText(
                  'Do you want to save the current segmentation before navigating?')

              # Add Yes and No buttons
              message_box.addButton(qt.QMessageBox.Yes)
              message_box.addButton(qt.QMessageBox.No)

              # Show the message box as modal
              result = message_box.exec_()

              # After the message box is closed, further code execution resumes
              print("Dialog closed. Continuing with the code...")

              # Determine which button was clicked and act accordingly
              if result == qt.QMessageBox.Yes:
                  print("User clicked Yes")
                  self.onSaveSegmentationButton(direction)
                  self.segmentationModified = False
                  print("done")
                  # Do something when user clicks Yes
              elif result == qt.QMessageBox.No:
                  print("User clicked No")
                  self.segmentationModified = False
                  if direction == "Next":
                    self.onNextButton()
                  else :
                      self.onPreviousButton()
                  # Do something when user clicks No

          # Call the function to show the message box
          show_message_box()

          # Code execution will pause at the message box until the user closes it.
          # After closing the message box, the code execution will resume.

          #remove observers
          self.cleanup_observers()

          print("Continuing with the rest of the code...")


          # def show_message_box():
          #     # Create a modal dialog
          #     dialog = qt.QDialog(slicer.util.mainWindow())
          #     dialog.setWindowTitle('Save Segmentation?')
          #
          #     # Create a layout for the dialog
          #     layout = qt.QVBoxLayout()
          #
          #     # Add a label with the message
          #     label = qt.QLabel("Do you want to save the current segmentation before navigating?.")
          #     layout.addWidget(label)
          #
          #     # Add Ok button
          #     ok_button = qt.QPushButton("OK")
          #     layout.addWidget(ok_button)
          #
          #     # Set the layout for the dialog
          #     dialog.setLayout(layout)
          #
          #     # Connect the button to close the dialog
          #     def close_dialog():
          #         dialog.accept()
          #
          #     ok_button.clicked.connect(close_dialog)
          #
          #     # Show the dialog as modal
          #     dialog.exec_()
          #
          #     # After the dialog is closed, further code execution resumes
          #     print("Dialog closed. Continuing with the code...")
          #
          # # Call the function to show the message box
          # show_message_box()
          #
          # # Code execution will pause at the message box until the user closes it.
          # # After closing the message box, the code execution will resume.
          # print("Continuing with the rest of the code...")



          # # # Ask user to save segmentation
          # # Create a QMessageBox
          # message_box = qt.QMessageBox(slicer.util.mainWindow())
          # message_box.setWindowTitle('Save Segmentation?')
          # message_box.setText('Do you want to save the current segmentation before navigating?')
          # message_box.setStandardButtons(
          #     qt.QMessageBox.Yes | qt.QMessageBox.No)
          #
          # # Show the message box
          # message_box.show()
          #
          # # Use event handling to determine when to close it
          # def close_message_box(result):
          #     if result == qt.QMessageBox.Ok:
          #         print(" ACCEPTTED ***")
          #
          #         self.onSaveSegmentationButton()
          #         self.segmentationModified = False
          #         message_box.accept()
          #         print("completed accepeted")
          #         # Accept the message box
          #     elif result == qt.QMessageBox.Cancel:
          #         print(" REJECTED ***")
          #         message_box.reject()  # Reject the message box
          #
          # message_box.finished.connect(close_message_box)
          print("Message box closed")




          # # Check user response
          # if save == qt.QMessageBox.Yes:
          #     print("User selected to save segmentation")
          #     self.onSaveSegmentationButton()
          #     self.segmentationModified = False
          # else:
          #     print("User selected not to save segmentation")



      return None

  def cleanup_observers(self):
      # Remove observers
      for observer_tag in self.observer_tags.values():
          slicer.mrmlScene.RemoveObserver(observer_tag)

      self.observer_tags = {}

  # def cleanup(self):
  #     segmentationNode = slicer.mrmlScene.GetFirstNodeByClass(
  #         'vtkMRMLSegmentationNode')
  #     if segmentationNode:
  #         segmentationNode.RemoveObserver(self.segmentationNodeObserverTag)
  #         segmentation = segmentationNode.GetSegmentation()
  #         if segmentation:
  #             segmentation.RemoveObserver(self.segmentationObserverTag)


  def onPushButton_uint8casting(self):
      """
      Check for dtype in nrrd or nifti files and cast to uint8 if not already - this causes issues
      in Slicer 5.6 (vector error). Segmentation file should anyway be uint8, not float.

      """
      print("\n ENTERING onPushButton_uint8casting \n")
      # message box to confirm overwriting
      reply = qt.QMessageBox.question(None, 'Message', 'Casiting to uint8. Do you want to overwrite the original segmentation files?', qt.QMessageBox.Yes | qt.QMessageBox.No, qt.QMessageBox.No)
      if reply == qt.QMessageBox.No:
          raise ValueError('The segmentation files were not overwritten.')
      else:
          self.cast_segmentation_to_uint8()

  def cast_segmentation_to_uint8(self):
      print("\n ENTERING cast_segmentation_to_uint8 \n")
      for case in self.CasesPaths:
          # Load the segmentation
          input_path = os.path.basename(case)
          if input_path.endswith('.nii') or input_path.endswith('.nii.gz'):
              segm = nib.load(case)
              segm_data = segm.get_fdata()
              print(f'infile: {input_path}, dtype: {segm_data.dtype}')
              if segm_data.dtype != np.uint8:
                  segm_data = segm_data.astype(np.uint8)
                  segm_nii = nib.Nifti1Image(segm_data, segm.affine)
                  nib.save(segm_nii, case)
                  print(f'converted file {input_path} to uint8')
          elif input_path.endswith('.nrrd'):
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
      print("\n You have just clicked onBrowseFoldersButton.\n")
      # LLG get dialog window to ask for directory
      self.CurrentFolder= qt.QFileDialog.getExistingDirectory(None,"Open a folder", self.DefaultDir, qt.QFileDialog.ShowDirsOnly)
      self.updateCurrentFolder()
      # LLG GET A LIST OF cases WITHIN CURRENT FOLDERS (SUBDIRECTORIES). List comp to get only the case
      # self.CasesPaths = sorted(glob(f'{self.CurrentFolder}{os.sep}{self.VOLUME_FILE_TYPE}'))
      #this line below works well for the brats dataset
      # self.CasesPaths = sorted(glob(f'{self.CurrentFolder}{os.sep}{self.FOLDER_FORMAT}*{os.sep}*{self.CONTRAST}{self.VOLUME_FILE_TYPE}'))
      #this line below works well for bids dataset
      self.CasesPaths = sorted(glob(f'{self.CurrentFolder}{os.sep}{self.FOLDER_FORMAT}*{os.sep}anat{os.sep}*{self.CONTRAST}{self.VOLUME_FILE_TYPE}'))
      self.lenDirectoryCases = len(self.CasesPaths)

      #mb added for efficiency
      self.allCasesPath = sorted(glob(f'{self.CurrentFolder}{os.sep}{self.FOLDER_FORMAT}*{os.sep}anat{os.sep}*{self.CONTRAST}{self.VOLUME_FILE_TYPE}'))
      self.allCases = []
      for i in range(len(self.allCasesPath)):
          self.allCases.append(os.path.split(self.allCasesPath[i])[1])

      print("self all cases", self.allCases)



      #trying with bids only t1raw
      ###HERE
      # self.CasesPaths = glob(f'{self.CurrentFolder}{os.sep}')
      # print("test debug maxime")
      print("Cases Paths printed", self.CasesPaths)
      print("current folder", self.CurrentFolder)
      print("self Volume file type", self. VOLUME_FILE_TYPE)
      print("self regex", self.VOL_REGEX_PATTERN)
      print("folder format", self.FOLDER_FORMAT)
      # self.Cases = sorted([re.findall(self.VOL_REGEX_PATTERN,os.path.split(i)[-1])[0] for i in self.CasesPaths])
      # self.Cases = sorted([re.findall(f'/{self.VOL_REGEX_PATTERN}',
      #                                 os.path.split(
      #     i)[1]) for i in self.CasesPaths])
      # test_split = os.path.split(self.CasesPaths[0])
      # good_name = test_split[1]
      # print("good name", good_name)
      # print("test slpit", test_split)
      # print("test split 0", test_split[0])
      # print("test split 1", test_split[1])

      # jacques = os.path.split(self.CasesPaths[0])[1]
      # print ("jacques ", jacques)
      self.Cases = []
      for i in range(len(self.CasesPaths)):
          self.Cases.append(os.path.split(self.CasesPaths[i])[1])

      print("self cases", self.Cases)
      print()

      # self.Cases = sorted([re.findall("/",os.path.split(
      #     i)[-1])[0] for i in self.CasesPaths])
      # print("self vol regex i o path")
      # print("os path path .split", os.path.split(self.CasesPaths))

      # self.Cases =  re.findall(self.VOL_REGEX_PATTERN, str(self.CasesPaths))
      # print("self cases", self.Cases)
      self.update_UI_case_list()
      print("\n leaving browse folder button \n")

      # print("checking if previous segmentation exists")
      # print("self current directory", self.CurrentFolder)
      # # remainingCasesPath = os.path


      # ####modif maxime starting from scrath
      # self.CurrentFolder = qt.QFileDialog.getExistingDirectory(None,
      #                                                          "Open a folder",
      #                                                          self.DefaultDir,
      #                                                          qt.QFileDialog.ShowDirsOnly)
      # self.updateCurrentFolder()
      # self.CasesPaths = glob(f'{self.CurrentFolder}{os.sep}')
      # print("current folder printed", self.CurrentFolder)
      # print("Cases Paths printed", self.CasesPaths)
      # print("Volume file type", self.VOLUME_FILE_TYPE)
      # print("self yaml volume load ", self.config_yaml[
      # 'regex_format_volume_load'])

  def update_UI_from_other_case_list(self):
      print(" ENTERING UPDATE_from_other_case_list \n")
      self.ui.SlicerDirectoryListView.clear()
      self.ui.SlicerDirectoryListView.addItems(self.allCases)
      # print(" in if yamlListofCaseflas", self.yamlListPath)
      # print("self.yamListof cases", self.yamlListName)
      print("len selfyamlListName", len(self.yamlListName))
      print("len selfyamlListPath", len(self.yamlListPath))
      print("index self currentCase", self.currentCase_index)
      # self.CasesPaths = self.yamlListPath
      # self.Cases = self.yamlListName
      #
      # print("self cases paths in update ui diff", self.CasesPaths)
      # print("self cases in yamlListName", self.Cases)

      # self.currentCase = self.yamlListName[self.currentCase_index]
      # self.currentCasePath = self.yamlListPath[self.currentCase_index]

      # #curentCase index corresponds to which index in self.allCases
      # right_element = self.allCases[self.currentCase_index]
      # right_index = self.currentCase_index - self.get_index_difference()
      # print("right index", right_index)
      #
      # if right_index >= 0:
      #     self.currentCase = self.yamlListName[right_index]
      #     self.currentCasePath = self.yamlListPath[right_index]
      # else :
      #     self.currentCase = self.allCases[self.currentCase_index]
      #     self.currentCasePath = self.allCasesPath[self.currentCase_index]

      # curentCase index corresponds to which index in self.allCases

      #get the yaml name
      if self.indexYaml != -1 and (self.yamlListName != []):
          print("index yaml succed")
          print(" in update_UI_from_other_case_list self indexYaml ",
                self.indexYaml)
          self.currentCase = self.yamlListName[self.indexYaml]
          print("currentCase succed", self.currentCase)
          self.currentCasePath = self.yamlListPath[self.indexYaml]
          print("self current path succes", self.currentCasePath)
          self.currentCase_index = self.allCases.index(self.nameYaml)
          print("worked!!")
      else :
          print("except index yaml")
          self.currentCase = self.allCases[self.currentCase_index]
          self.currentCasePath = self.allCasesPath[self.currentCase_index]




  def check_different_list(self):
      print(" ENTERING check_other_list \n")
      if (self.yamlListPath != []) and (self.yamlListName != []):
          print(" IN update_UI_case_list ABOUT TO GO IN SELF YAMLLIST",
                self.yamlListPath)
          print(" in if yamlListName", self.yamlListName)
          self.CasesPaths = self.yamlListPath
          self.Cases = self.yamlListName

          print("self cases paths in update ui diff", self.CasesPaths)
          print("self cases in yamlListName", self.Cases)
          return True
      return False

  def set_appropriate_index(self):
      print(" ENTERING set_appropriate_index \n")
      if self.check_different_list():
          print(" self check different list in set approiate index")
          pass

  # def get_current


  def update_UI_case_list(self):
      print("\n ENTERING UPDATE_UI_CASE_LIST \n")
      # print("update_UI_case_list self.Cases", self.Cases)
      self.ui.SlicerDirectoryListView.clear()
      # Populate the SlicerDirectoryListView
      if self.check_different_list():
          print("in check differetn list")
          self.update_UI_from_other_case_list()
          print("in check differetn list,", self.currentCase_index)

      else :
          print("in else update ui case_list")
          self.ui.SlicerDirectoryListView.addItems(self.allCases)
          self.currentCase_index = 0  # THIS IS THE CENTRAL THING THAT HELPS FOR CASE NAVIGATION
      print("self currencCas eindex reset", self.currentCase_index)
      # print("self currentCasepATH 1", self.currentCasePath)
      self.updateCaseAll()
      print("self currentCasepATH 2", self.currentCasePath)
      self.loadPatient()

  def updateCaseAll(self):
      print("\n ENTERING UPDATECASEALL \n")
      # All below is dependent on self.currentCase_index updates,
      if self.check_different_list():
          print(" in entering updatecaseall")
          self.update_UI_from_other_case_list()
      else :
          print("om else update case all")
          print(" self currentcas eindex", self.currentCase_index)

          self.currentCase = self.Cases[self.currentCase_index]
          self.currentCasePath = self.CasesPaths[self.currentCase_index]

          print(" self curent case", self.currentCase)
          print(" self currentcas eindex", self.currentCase_index)
          print("self current case path", self.currentCasePath)

      print("after else", self.currentCasePath)
      self.updateCurrentPatient()
      print("after update Current Patient", self.currentCasePath)
      print(" update casle all currentcase index", self.currentCase_index)
      print("self current patient", self.currentCase)
      # Highlight the current case in the list view (when pressing on next o)
      self.ui.SlicerDirectoryListView.setCurrentItem(self.ui.SlicerDirectoryListView.item(self.currentCase_index))

  def get_index_difference(self):
      len_directoryCases = self.lenDirectoryCases
      print("len directoryCases", len_directoryCases)
      len_yamlCases = len(self.yamlListName)
      print(" len yamlCases", len_yamlCases)
      difference = int(len_directoryCases - len_yamlCases)
      print("difference", difference)
      return difference

  def getCurrentTableItem(self):
      print("\n ENTERING UPDATE_UI_CASE_LIST \n")
      # ----- ANW Addition ----- : Reset timer when change case and uncheck all checkboxes
      self.resetTimer()
      # self.uncheckAllBoxes()
      self.clearTexts()

      print("self ui slicerdirectory lsit view,", self.ui.SlicerDirectoryListView.currentRow)

      # When an item in SlicerDirectroyListView is selected the case number is printed
      # below we update the case index and we need to pass one parameter to the methods since it takes 2 (1 in addition to self)
      # self.updateCaseIndex(
      #     self.ui.SlicerDirectoryListView.currentRow)  # Index starts at 0
      # Update the case index
      # print(" self cirrentCase", self.currentCase)
      # self.currentCase_index = self.yamlListName.index(self.currentCase)
      # Same code in onBrowseFoldersButton, need to update self.currentCase
      # note that updateCaseAll() not implemented here - it is called when a case is selected from the list view or next/previous button is clicked
      # All below is dependent on self.currentCase_index updates,
      if self.check_different_list():
          self.currentCase_index = self.ui.SlicerDirectoryListView.currentRow
          self.indexYaml = self.ui.SlicerDirectoryListView.currentRow
          print("self ui slicerdirectory lsit view self index yaml,",
                self.indexYaml)
          self.indexYaml = -1

          self.update_UI_from_other_case_list()
      else:
          print("entering else getcurrenttableidem")
          self.updateCaseIndex(
              self.ui.SlicerDirectoryListView.currentRow)  # Index starts at 0
          # Update the case index
          self.currentCase_index = self.ui.SlicerDirectoryListView.currentRow
          self.currentCase = self.Cases[self.currentCase_index]
          self.currentCasePath = self.CasesPaths[self.currentCase_index]
          print("entering else getcurrenttableidem self currentCase_index", self.currentCase_index)
          print("entering else getcurrenttableidem self currentCase",
                self.currentCase)
          print("entering else getcurrenttableidem self currentCasePath ",
                self.currentCasePath)


      # # When an item in SlicerDirectroyListView is selected the case number is printed
      # # below we update the case index and we need to pass one parameter to the methods since it takes 2 (1 in addition to self)
      # self.updateCaseIndex(self.ui.SlicerDirectoryListView.currentRow) # Index starts at 0
      # # Update the case index
      # self.currentCase_index = self.ui.SlicerDirectoryListView.currentRow
      # # Same code in onBrowseFoldersButton, need to update self.currentCase
      # # note that updateCaseAll() not implemented here - it is called when a case is selected from the list view or next/previous button is clicked
      # # All below is dependent on self.currentCase_index updates,
      # if self.check_different_list():
      #     self.update_UI_from_other_case_list()
      # else :
      #     self.currentCase = self.Cases[self.currentCase_index]
      #     self.currentCasePath = self.CasesPaths[self.currentCase_index]

      # self.currentCase = self.Cases[self.currentCase_index]
      # self.currentCasePath = self.CasesPaths[self.currentCase_index]
      self.updateCurrentPatient()
      self.loadPatient()
      
      # ----- ANW Addition ----- : Reset timer when change case, also reset button status
      self.resetTimer()

  def updateCaseIndex(self, index):
      print("\n ENTERING UPDATECASEINDEX \n")
      # ----- ANW Modification ----- : Numerator on UI should start at 1 instead of 0 for coherence
      self.ui.FileIndex.setText('{} / {}'.format(index+1, len(self.Cases)))

  def updateCurrentFolder(self):
      print("\n ENTERING UPDATECASE \n")
      self.ui.CurrentFolder.setText('Current folder : \n...{}'.format(self.CurrentFolder[-80:]))
      
  def updateCurrentPatient(self):
      print("\n ENTERING updateCurrentPatient \n")
      if self.yamlListName:
          print("name")
          # print("self yamllist name", self.yamlListName)
          # print("self yamllipah", self.yamlListPath)
      print("self current patient", self.currentCase)

      self.ui.CurrentPatient.setText(f'Current case : {self.currentCase}')

      print("self current index", self.currentCase_index)

      self.updateCaseIndex(self.currentCase_index)
  
  def updateCurrentSegmenationLabel(self):
      print("\n ENTERING updateCurrentSegmenationLabel \n")
      self.ui.CurrentSegmenationLabel.setText('Current segment : {}'.format(self.segment_name))
      
  def loadPatient(self):
      print("\n ENTERING loadPatient \n")
      print("IN LOAD PATIENT")
      timer_index = 0
      self.timers = []
      for label in self.config_yaml["labels"]:
          self.timers.append(Timer(number = timer_index))
          timer_index = timer_index + 1
      
      # reset dropbox to index 0
      #initially was to 0 -- maxime modified
      # self.ui.dropDownButton_label_select.setCurrentIndex(0)
      self.ui.dropDownButton_label_select.setCurrentIndex(self.currentCase_index)

      print("load patient current index", self.currentCase_index)

      
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

      #deactive the interpolation
      if not self.interpolation:
          print("interpolation deactivation set to true")
          self.VolumeNode.GetDisplayNode().SetInterpolate(0)
          self.ui.toggleInterpolation.setStyleSheet("background-color : red")


      # MB - WW removed since MRI may also be loaded
      # Vol_displayNode.SetWindow(85)
      # Vol_displayNode.SetLevel(45)

      #mb addind

      self.newSegmentation()
      if self.loadMask :
          self.load_segmentation()

      # if self.loadMask :
      #     self.load_segmentation()
      #     self.createNewSegments()
      # else :
      #     self.newSegmentation()
      self.subjectHierarchy()
      self.clean_hierarchy_folder()

  # def loadPatient(self):
  #     print("\n ENTERING loadPatient \n")
  #     print("IN LOAD PATIENT")
  #     timer_index = 0
  #     self.timers = []
  #     for label in self.config_yaml["labels"]:
  #         self.timers.append(Timer(number=timer_index))
  #         timer_index = timer_index + 1
  #
  #     # reset dropbox to index 0
  #     # initially was to 0 -- maxime modified
  #     # self.ui.dropDownButton_label_select.setCurrentIndex(0)
  #     self.ui.dropDownButton_label_select.setCurrentIndex(
  #         self.currentCase_index)
  #
  #     # timer reset if we come back to same case
  #     self.called = False
  #
  #     slicer.mrmlScene.Clear()
  #     slicer.util.loadVolume(self.currentCasePath)
  #     self.VolumeNode = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')[
  #         0]
  #     self.updateCaseAll()
  #     self.ui.CurrentSegmenationLabel.setText(
  #         'New patient loaded - No segmentation created!')
  #     # Adjust windowing (no need to use self. since this is used locally)
  #     Vol_displayNode = self.VolumeNode.GetDisplayNode()
  #     Vol_displayNode.AutoWindowLevelOff()
  #     # MB - WW removed since MRI may also be loaded
  #     # Vol_displayNode.SetWindow(85)
  #     # Vol_displayNode.SetLevel(45)
  #     self.newSegmentation()
  #     self.subjectHierarchy()


  def load_segmentation(self):
      if self.loadMask :
          name = self.Cases[self.currentCase_index]
          filename = self.remove_file_extension(name)
          print("load_segmentation name", filename)
          version = self.get_latest_version(filename)
          str_version = f"_v{version:02d}"
          print("version", version)
          print("str_version", str_version)
          listfile = []
          dictTupleFileInfo = {}
          for i in range(len(self.config_yaml["labels"])):
              labelName = self.config_yaml["labels"][i]["name"]
              # reconstruct the path of the file_mask
              maskFilePath = (f'{self.OutputFolder}{os.sep}versions{os.sep}'
                              f'{filename}_'
                              f'{labelName}{str_version}{self.file_extension}')
              print("maskFilePath", maskFilePath)
              listfile.append(maskFilePath)
              print("load_segmentation listfile should have 3", listfile)
              file_info = (f"{filename}_{labelName}", str_version)
              # dictTupleFileInfo[f"{filename}_{labelName}"] = file_info
              dictTupleFileInfo[f"{maskFilePath}"] = file_info


          #tuple id for associating file label to file version
          print("load_segmentation( dictTupleFileInfo", dictTupleFileInfo)

          # #load each segment in the display zone
          # for segment in listfile:
          #     print("for loop in segment listfile", segment)
          #     name = dictTupleFileInfo[segment][0]
          #     if os.path.exists(segment):
          #         segmentationNode = slicer.util.loadSegment(segment)
          #         segmentationNode.SetName(f"{name}{self.file_extension}")
          #         print("in for segment in listfile segmentationNode",
          #               segmentationNode)

          # load each segment in the display zone
          for segment in listfile:
              print("for loop in segment listfile", segment)
              name = dictTupleFileInfo[segment][0]
              labelName = self.config_yaml["labels"][0]["name"]

              if os.path.exists(segment):
                  [success, labelmap_node] = slicer.util.loadLabelVolume(
                      segment, returnNode=True)
                  print("labelmap node in os path exist segment", labelmap_node)


                  if success: #RENDU ICI 27 MAI 2024

                      #get the segmentation node (the same each time)
                      segmentation_node = slicer.mrmlScene.GetFirstNodeByClass(
                          'vtkMRMLSegmentationNode')
                      print("if success get segmentationNode",
                            segmentation_node)

                      #get the different segments
                      segments = segmentation_node.GetSegmentation()
                      print("if success get segments", segments)

                      # Convert label map to binary label map representation
                      binary_labelmap_node = slicer.mrmlScene.AddNewNodeByClass(
                          'vtkMRMLLabelMapVolumeNode')
                      print("\n \n if success binarylabel_map node",
                            binary_labelmap_node)


                      print("in if succss master representation",
                            segments.GetNthSegment)

                      print("name in if success", name)
                      print("name with file extension", f"{name}{self.file_extension}")

                      # segment_id = segmentation_node.GetSegmentation().GetSegmentIdBySegmentName(
                      #     name)
                      # print("in if succss segment_id", segment_id)
                      # Create or get the display node
                      display_node = slicer.mrmlScene.GetFirstNodeByClass(
                          'vtkMRMLLabelMapVolumeDisplayNode')
                      if display_node is None:
                          display_node = slicer.mrmlScene.AddNewNodeByClass(
                              'vtkMRMLLabelMapVolumeDisplayNode')
                      print("display node", display_node)

                      # Set display node reference
                      print("argument display node get id",
                            display_node.GetID())
                      binary_labelmap_node.SetAndObserveDisplayNodeID(
                          display_node.GetID())

                      # Create or get the storage node
                      storage_node = slicer.mrmlScene.GetFirstNodeByClass(
                          'vtkMRMLStorageNode')
                      print("storage node", storage_node)
                      if storage_node is None:
                          storage_node = slicer.mrmlScene.AddNewNodeByClass(
                              'vtkMRMLStorageNode')

                      # Set storage node reference
                      binary_labelmap_node.SetAndObserveStorageNodeID(
                          storage_node.GetID())
                      print("storage node.get id", storage_node.GetID() )

                      # Create or get the transform node
                      transform_node = slicer.mrmlScene.GetFirstNodeByClass(
                          'vtkMRMLTransformNode')
                      if transform_node is None:
                          transform_node = slicer.mrmlScene.AddNewNodeByClass(
                              'vtkMRMLTransformNode')
                      print("transform_node", transform_node)

                      # Set transform node reference
                      binary_labelmap_node.SetAndObserveTransformNodeID(
                          transform_node.GetID())
                      print("transform_node get id", transform_node.GetID())

                      print("aaaaaa")

                      # segmentation_node.SetBinaryLabelmapRepresentation(
                      #     segment_id, labelmap_node)

                      print("in if success it worked for labelmapping")
                      # Load the labelmap volume
                      # labelmap_node = slicer.util.loadLabelVolume(segment)

                      # The labelmap volume will automatically be converted to a segmentation node
                      # segmentation_node = labelmap_node.GetSegmentationNode()
                      # print("success segmentation_node", segmentation_node)


                      # # Step 1: Retrieve the source segmentation node and the segment you want to convert
                      # source_segmentation_node = labelmap_node.GetSegmentationNode()
                      # source_segment_id = "SourceSegmentID"
                      #
                      # # Step 2: Retrieve the target segmentation node
                      # target_segmentation_node = slicer.util.getNode(
                      #     "sub-ott002_acq-sag_T2w.nii.gz_segmentation")
                      #
                      # # Step 3: Create a new segment in the target segmentation node
                      # target_segmentation_node.CreateEmptySegment(
                      #     "NewSegmentID", "NewSegmentName")
                      #
                      # # Step 4: Copy the binary labelmap representation of the source segment to the new segment in the target segmentation node
                      # source_segmentation_node.GetSegmentation().CopySegmentFromSegmentation(
                      #     source_segment_id,
                      #     target_segmentation_node.GetSegmentation(),
                      #     "NewSegmentID")
                      #
                      # # # Optionally, remove the temporary loaded segmentation node
                      # # slicer.mrmlScene.RemoveNode(loadedSegmentationNode)


                  # if success:
                  #     segmentation = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0].GetSegmentation()
                  #     print("segmentation", segmentation)
                  #     new_segment_id = segmentation.AddEmptySegment(f'{filename}_'
                  #             f'{labelName}{str_version}{self.file_extension}')
                  #     print("new segment id", new_segment_id)
                  #     # slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(
                  #     #     labelmap_node, segmentation, new_segment_id)
                  #     nodeMapLoaded = slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(
                  #         labelmap_node, segmentation)
                  #     segmentation.CreateClosedSurfaceRepresentation()
                  #     print("  nodeMapLoaded", nodeMapLoaded)
                  #
                  #     # # Optionally, remove the temporary loaded segmentation node
                  #     # slicer.mrmlScene.RemoveNode(loadedSegmentationNode)






  # Getter method to get the segmentation node name    - Not sure if this is really useful here.
  @property
  def segmentationNodeName(self):
    print("\n ENTERING segmentationNodeName \n")
    return f'{self.currentCase}_segmentation'
  
      
  def newSegments(self):
      print("\n ENTERING newSegments \n")
      pass
      
  def onPushButton_NewMask(self):
      print("\n ENTERING onPushButton_NewMask \n")
      self.newSegments()
            
  def onPreviousButton(self):
      print("\n ENTERING onPreviousButton \n")
      if self.segmentationModified:
        self.navigateCase("Previous")
        return None
      else:
          self.cleanup_observers()

      # ----- ANW Addition ----- : Reset timer when change case and uncheck all checkboxes
      self.resetTimer()
      # self.uncheckAllBoxes()
      self.clearTexts()

      #Code below avoid getting in negative values. 
      self.currentCase_index = max(0, self.currentCase_index-1)
      self.updateCaseAll()
      self.loadPatient()

      if self.currentCase_index == 0:
          print("*** This is the first case of the list. ***")
          self.show_message_box("This is the first case of the list.")

      print("*** in on next button self currentCase_index", self.currentCase_index)
      print("*** in on next button len(self.Cases-1", len(self.Cases)-1)
      print("*** in on next button self current in+1", self.currentCase_index+1)

  
  def onNextButton(self):
      print("\n ENTERING onNextButton \n")
      # print(" self segmentation Modified: ", self.SegmentationModified)
      print(" MMMMMMMMMM onNexButton self segmentation modified",
            self.segmentationModified)
      if self.segmentationModified:
        self.navigateCase("Next")
        return None
      else:
          self.cleanup_observers()
      # self.observeSegmentationNode()


      # ----- ANW Addition ----- : Reset timer when change case and uncheck all checkboxes
      self.resetTimer()
      # self.uncheckAllBoxes()
      self.clearTexts()

      # ----- ANW Modification ----- : Since index starts at 0, we need to do len(cases)-1 (instead of len(cases)+1).
      # Ex. if we have 10 cases, then len(case)=10 and index goes from 0-9,
      # so we have to take the minimum between len(self.Cases)-1 and the currentCase_index (which is incremented by 1 everytime we click the button)
      # self.currentCase_index = min(len(self.Cases)-1, self.currentCase_index+1)
      print("self currentCaseindex BEFORE min len", self.currentCase_index)

      self.currentCase_index = min(len(self.allCases)-1,
                                   self.currentCase_index+1)
      print("self currentCaseindex after min len", self.currentCase_index)

      self.updateCaseAll()
      self.loadPatient()

      if self.currentCase_index == (len(self.allCases)-1):
          print("*** This is the last case of the list. ***")
          self.show_message_box("This is the last case of the list.")

      print("*** in on next button self currentCase_index", self.currentCase_index)
      print("*** in on next button len(self.Cases-1", len(self.allCases)-1)
      print("*** in on next button self current in+1", self.currentCase_index+1)
      print(" incremented self currencease index quesiton",
            self.currentCase_index)

  def generate_message_box(self, message):
      # Create a message box
      messageBox = qt.QMessageBox()

      # Set the message box text
      messageBox.setText(message)

      # Set the message box title
      messageBox.setWindowTitle("Message Box")

      # Display the message box
      messageBox.exec_()


  def newSegmentation(self):
      print("IN NEW SEGMENTATION")
      # for creating new segmentation node to allow creation of segenation mask
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
      print("ABOUT TO SET ACTIVE ")
      self.segmentEditorWidget.setActiveEffectByName("No editing")


      # self.onPushButton_Paint()
      # self.segmentEditorWidget.setSegmentationNode(segmentationNode)
      # print(" segmentation node", segmentationNode)

      # # Assuming `segmentEditorWidget` is the Segment Editor widget
      # currentSegmentID = self.segmentEditorWidget.currentSegmentID
      # print("Current segment ID:", currentSegmentID)
      #
      # # Get the segmentation node
      # segmentationNode = slicer.mrmlScene.GetFirstNodeByName(
      #     "vtkMRMLSegmentationNode1")
      #
      # # Assuming segment ID is stored in the subject hierarchy node attributes
      # segmentationHierarchyNode = segmentationNode.GetSubjectHierarchyNode()
      # currentSegmentHierarchyNode = segmentationHierarchyNode.GetItemByDataNode(
      #     segmentationNode.GetSegmentation().GetSegment(0))
      #
      # # Get segment ID from attributes
      # segmentID = currentSegmentHierarchyNode.GetAttribute("SegmentID")
      # print("Current segment ID:", segmentID)

      # self.segmentEditorWidget.setCurrentSegmentID(segmentationNode)
      self.segmentEditorWidget.setActiveEffectByName("No editing")


  # # Load all segments at once
  # # TODO REMOVE THE NAME IN EACH SEGMENTS SINCE THIS IS NOT REALLY NEED. WOULD NEED TO MODIFY THE QC SCRIPT ALSO
  def createNewSegments(self, listfile=None):
        print("IN CREATE NEW SEGMENTS!!!!")
        # create the number of required segments
        # for label in self.config_yaml["labels"]:
        #     self.onNewLabelSegm(label["name"], label["color_r"], label["color_g"], label["color_b"], label["lower_bound_HU"], label["upper_bound_HU"])

        segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]

        self.set_color_label(segmentationNode)

        # for label in self.config_yaml["labels"]:
        #     print("******* ****** *****")
        #     print(" label yaml data", label)
        #     print("label yaml name", label["name"])
        #     print(" rgb", label["color_r"], label["color_g"], label["color_b"])
        #
        #     self.onNewLabelSegm(label["name"], label["color_r"],
        #                         label["color_g"], label["color_b"])
        #                         # label["lower_bound_HU"],
        #                         # label["upper_bound_HU"])
        #     # print("sel on NewlabelSegm", self.onNewLabelSegm())

        first_label_name = self.config_yaml["labels"][0]["name"]

        print(f" test get name {self.currentCase}")

        string = f"{self.currentCase}"
        regex = self.config_yaml["volume_extension"]
        print(string)
        cleaned = re.sub(regex, "", string)
        print(cleaned)

        self.first_label_segment_name = f"{cleaned}_{first_label_name}{regex}"
        print("first label segment name", self.first_label_segment_name)

        currentSegmentID = self.segmentEditorWidget.currentSegmentID
        print("Current segment ID in new segment creation:", currentSegmentID)

        ###ATTENTION! NEVER COMMENT THIS LINE BELOW SINCE IT WILL CAUSE
        # TROUBLE ++++ TO CORRECT (PAINTING AND SEGMENTATION)

        self.onPushButton_select_label(self.first_label_segment_name)

        # self.onPushButton_select_label(first_label_segment_name, self.config_yaml["labels"][0]["lower_bound_HU"], self.config_yaml["labels"][0]["upper_bound_HU"])
        # self.onPushButton_select_label(self.first_label_segment_name)

  # def createNewSegments(self):
  #     print("IN CREATE NEW SEGMENTS!!!!")
  #     # create the number of required segments
  #     # for label in self.config_yaml["labels"]:
  #     #     self.onNewLabelSegm(label["name"], label["color_r"], label["color_g"], label["color_b"], label["lower_bound_HU"], label["upper_bound_HU"])
  #
  #     for label in self.config_yaml["labels"]:
  #         print("******* ****** *****")
  #         print(" label yaml data", label)
  #         print("label yaml name", label["name"])
  #         print(" rgb", label["color_r"], label["color_g"], label["color_b"])
  #
  #         self.onNewLabelSegm(label["name"], label["color_r"],
  #                             label["color_g"], label["color_b"])
  #         # label["lower_bound_HU"],
  #         # label["upper_bound_HU"])
  #         # print("sel on NewlabelSegm", self.onNewLabelSegm())
  #
  #     first_label_name = self.config_yaml["labels"][0]["name"]
  #
  #     print(f" test get name {self.currentCase}")
  #
  #     string = f"{self.currentCase}"
  #     regex = ".nii.gz"
  #     print(string)
  #     cleaned = re.sub(regex, "", string)
  #     print(cleaned)
  #
  #     self.first_label_segment_name = f"{cleaned}_{first_label_name}{regex}"
  #     print("first label segment name", self.first_label_segment_name)
  #
  #     currentSegmentID = self.segmentEditorWidget.currentSegmentID
  #     print("Current segment ID in new segment creation:", currentSegmentID)
  #
  #     ###ATTENTION! NEVER COMMENT THIS LINE BELOW SINCE IT WILL CAUSE
  #     # TROUBLE ++++ TO CORRECT (PAINTING AND SEGMENTATION)
  #
  #     self.onPushButton_select_label(self.first_label_segment_name)
  #
  #     # self.onPushButton_select_label(first_label_segment_name, self.config_yaml["labels"][0]["lower_bound_HU"], self.config_yaml["labels"][0]["upper_bound_HU"])
  #     # self.onPushButton_select_label(self.first_label_segment_name)


  def newSegment(self, segment_name=None):
      print("IN NEW SEGMENT")
      print(" MMMMMMMMMM newSegment self segmentation modified",
            self.segmentationModified)

      #to adjust since already this method used in previous
      string = f"{self.currentCase}"
      regex = ".nii.gz"
      # print(string)
      cleaned = re.sub(regex, "", string)
      # print(cleaned)

      #maxime add clean observer
      self.cleanup_observers()
      self.segmentationModified = False


      # first_label_name = self.config_yaml["labels"][0]["name"]
      # label_name = self.config_yaml["labels"]["name"]
      # jacques = segment_name
      # print("** jacques", jacques)

      self.segment_name = f"{cleaned}_{segment_name}{regex}"
      srcNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      self.srcSegmentation = srcNode.GetSegmentation()

      #maxime modifications
      # Below will create a new segment if there are no segments in the segmentation node, avoid overwriting existing segments

      print("newSegment ELSE any segment exists")
      if self.loadMask:
          print("newSegment ELSE any segment exists self load mask",
                self.loadMask)
          self.segmentationNode = \
          slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
          # self.segmentationNode.GetSegmentation().AddEmptySegment(
          #     self.segment_name)
          print(" newSegment got segmentation node", self.segmentationNode)
          # aaa = self.get_existing_segment()
          # print("aaa", aaa)
          if self.get_existing_segment():
              print("new segment to be added")
              # self.create_vtk_segment()

              # self.segmentationNode.GetSegmentation().AddSegment(
              #     self.create_vtk_segment())

              self.create_vtk_segment()


              # # Add the segment to the segmentation node
              # self.segmentationNode.GetSegmentation().AddSegment(self.create_vtk_segment())

              # Update the segmentation node
              self.segmentationNode.Modified()
              print("should have worked if here")

          else :
              print("create an empty segment")
              self.segmentationNode = \
              slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
              self.segmentationNode.GetSegmentation().AddEmptySegment(
                  self.segment_name)
          # print("temp")
      else :
          print("newSegment ELSE ELSE")
          self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
          self.segmentationNode.GetSegmentation().AddEmptySegment(self.segment_name)


      # # Below will create a new segment if there are no segments in the segmentation node, avoid overwriting existing segments
      # if not self.srcSegmentation.GetSegmentIDs(): # if there are no segments in the segmentation node
      #   self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      #   self.segmentationNode.GetSegmentation().AddEmptySegment(self.segment_name)
      #
      # # if there are segments in the segmentation node, check if the segment name is already in the segmentation node
      # if any([self.segment_name in i for i in self.srcSegmentation.GetSegmentIDs()]):
      #       pass
      # else:
      #       self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      #       self.segmentationNode.GetSegmentation().AddEmptySegment(self.segment_name)

      print("MMMMMMMMMM newSegment after else become true",
            self.segmentationModified)


      print("self segment name", self.segment_name)

      # Make the new segment active for editing
      print("new segment editor widget \n")
      print("self segment name", self.segment_name)
      # print("self segmentationNode", self.segmentationNode)
      # self.segmentationNode.GetSegmentation().SetActiveSegmentID(self.segment_name)

      # Refresh the 3D view to visualize the changes
      # slicer.app.processEvents()

      #maxime add
      # segmentationNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLSegmentationNode")

      # # Set the segmentation node to the Segment Editor widget

      self.segmentEditorWidget.setSegmentationNode(self.segmentationNode)

      self.segmentEditorWidget.setCurrentSegmentID(self.segmentationNode)

      # print("segmentation id", segmentationNode.GetSegmentID())

      return self.segment_name


  def subjectHierarchy(self):

    print("IN SUBJECT HIERARCHY")

    # Get the subject hierarchy node
    shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
    # print(shNode)
    #
    # # print(" ** shNode", shNode)
    #
    # Get scene item ID first because it is the root item:
    sceneItemID = shNode.GetSceneItemID()

    # print("scene item ID", sceneItemID)

    # Get the scene item ID (check if the scene item exists)
    subjectItemID = shNode.GetItemChildWithName(shNode.GetSceneItemID(), self.currentCase)
    if not subjectItemID:
        subjectItemID = shNode.CreateSubjectItem(shNode.GetSceneItemID(), self.currentCase)

    print("subject item ID", subjectItemID)

    # TODO: this will need to be updated when moving to multiple studies per patient (or done in a separate script)
    # Creat a folder to include a study (if more than one study)
    # check if the folder exists and if not create it (avoid recreating a new one when reloading a mask)
    Study_name = 'Study to be updated'
    folderID = shNode.GetItemChildWithName(subjectItemID, Study_name)
    print("subject item id", subjectItemID)
    print("folder id", folderID)
    if not folderID:
        folderID = shNode.CreateFolderItem(subjectItemID, Study_name)
    # set under the subject
    shNode.SetItemParent(folderID, subjectItemID)

    # get all volume nodes
    VolumeNodes = slicer.util.getNodesByClass('vtkMRMLVolumeNode')
    VolumeNodeNames = [i.GetName() for i in VolumeNodes]

    print("VOlume node names", VolumeNodeNames)

    # Get all child (itemID = CT or MR series/sequences)
    for i in VolumeNodeNames:
        itemID = shNode.GetItemChildWithName(sceneItemID, i)
        shNode.SetItemParent(itemID, folderID)
    # same thing for segmentation nodes
    SegmentationNodes = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')
    SegmentationNodeNames = [i.GetName() for i in SegmentationNodes]

    self.segmentEditorWidget.setCurrentSegmentID(SegmentationNodes[0])

    # print("segmentation node names", SegmentationNodeNames)
    #
    # print("segmentation node", )
    #
    # childItemIDs = vtk.vtkIdList().GetNumberOfIds()
    # print("child item ids", childItemIDs)


    #TO SET THE SEGMENTAITON NODE AND SEGMENT
    # self.segmentEditorWidget.setSegmentationNode(segmentNode)
    # self.segmentEditorWidget.setCurrentSegmentID(segmentNodeName)


    print(" *****TESTING")
    # print(shNode)
    # print("SEGMENTATION NODES", SegmentationNodes[0].GetSegmentation())
    # print("SEGMENTATION NODES", SegmentationNodes[0].GetName())
    # print("SEGMENTATION IDS", SegmentationNodes[0].GetIDs())
    # print("SEGMENTATION IDS", SegmentationNodes[0].GetIDs())



    ###RENDU ICI
    ##ESSENTIELLEMENT = LOAD L'IMAGE  MAIS QUAND JANNOTE = MET





    # umIds = idList.GetNumberOfIds()
    # ids = [idList.GetId(i) for i in range(numIds)]
    # print("vtkIdList contains:", ids)


    # # move all segmentation nodes to the subject
    # for i in SegmentationNodeNames:
    #     itemID = shNode.GetItemChildWithName(sceneItemID, i)
    #     shNode.SetItemParent(itemID, folderID)
    # # print("shnode modif", shNode)

  def clean_hierarchy_folder(self):
      print(" ENTERING CLEAN_HIERARCHY FOLDER")
      # Get the subject hierarchy node
      subjectHierarchyNode = slicer.mrmlScene.GetSubjectHierarchyNode()

      # Get the folder item by name (replace 'NameOfFolder' with the actual folder name)
      folderItemID = subjectHierarchyNode.GetItemByName('Study to be updated')

      # Check if the folder item was found
      if folderItemID:
          # Get all child items (nodes) in the folder
          childItemIDs = vtk.vtkIdList()
          subjectHierarchyNode.GetItemChildren(folderItemID, childItemIDs)

          # Iterate over each child item and remove the corresponding node
          for i in range(childItemIDs.GetNumberOfIds()):
              childItemID = childItemIDs.GetId(i)
              node = subjectHierarchyNode.GetItemDataNode(childItemID)
              # volume_node = slicer.util.getNodesByClass('vtkMRMLVolumeNode')
              # print("volume node", volume_node)
              print("node", node)
              # Check if the node is a labelmap volume node
              if node and node.IsA('vtkMRMLLabelMapVolumeNode'):
                  # Remove the labelmap volume node
                  slicer.mrmlScene.RemoveNode(node)
      else:
          print("Folder not found")


  def onPushButton_segmeditor(self):
      print("IN PUSH BUTTON")
      slicer.util.selectModule("SegmentEditor")
      #mb testing
      print("module selection")
      # slicer.util.selectModule("Models")

  # def onNewLabelSegm(self, label_name, label_color_r, label_color_g, label_color_b, label_LB_HU, label_UB_HU):
  #     segment_name = self.newSegment(label_name)
  #     self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
  #     self.segmentationNode.UndoEnabledOn()
  #     Segmentation = self.segmentationNode.GetSegmentation()
  #     self.SegmentID = Segmentation.GetSegmentIdBySegmentName(segment_name)
  #     segment = Segmentation.GetSegment(self.SegmentID)
  #     segment.SetColor(label_color_r/255,label_color_g/255,label_color_b/255)
  #     self.onPushButton_select_label(segment_name, label_LB_HU, label_UB_HU)

  #maxime modif

  def onNewLabelSegm(self, segmentationNode, label_name, label_color_r,
                     label_color_g,
                     label_color_b, AssessSegmentationFlag=False):
      print("IN ON NEW LABEL SEG")
      print("label name", label_name)

      if AssessSegmentationFlag:
          # -12 to remove the extension Segmentation (keeping the _)
          segment_name = f"{segmentationNode.GetName()[:-12]}{label_name}{self.file_extension}"
          print("segment name in assess seg flag", segment_name)
      else:
          segment_name = self.newSegment(label_name)

      # segment_name = self.newSegment(label_name)
      # segment_name = f"{segmentationNode.GetName()}{label_name}{self.file_extension}"

      print("segment name", segment_name)
      print("rgb dans newlabel segm", label_color_r, label_color_g, label_color_b)
      # self.segmentationNode = segmentationNode

      # self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      # self.segmentationNode.UndoEnabledOn()
      # Segmentation = self.segmentationNode.GetSegmentation()
      # self.SegmentID = Segmentation.GetSegmentIdBySegmentName(segment_name)

      segmentationNode.UndoEnabledOn()
      Segmentation = segmentationNode.GetSegmentation()
      # self.SegmentID = Segmentation.GetSegmentIdBySegmentName(segment_name)
      SegmentID = Segmentation.GetSegmentIdBySegmentName(segment_name)





      print(" xxxxxxxxxxx new label seg id", SegmentID)

      segment = Segmentation.GetSegment(SegmentID)
      # segment = Segmentation.GetSegment(segment_name) maybe to try if not
      # working

      segment.SetColor(label_color_r/255,label_color_g/255,label_color_b/255)
      # self.onPushButton_select_label(segment_name)

  #maxime
  def onPushButton_select_label(self, segment_name,
                                segmentationNodeSpec=None):
      print("\n ENTERING oN PUSH BUTTON SELECT LABEL segment name")
      print(f"segment label select name: {segment_name}")
      print("segmentationnode spec", segmentationNodeSpec)
      # if segmentationNodeSpec != None:
      #     print("in if segmentaitnnode spec diff of none")
      #     self.segmentationNode = segmentationNodeSpec
      # else :
      #     print(" in else segmentaitno node == NOne")
      #     self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]

      Segmentation = self.segmentationNode.GetSegmentation()
      self.SegmentID = Segmentation.GetSegmentIdBySegmentName(segment_name)
      print("onPushButton_select_labe self segment ID", self.SegmentID)
      print("onPushButton_select_labe segment name", segment_name)
      self.segmentEditorNode.SetSelectedSegmentID(self.SegmentID)
      # print(" *** pusb ubutotn selec tlabel segment id", self.SegmentID)
      # print(" *** segment name in pusb butotn selct labewl", segment_name)
      # self.segment_name = segment_name
      self.updateCurrentSegmenationLabel()
      # self.LB_HU = label_LB_HU
      # self.UB_HU = label_UB_HU
      self.onPushButton_Paint()


      ###NEVER COMMENT THOSE LINES SINCE IT AFFECTS SELECTING LABEL BUTOTN
      # FUNCITON (makes the icon become unclickable)

      if (
              self.MostRecentPausedCasePath != self.currentCasePath and self.MostRecentPausedCasePath != ""):
          self.timers[self.current_label_index] = Timer(
              number=self.current_label_index)  # new path, new timer

      self.timer_router()

  # def onPushButton_select_label(self, segment_name, label_LB_HU, label_UB_HU):
  #     self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
  #     Segmentation = self.segmentationNode.GetSegmentation()
  #     self.SegmentID = Segmentation.GetSegmentIdBySegmentName(segment_name)
  #     self.segmentEditorNode.SetSelectedSegmentID(self.SegmentID)
  #     self.updateCurrentSegmenationLabel()
  #     self.LB_HU = label_LB_HU
  #     self.UB_HU = label_UB_HU
  #     self.onPushButton_Paint()
  #
  #     if (self.MostRecentPausedCasePath != self.currentCasePath and self.MostRecentPausedCasePath != ""):
  #       self.timers[self.current_label_index] = Timer(number=self.current_label_index) # new path, new timer
  #
  #     self.timer_router()

  # def onPushButton_SemiAutomaticPHE_Launch(self):
  #     flag_PHE_label_exists = False
  #     PHE_label = None
  #     PHE_label_index = 0
  #     for label in self.config_yaml["labels"]:
  #         if label["name"] == "PHE":
  #             flag_PHE_label_exists = True
  #             PHE_label = label
  #             break
  #         PHE_label_index = PHE_label_index + 1
  #     assert flag_PHE_label_exists
  #
  #     PHE_segment_name = f"{self.currentCase}_PHE"
  #     self.onPushButton_select_label(PHE_segment_name, PHE_label["lower_bound_HU"], PHE_label["upper_bound_HU"])
  #     self.ui.dropDownButton_label_select.setCurrentIndex(PHE_label_index)
  #     toolWindow = SemiAutoPheToolThresholdWindow(self)
  #     toolWindow.show()
      
  def onPushButton_SemiAutomaticPHE_ShowResult(self):
      print("\n ENTERING SEMI AUTOMATIC PHE SHOW RESULT \n")
      self.segmentationNode.GetDisplayNode().SetVisibility(True)
      self.onPushButton_Erase()
      self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(False)

  def ApplyThresholdPHE(self, inLB_HU, inUB_HU):
      print("\n ENTERING applyThreshold \n")
      self.segmentEditorWidget.setActiveEffectByName("Threshold")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("MinimumThreshold",f"{inLB_HU}")
      effect.setParameter("MaximumThreshold",f"{inUB_HU}")
      effect.self().onApply()

  def ApplySemiAutomaticThresholdAlgorithm(self):
      print("\n ENTERING applySemiAutomaticThresholdAlgorithm \n")
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

  # def ClearPHESegment(self):
  #     flag_PHE_label_exists = False
  #     PHE_label = None
  #     PHE_label_index = 0
  #     for label in self.config_yaml["labels"]:
  #         if label["name"] == "PHE":
  #             flag_PHE_label_exists = True
  #             PHE_label = label
  #             break
  #         PHE_label_index = PHE_label_index + 1
  #     assert flag_PHE_label_exists
  #
  #     segm_name = f"{self.currentCase}_PHE"
  #     self.srcSegmentation.RemoveSegment(segm_name)
  #     self.onNewLabelSegm(PHE_label["name"], PHE_label["color_r"], PHE_label["color_g"], PHE_label["color_b"], PHE_label["lower_bound_HU"], PHE_label["upper_bound_HU"])

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
  # MB DO NOT COMMENT THIS FUNCTION THIS SCRAPS SELECTING NODE
  def timer_router(self):
      #maxime
      # self.current_label_index = 0
      # print(" tes timer self curent label index : ", self.current_label_index)
      # print(" self timers", self.timers)
      # self.timers[0].start()
      self.timers[self.current_label_index].start()
      self.flag = True

      timer_index = 0
      for timer in self.timers:
          if timer_index != self.current_label_index:
              timer.stop()
          timer_index = timer_index + 1

  # def checkboxChanged(self):
  #     self.checked_ichtype = []
  #     self.checked_ichloc = []
  #     self.checked_ems = []
  #     for i in self.listichtype:
  #         if i.isChecked():
  #             ichtype = i.text
  #             self.checked_ichtype.append(ichtype)
  #     for j in self.listichloc:
  #         if j.isChecked():
  #             ichloc = j.text
  #             self.checked_ichloc.append(ichloc)
  #     for k in self.listEMs :
  #         if k.isChecked():
  #             em = k.text
  #             self.checked_ems.append(em)
  #     self.checked_ichtype = ';'.join(self.checked_ichtype)
  #     self.checked_ichloc = ';'.join(self.checked_ichloc)
  #     self.checked_ems = ';'.join(self.checked_ems)
  #     return self.checked_ichtype, self.checked_ichloc, self.checked_ems

  # def uncheckAllBoxes(self):
  #     self.allcheckboxes = self.listichtype + self.listichloc + self.listEMs
  #     for i in self.allcheckboxes:
  #         i.setChecked(False)

  def clearTexts(self):
      self.ui.ichtype_other.clear()
      self.ui.EM_comments.clear()


  #### SAVING FILES ####
  def createFolders(self):
      """
      Create the top output directory
      """
      print("\n ENTERING createFolders \n")
      self.revision_step = self.ui.RevisionStep.currentText
      if len(self.revision_step) != 0:
          # self.output_dir = os.path.join(self.CurrentFolder,
          #                                f'Output_{self.annotator_name}_{self.revision_step[0]}')  # only get the number

          #maxime
          ## add here to us this function to save a file csv or yaml in
          # output directory instead

          print("***SELF OUTPUT FOLDER PRINTED**", self.OutputFolder)

          #PUT A FUNCTION THAT CREATE A FILE INSTEAD!


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

  def onSaveSegmentationButton(self, direction=None):
      print("Save segmentation button clicked.")

      # Get the segmentation node (the current one)
      self.SegmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      # print("self segmentationNode", self.segmentationNode)

      # Get the volume node (the current one)
      self.VolumeNode = slicer.util.getNodesByClass('vtkMRMLVolumeNode')[0]

      # Get the label mal (signification? - mb added by chatgpt and works!
      self.labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
      # print("self label mao", self.labelmap_volume_node)
      slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(
          self.SegmentationNode, self.labelmapVolumeNode, self.VolumeNode)

      # Get the segments name
      self.SegmentsNames = self.SegmentationNode.GetSegmentation().GetSegmentIDs()

      print("self segment names", self.SegmentsNames)

      print("output folder", self.OutputFolder)

      # # Save each segmentation mask in the output folder
      # for element in self.SegmentsNames:
      #     print("elenent", element)
      #     print("path", f'{self.OutputFolder}{os.sep}{element}')
      #     slicer.util.saveNode(self.labelmapVolumeNode,
      #                          f'{self.OutputFolder}{os.sep}{element}')

      # # Save each segmentation mask in the versions output folder
      # for element in self.SegmentsNames:
      #     print("elenent", element)
      #     print("path", f'{self.OutputFolder}{os.sep}versions{os.sep}{element}')
      #     slicer.util.saveNode(self.labelmapVolumeNode,
      #                          f'{self.OutputFolder}{os.sep}versions{os.sep}{element}')

      segmentation_node = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      segmentation = segmentation_node.GetSegmentation()
      segment_ids = vtk.vtkStringArray()
      segmentation.GetSegmentIDs(segment_ids)
      print("segment IDS plus loins", segment_ids)

      for i in range(segment_ids.GetNumberOfValues()):

          segment_id = segment_ids.GetValue(i)
          segment = segmentation.GetSegment(segment_id)
          segment_name = segment.GetName()

          filename = self.remove_file_extension(segment_name)

          # filename = self.remove_file_extension(self.SegmentsNames[i])



          version = self.check_version(filename)
          version = self.increment_latest_version(filename)
          print("Check if folder version exists.", version)
          print("file name oN SAVE SEGMENTATION ", filename)


          segment_id = segment_ids.GetValue(i)

          print("\n onSaveSegmentationButton segment_id", segment_id)


          segment_name = segmentation.GetSegment(segment_id).GetName()
          print("\n onSaveSegmentationButton segment_name", segment_name)

          # Create a new labelmap volume node
          labelmap_volume_node = slicer.mrmlScene.AddNewNodeByClass(
              "vtkMRMLLabelMapVolumeNode", segment_name + "_labelmap")

          print("\n onSaveSegmentationButton label_map_volumenode",
                labelmap_volume_node)

          # print("\n onSaveSegmentationButton [segment_id]", vtk.vtkStringArray(segment_id)
          segment_id_array = vtk.vtkStringArray()
          segment_id_array.InsertNextValue(segment_id)
          print("segment id array", segment_id_array)




          # Export the segment to the labelmap volume node
          # slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(
          #     segmentation_node, vtk.vtkStringArray(segment_id),
          #     labelmap_volume_node)

          slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(
              segmentation_node, segment_id_array, labelmap_volume_node)

          #remove file extension to optimise the saving with a vesion control


          # # Construct the file path
          # file_path = os.path.join(f"{self.OutputFolder}{os.sep}versions{os.sep}",
          #                          f"{segment_name}")

          # # Construct the file path
          file_path = os.path.join(f"{self.OutputFolder}{os.sep}versions{os.sep}",
                                   f"{filename}{version}"
                                   f"{self.file_extension}")

          # Save the labelmap volume node
          slicer.util.saveNode(labelmap_volume_node, file_path)

          # Optionally, remove the labelmap volume node from the scene to free up memory
          slicer.mrmlScene.RemoveNode(labelmap_volume_node)

          print(f"Saved segment '{segment_name}' to file: {file_path}")

      print("onSaveSegmentationButton new saved worked!!!!")



      # # Save each segmentation mask in the versions output folder
      # for element in self.SegmentsNames:
      #     print("elenent", element)
      #     filename = self.remove_file_extension(element)
      #
      #     # version = self.check_version(filename)
      #     version = self.increment_latest_version(filename)
      #     print("Check if folder version exists.", version)
      #
      #     print("file name oN SAVE SEGMENTATION ", filename)
      #
      #     print("path", f'{self.OutputFolder}{os.sep}versions{os.sep}{element}')
      #
      #
      #
      #
      #     slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(
      #         segmentation_node, vtk.vtkStringArray([segment_id]),
      #         labelmap_volume_node)

          # slicer.util.saveNode(self.labelmapVolumeNode,
          #                      f'{self.OutputFolder}{os.sep}versions{os.sep}'
          #                      f'{filename}{version}{self.file_extension}')

      #here some adjustements will be needed since when load it considers as
      # volume and to put in derivatives

      # # ON HOLD FOR NOW generate qc report
      ###mathieu suggestion in sctmeeting : Env pour 3d slcier dans le terminal pour executer sheell scirpt
      ###go see folder agenda sct meeting for qc
      # print("qc report to be generated")
      # print("self extension directory", self.EXTENSION_DIR)
      # shell_script = (f"{self.EXTENSION_DIR}{os.sep}bin/from_sct_qc.sh")
      # # shell_script = (f"{self.EXTENSION_DIR}{os.sep}bin/from_sct_qc.sh 'jacques' ")
      # #make sure you have the permission to execute the shell script
      # # Execute the shell script
      # # result = subprocess.run([shell_script], capture_output=True, text=True)
      #
      # # background_image
      # # volumeNode = slicer.util.getNode('MRHead')
      # print("******volume node: ", self.VolumeNode)
      # # background_image_path = self.VolumeNode.GetStorageNode().GetFileName()
      # print("storage node:", self.VolumeNode.GetStorageNode().GetFileName())
      # bg_image = self.VolumeNode.GetStorageNode().GetFileName()
      #
      # #name of the current segment
      # segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      # selectedSegmentID = segmentEditorWidget.mrmlSegmentEditorNode().GetSelectedSegmentID()
      # print("name of the current segment:", selectedSegmentID)
      # # current segment node path (mask)
      # current_segment_path = f'{self.OutputFolder}{os.sep}{selectedSegmentID}.nii.gz'
      # print("current segment path", current_segment_path)
      #
      # #path of the current roi segmentation
      # #please note that this works only for bids (always 10 characters for
      # # subject naming)
      # labels_path = f'{self.CurrentFolder}{os.sep}derivatives{os.sep}labels'
      #
      #
      # ##ATTENTION! INSTEAD OF USING :10 WE COULD USE PARSE FUNCTION TO
      # # DELIMITATE WITH THE SUBJECT NAME
      # subject_name = f'{self.currentCase}'[:10]
      # print("subject name", subject_name)
      # print("type subject name", type(subject_name))
      # current_roi = (f'{labels_path}{os.sep}{subject_name}{os.sep}anat'
      #                f'{os.sep}{self.VolumeNode.GetName()}_seg.nii.gz')
      # print("path current roi segmentation:", current_roi)
      #
      #
      # #path of output file (from the shell script to run)
      # output_folder = self.OutputFolder
      # print("path output file", output_folder)
      #
      # result = subprocess.run([shell_script, bg_image,
      #                          current_segment_path, current_roi, output_folder],
      #                         capture_output=True,
      #                         text=True)
      #
      # # Print the output and error (if any)
      # print("stdout:", result.stdout)
      # print("stderr:", result.stderr)
      # print("Return code:", result.returncode)

      # save a csv file with statistics
      self.annotator_name = self.ui.Annotator_name.text
      self.annotator_degree = self.ui.AnnotatorDegree.currentText
      self.revision_step = self.ui.RevisionStep.currentText

      print("about to write csv function")
      print(" get segmentation name", self.SegmentationNode.GetName())
      print(" get annotator_name", self.annotator_name)
      print(" get annotator_degree", self.annotator_degree)
      print("get revision step", self.revision_step)


      # helped by ChatGPT
      # Actual variables [formated in list for convenient purposes].
      Case_number = [self.SegmentationNode.GetName()]
      Annotator_name = [self.annotator_name]
      Annotator_degree = [self.annotator_degree]
      Revision_step = [self.revision_step]
      csv_name = 'metadata.csv' #by default. Can be changed by user.

      # Combine data into rows using zip
      data = list(
          zip(Case_number, Annotator_name, Annotator_degree, Revision_step))

      # Create the folder if it does not exist
      os.makedirs(self.OutputFolder, exist_ok=True)
      # Define the complete file path
      csv_path = os.path.join(self.OutputFolder, csv_name)
      # Check if the file already exists
      csv_exists = os.path.isfile(csv_path)

      # Write in csv file or add new data
      with open(csv_path, mode='a', newline='', encoding='utf-8') as file:
          writer = csv.writer(file)
          # Write header only if the file does not already exist
          if not csv_exists:
              writer.writerow(
                  ['Case number', 'Annotator Name', 'Annotator Degree',
                   'Revision Step'])

          # Write data rows
          for row in data:
              writer.writerow(row)

      # add a comment box

      # #Get the remaining cases and save them in a yaml file (copied in select
      # # output folder ufnction)

      #go to next case to segment

      # print("going to the next case")
      # self.segmentationModified = False
      # if direction == "Previous":
      #     if self.currentCase_index == 0:
      #         print("*** This is the first case of the list. ***")
      #         self.show_message_box("This is the first case of the list.")
      #     else :
      #         self.onPreviousButton()
      # else :
      #     if self.currentCase_index == (len(self.allCases) - 1):
      #         print("*** This is the last case of the list. ***")
      #         self.show_message_box("This is the last case of the list.")
      #     else :
      #       self.onNextButton()

      # Update the remainingCasesYAML

      # Load the YAML file
      # with open(self.RemainingCases, 'r') as file:
      #     remainingCasesYAML = yaml.safe_load(file)
      #     print(remainingCasesYAML['FILES_SEG'])
      #     remainingCasesYAML['FILES_SEG'].pop(0)
      #     print(remainingCasesYAML['FILES_SEG'])
      # self.RemainingCases



      with open(self.RemainingCases, 'r') as file:
          data = yaml.safe_load(file)
          print("data, data", data)
          self.yamlListName = data['FILES_SEG']
          print("len yamlList name in with open", len(self.yamlListName))
          print("list yaml name", self.yamlListName)
          self.yamlListPath = []
          for i in range(len(self.yamlListName)):
              for element in self.allCasesPath:
                  if self.yamlListName[i] in element:
                      self.yamlListPath.append(element)
          print("for loop worked!!!****")
          print("len yamlListPath", len(self.yamlListPath))

      print("data file seg before entering if", data['FILES_SEG'] )
      print("self.currentCase and boolean", self.currentCase)
      print(self.currentCase in data['FILES_SEG'])
      print("len data", len(data['FILES_SEG']))

      index_case_to_modify = self.allCases.index(self.currentCase)
      print("index_case_to modify ", index_case_to_modify)

      correspondingIndex = self.get_corresponding_index()
      print("checkinf if first or last")
      if (correspondingIndex[0] == 0) or (correspondingIndex[0] == len(
              self.allCases)-1): #check if first or last case
          print("first or last")
          self.currentCaseModified = self.allCases[correspondingIndex[0]]
          print("sel current cas emodified i index 0", self.currentCaseModified)
          print("self current case should be the same", self.currentCase)

          self.currentCasePathModified = self.allCasesPath[correspondingIndex[0]]
          print("current case path modified i 0", self.currentCasePathModified)

      else:
          self.currentCaseModified = self.allCases[correspondingIndex[0]]
          print("sel current cas emodified i index else",
                self.currentCaseModified)
          print("self current case should be the same", self.currentCase)

          self.currentCasePathModified = self.allCasesPath[
              correspondingIndex[0]]
          print("current case path modified else", self.currentCasePathModified)


      if self.currentCaseModified in data['FILES_SEG']:
          print("self currenCase in data file seg", self.currentCaseModified)
          print("***************************\n")
          print(" len data file seg", len(data['FILES_SEG']))
          # data['FILES_SEG'].remove(self.currentCase)
          print("self currentCase", self.currentCaseModified)
          print("self currentCasePath", self.currentCasePathModified)
          print("corresponding index [1[]", correspondingIndex[1])
          print("self yaml listname before not finding", self.yamlListName)
          print("len yaml listname", len(self.yamlListName))
          self.indexYaml = correspondingIndex[1]
          # self.indexYaml = self.yamlListName.index(self.currentCaseModified)
          print("self indexYaml before", self.indexYaml)
          self.yamlListPath.remove(self.currentCasePathModified)
          self.yamlListName.remove(self.currentCaseModified)
          data['FILES_SEG'] = self.yamlListName
          print("data file seg **", data['FILES_SEG'])
          print("self index yaml before cheks", self.indexYaml)
          print("len yamlListName", len(self.yamlListName))
          if data['FILES_SEG'] == []:
              print("empty list")
              self.generate_message_box("There is no remaining cases.")
              self.indexYaml = -1
              self.currentCase_index = -1
              self.yamlListPath = []
              # self.currentCasePath = self.allCasesPath[0]
              # self.currentCase =

          elif self.indexYaml >= len(self.yamlListName)-1:

              # means that you were on the last case
              print("that means you were on the last case")
              self.indexYaml = len(self.yamlListName)-1
              # self.currentCase_index = 0
              self.generate_message_box("Last case in remaininCases has been "
                                        "segmented. \nGoing to the last case in the remaining list.")

          else :
              print("entering else meaning not empty list")
              print("self indexYaml after", self.indexYaml)
              print("len yaml listname after", len(self.yamlListName))
              self.nameYaml = self.yamlListName[self.indexYaml]
              print("self name Yaml", self.nameYaml)
              self.currentCase_index = self.allCases.index(self.nameYaml)
              print("self current indez cas after", self.currentCase_index)
              # self.currentCase_index = self.currentCaseModified
              print("***************************\n")
      else :
          # file not found in yaml list
        print("else pass in save seg")
        print("correspdongin index -1?", correspondingIndex[1])

      # if index_case_to_modify == len(self.allCases)-1: ###HERE SSATURDAY
      #     print("last case")
      #     self.currentCaseModified = self.allCases[index_case_to_modify]
      #     print("self currentCase modified", self.currentCaseModified)
      #     index_path_to_modify = self.allCasesPath.index(self.currentCasePath)
      #     self.currentCasePathModified = self.allCasesPath[
      #         index_path_to_modify]
      #     print("current case path modified", self.currentCasePathModified)
      # else :
      #     if index_case_to_modify == 0:
      #         pass
      #
      #     self.currentCaseModified = self.allCases[index_case_to_modify-1]
      #     print("self currentCase modified", self.currentCaseModified)
      #     index_path_to_modify = self.allCasesPath.index(self.currentCasePath)
      #     self.currentCasePathModified = self.allCasesPath[index_path_to_modify-1]
      #     print("current case path modified", self.currentCasePathModified)
      #     # self.currentCaseModified = self.allCases[index_case_to_modify-1]
      #     # print("self currentCase modified", self.currentCaseModified)
      #     # index_path_to_modify = self.allCasesPath.index(self.currentCasePath)
      #     # self.currentCasePathModified = self.allCasesPath[index_path_to_modify-1]
      #     # print("current case path modified", self.currentCasePathModified)


      # if self.currentCase in data['FILES_SEG']:
      #     print("self currenCase in data file seg", self.currentCase)
      #     print("***************************\n")
      #     print(" len data file seg", len(data['FILES_SEG']))
      #     # data['FILES_SEG'].remove(self.currentCase)
      #     print("self currentCase", self.currentCase)
      #     print("self currentCasePath", self.currentCasePath)
      #     self.indexYaml = self.yamlListName.index(self.currentCase)
      #     print("self indexYaml before", self.indexYaml)
      #     self.yamlListPath.remove(self.currentCasePath)
      #     self.yamlListName.remove(self.currentCase)
      #     data['FILES_SEG'] = self.yamlListName
      #     print("self indexYaml after", self.indexYaml)
      #
      #     self.nameYaml = self.yamlListName[self.indexYaml]
      #     print("self name Yaml", self.nameYaml)
      #     self.currentCase_index = self.allCases.index(self.nameYaml)
      #     print("self current indez cas after", self.currentCase_index)
      #     self.currentCase_index = self.currentCase_index - 1
      #     print("***************************\n")

          # self.indexYaml =

          # new_index = self.currentCase

      # if 'FILES_SEG' in data and isinstance(data['FILES_SEG'], list) and data['FILES_SEG']:
      #     data['FILES_SEG'].pop(0)

      with open(self.RemainingCases, 'w') as file:
          print("in write remaining cases", data)
          print(" len data file seg after", len(data['FILES_SEG']))

          yaml.dump(data, file, default_flow_style=False)




      print("Should be completed")

      print("going to the next case")
      self.segmentationModified = False
      if direction == "Previous":
          if self.currentCase_index == 0:
              print("*** This is the first case of the list. ***")
              self.show_message_box("This is the first case of the list.")
          else:
              self.onPreviousButton()
      else:
          if self.currentCase_index == (len(self.allCases) - 1):
              print("*** This is the last case of the list. ***")
              self.show_message_box("This is the last case of the list.")
          else:
              self.onNextButton()

      # Open a new segmentation editor optimizedd

      self.onCreateSegmentationButton()

      #NOW HERE
      #NEXT STEPS ARE TO MANAGE SEGMENTATION MASKS ACCORDING TO CONFIG FILE
      # RE-ARRANGE TO MAKE THE MASK LOADING OK AND NOT HAVING TO RE-ARRANGE
      #INPUT SOME CONFIG PARAMETERS IN CONFIG FILE
      # MANAGE COMMENT BOX
      # MANAGE TIMER FOR EACH CASE
      # MAKE MANDATORY TO WRITE ANNOTATOR NAME ETC.
      # RE-ORGANIZE THE GUI
      # MAKE A BUTTON TO LOAD MASKS AND ASSOCIATE THEM TO VOLUME
      # CREATE KEYBOARD SHORTCUT AND AUTOMATIC DISPLAY OF SCREEN
      # TRY TO RE-ARRANGE THE GUI
      #CORRET EXTENSION NAME AND CODE ASSOCIATED

      # print("remainingCasesYAML", remainingCasesYAML)
      # print("type", type(remainingCasesYAML))
      #
      # # Extract the first element from the 'FILES_SEG' list
      # nextCase = remainingCasesYAML['FILES_SEG'][0] if ('FILES_SEG' in remainingCasesYAML and remainingCasesYAML['FILES_SEG']) else None
      # print("next case", nextCase)



      #pay attention to not rewrite csv file with data

      #add a box to put ocmments an save it in csv
      #add a button to falg the case
      #consider if case not flaged if revision step is 2 or 3

      # #test execute python file
      # script_path = '/Users/maximebouthillier/gitmax/code/dr_letourneau/ICH_SEGMENTER_V2/testingmaxime/test_script_other.py'
      # # Get the path to the Slicer Python executable
      # python_executable = sys.executable
      # def execute_script_in_folder(script_path):
      #     # Execute the script in the specified folder
      #     print("now in the executive function")
      #     result = subprocess.run([python_executable, script_path],
      #                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      #     if result.stdout:
      #         print("Standard output:")
      #         print(result.stdout.decode())  # Decode bytes to string
      #     if result.stderr:
      #         print("Standard error:")
      #         print(result.stderr.decode())  # Decode bytes to string
      #
      # execute_script_in_folder(script_path)
      #
      # self.createFolders()
      #
      #
      #
      # #TODO: refactor this methods and it is way too long
      # self.time = self.stopTimer()
      # for timer in self.timers:
      #       timer.stop()
      # self.annotator_name = self.ui.Annotator_name.text
      # self.annotator_degree = self.ui.AnnotatorDegree.currentText
      #
      # #maxime
      # output_file_pt_id_instanceUid = \
      # re.findall(self.VOL_REGEX_PATTERN_PT_ID_INSTUID_SAVE,
      #            os.path.basename(self.currentCasePath))[0]
      # print("*********************output file pt id instance Uid ******",
      #       output_file_pt_id_instanceUid)
      # # output_file_pt_id_instanceUid = re.findall(self.VOL_REGEX_PATTERN_PT_ID_INSTUID_SAVE,os.path.basename(self.currentCasePath))[0]
      #
      #
      # #### CHECKBOX SAVING - TO BE REFACTORED ####
      # # get ICH types and locations
      # # self.checked_ichtype, self.checked_icvhloc, self.checked_ems = self.checkboxChanged()
      # # self.ichtype_other = self.ui.ichtype_other.text
      # # self.em_comments = self.ui.EM_comments.text
      #
      # # Create folders if not exist
      # self.createFolders()
      #
      # # Run the code to remove outliers
      # print('*** Running outlier removal ***')
      # self.check_for_outlier_labels()
      #
      # # Get the segmentation node (the current one)
      # self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      #
      # #### SAVING CSV TIME #####
      # # Save if annotator_name is not empty and timer started:
      # if self.annotator_name and self.time is not None:
      #     # Save time to csv
      #     print("Saving time to csv")
      #     tag_str = "Case number, Annotator Name, Annotator degree, Revision step, Time"
      #     for label in self.config_yaml["labels"]:
      #           tag_str = tag_str + ", " + label["name"] + " time"
      #     if self.flag_ICH_in_labels:
      #           tag_str = tag_str + ", ICH type, ICH location, Expansion markers, Other ICH type, Other expansion markers"
      #     print('constructing data string')
      #     # TODO: refactor this to be more generic and use the config file values.
      #     data_str = self.currentCase
      #     data_str = data_str + ", " + self.annotator_name
      #     data_str = data_str + ", " + self.annotator_degree
      #     data_str = data_str + ", " + self.revision_step[0]
      #     data_str = data_str + ", " + str(self.ui.lcdNumber.value)
      #     for timer in self.timers:
      #           data_str = data_str + ", " + str(timer.total_time)
      #     if self.flag_ICH_in_labels:
      #           data_str = data_str + ", " + self.checked_ichtype
      #           data_str = data_str + ", " + self.checked_ichloc
      #           data_str = data_str + ", " + self.checked_ems
      #           data_str = data_str + ", " + self.ichtype_other
      #           data_str = data_str + ", " + self.em_comments
      #
      #     self.outputTimeFile = os.path.join(self.output_dir, 'annotation times',
      #                                        '{}_Case_{}_time_{}.csv'.format(self.annotator_name, output_file_pt_id_instanceUid, self.revision_step[0]))
      #     print(f'line 961 - outputTimeFile: {self.outputTimeFile}')
      #     time_folder = os.path.dirname(self.outputTimeFile)
      #
      #     if not os.path.exists(time_folder):
      #         print("Creating directory: ", time_folder)
      #         os.makedirs(time_folder)
      #
      #     if not os.path.isfile(self.outputTimeFile):
      #         with open(self.outputTimeFile, 'w') as f:
      #             f.write(tag_str)
      #             f.write("\n")
      #             f.write(data_str)
      #     else:
      #         with open(self.outputTimeFile, 'a') as f:
      #             f.write("\n")
      #             f.write(data_str)
      #
      #
      #     ### SAVING SEGMENTATION FILES ####
      #
      #     # self.outputSegmFile = os.path.join(self.output_dir,'segmentations',
      #     #                                        "{}_{}_{}.seg.nrrd".format(output_file_pt_id_instanceUid, self.annotator_name, self.revision_step[0]))
      #
      #     #maxime
      #     self.outputSegmFile = self.OutputFolder
      #     print("output file worked")
      #
      #     print(f'line 980 - outputTimeFile: {self.outputTimeFile}')
      #     print(f'Saving segmentation to {self.outputSegmFile}')
      #
      #     # get the directory of the output segmentation file (needed in the method to check for remaining labels)
      #     self.output_seg_dir = os.path.dirname(self.outputSegmFile)
      #     print(f'output_seg_dir: {self.output_seg_dir}')
      #     if not self.output_seg_dir:
      #         os.makedirs(self.output_seg_dir)
      #
      #     self.save_node_with_isfile_check_qt_msg_box(self.outputSegmFile, self.segmentationNode)
      #
      #     # reloading the .seg.nrrd file and check if the label name : value match
      #     self.check_match_label_name_value()
      #
      # # If annotator_name empty or timer not started.
      # else:
      #     if not self.annotator_name:
      #         msgboxtime = qt.QMessageBox()
      #         msgboxtime.setText("Segmentation not saved : no annotator name !  \n Please save again with your name!")
      #         msgboxtime.exec()
      #     elif self.time is None:
      #         msgboxtime2 = qt.QMessageBox()
      #         msgboxtime2.setText("Error: timer is not started for some unknown reason. Restart and save again. File not saved!")
      #         msgboxtime2.exec()
      #
      #
      # # Save volumes
      # self.save_statistics()
      # # Update the color of the segment
      # self.update_current_case_paths_by_segmented_volumes()

  # def adjust_index(self, index_removed):
  #     self.allCases
  #     self.allCasesPath
  #
  #     self.yamlListName
  #     self.yamlListPath
  #
  #     #find index in allCases
  #     appropriate_index = self.allCases.index(self.yamlListName[index_removed])
  #     print("appropriate_index", appropriate_index)
  #     return appropriate_index

  def get_corresponding_index(self):
      if self.currentCase:
          allCasesIndex = self.allCases.index(self.currentCase)
          if self.currentCase in self.yamlListName:
              yamlListIndex = self.yamlListName.index(self.currentCase)
          else:
              yamlListIndex = -1
          print("\n ******* \n ")
          print("verifications corresponding index", self.currentCase)
          print("allCasesIndex", allCasesIndex)
          print("yamlListIndex", yamlListIndex)
          return (allCasesIndex, yamlListIndex)

  def get_path_from_name(self, currentCase):
      print("in get_path_from_name")
      print("current case", self.currentCase)
      for element in self.allCasesPath:
          if currentCase in element:
              print("element (the path)", element)
              return element


  def remove_file_extension(self, file_path):
      print(" ENTERING remove file extension")
      filename = file_path.split('.')[0]
      print("filename=", filename)
      return filename

  def remove_version_extension(self, filename):
      print(" ENTERING remove version extension")
      filename = filename[:-4]
      return filename

  def remove_label_extension(self, filename, list_of_labels):
      print(" ENTERING remove label extension")
      for i in range(len(list_of_labels)):
          if list_of_labels[i] in filename:
              return filename.replace(list_of_labels[i], "")



  def check_version_folder(self):
      if os.path.exists(f'{self.OutputFolder}{os.sep}versions'):
          print("folder version exists")
          return True
      else :
          print("folder version does not exist")
          return False

  def check_ref_folder(self):
      if os.path.exists(f"{self.GTFolder}"):
          print("folder version exists")
          return True
      else:
          print("folder version does not exist")
          return False

  def check_version(self, filename):
      folder_version = self.check_version_folder()
      version = "_v01"
      if folder_version:
          print("\n ttttt NEEDS SCAN FOR VERSION \n")
          version = self.get_latest_version(filename)

      return version

  def check_version_ref(self, filename):
      folder_ref = self.check_ref_folder()
      version = "_v01"
      if folder_ref:
          print("\n ttttt NEEDS SCAN FOR VERSION \n")
          version = self.get_latest_version_ref(filename)

      return version

  #maxime for loading labelmap
  def get_existing_segment(self):
      filename = self.remove_file_extension(self.segment_name)
      print("get_list_segment filename", filename)
      version = self.get_latest_version(filename)
      print("get_list_segment get latest version", version)
      if version == 0:
          print("get_list_segment version ==0 ")
          return False
      return True

  def create_vtk_segment(self):
      # Creates a vtk object from an existing already saved segment.
      # Load Binary Label Map
      filename = self.remove_file_extension(self.segment_name)
      print("get_list_segment filename", filename)
      version = self.format_latest_version(filename)
      print("create vtk segment , version", version)
      segment_path = (f"{self.OutputFolder}{os.sep}versions{os.sep}{filename}"
                      f"{version}{self.file_extension}")
      print("create_vtk_segmen segment_path", segment_path)

      # # self.segment_name
      labelmap_node = slicer.util.loadLabelVolume(segment_path)
      # print("labelmap node in os path exist segment", labelmap_node)

      # if success:  # RENDU ICI 27 MAI 2024

      print("create_vtk_segment labelmap node 1", labelmap_node)
      print("create_vtk_segment labelmap node type", type(labelmap_node))

      # Create a new segment
      # segment = slicer.vtkSegment()
      # segment.SetName('MyLoadedSegment')

      print("create vtk segment segment created and name set")

      # # Convert the label map volume node to a binary labelmap representation
      # segmentationLogic = slicer.modules.segmentations.logic()
      #
      # print("segment logic applied")
      #
      # binaryLabelmap = slicer.vtkOrientedImageData()


      # print("binary labelmap created", binaryLabelmap)

      slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(
          labelmap_node, self.segmentationNode)

      # Get the segmentation node
      segmentation = self.segmentationNode.GetSegmentation()
      print("create vtk ; print segmentation", segmentation)

      # Get the segment IDs
      segmentIDs = vtk.vtkStringArray()
      print("create vtk segment segmentIDs vtk string array", segmentIDs)
      segmentation.GetSegmentIDs(segmentIDs)
      print("segment get segment ids after adding segments",
            segmentation)

      # Set the name for each segment
      print("set name len of segment", segmentIDs.GetNumberOfValues())
      segmentID = segmentIDs.GetValue((segmentIDs.GetNumberOfValues()-1))
      print("segmentID after setted", segmentID)
      segment = segmentation.GetSegment(segmentID)
      print("semgnet affetr setted", segment)
      segmentName = f"{self.segment_name}"
      print("segmentName", segmentName)# Customize the name as needed
      segment.SetName(segmentName)
      # segment.SetID(segmentName)
      print("segmentation after renaming", segmentation)

      # slicer.mrmlScene.RemoveNode(labelmap_node)




      # # Set the name for each segment
      # print("set name len of segment", segmentIDs.GetNumberOfValues())
      # segmentID = self.segment_name
      # segment = segmentation.GetSegment(segmentID)
      # print("segment,", segment)
      # # segmentName = f"{self.segment_name}"
      # # print("segmentName", segmentName)# Customize the name as needed
      # print("self segment_name", self.segment_name)
      # segment.SetName(self.segment_name)

      # # Set the name for each segment
      # print("set name len of segment", segmentIDs.GetNumberOfValues())
      # for i in range(segmentIDs.GetNumberOfValues()):
      #     segmentID = segmentIDs.GetValue(i)
      #     segment = segmentation.GetSegment(segmentID)
      #     segmentName = f"{self.segment_name}"
      #     print("segmentName", segmentName)# Customize the name as needed
      #     segment.SetName(segmentName)

      # segmentationLogic.CreateOrientedImageDataFromVolumeNode(
      #     labelmap_node, transformNode)

      print("segmentation logic applied 2")

      # Add the binary labelmap to the segment
      # segment.AddRepresentation(
      #     slicer.vtkSegmentationConverter.GetBinaryLabelmapRepresentationName(),
      #     binaryLabelmap)
      #
      # print("create vtk segment , segment", segment)

      # return segment










  # def get_latest_version(self, filename):
  #     elements = os.listdir(f'{self.OutputFolder}{os.sep}versions')
  #     list_version = []
  #     version = "01"
  #     for element in elements:
  #         element = element[:-len(self.config_yaml["volume_extension"])]
  #         print(" filename in get_latest_version", filename)
  #         print(" get latest version element", element)
  #         if filename in element:
  #             list_version.append(int(element[-2:]))
  #
  #     print(" ttttt list version", list_version)
  #
  #     if list_version == []:
  #         return f"_v{version}"
  #     else :
  #         max_version = max(list_version)
  #         print("max list_version before increment", max_version)
  #         return f"_v{(max_version + 1):02d}"
  #

  # Get list_of_versions
  def get_list_of_versions(self, filename):
      list_version = []
      if os.path.exists(f'{self.OutputFolder}{os.sep}versions'):
          elements = os.listdir(f'{self.OutputFolder}{os.sep}versions')
          for element in elements:
              element = element[:-len(self.config_yaml["volume_extension"])]
              print(" filename in get_list_of_version", filename)
              print(" get list of version element", element)
              if filename in element:
                  list_version.append(int(element[-2:]))

      print(" ttttt list version", list_version)
      return list_version

  def get_list_of_versions_ref(self, filename):
      list_version = []
      if os.path.exists(f'{self.GTFolder}'):
          elements = os.listdir(f'{self.GTFolder}')
          for element in elements:
              element = element[:-len(self.config_yaml["volume_extension"])]
              print(" filename in get_list_of_version", filename)
              print(" get list of version element", element)
              if filename in element:
                  list_version.append(int(element[-2:]))

      print(" ttttt list version", list_version)
      return list_version



  # def get_all_files(self):
  #     print(" ENTERING et_all_files")
  #     # all_files = sorted(glob(f'{self.OutputFolder}{os.sep}versions{os.sep}'))
  #     versions_folder = os.path.join(self.OutputFolder, 'versions')
  #     pattern = os.path.join(versions_folder,'*')  # Adjust pattern to match files
  #     all_files = sorted(glob(pattern))
  #     print("all_file", all_files)
  #     print("len all file", len(all_files))
  #     return all_files

  def get_all_labels(self):
      print("Entering get_all_labels")
      list_of_labels = []

      for i in range(len(self.config_yaml["labels"])):
          print(self.config_yaml["labels"][i]["name"])
          list_of_labels.append(self.config_yaml["labels"][i]["name"])
          # print("type", type(self.config_yaml["labels"][i]))
      return list_of_labels






  def get_all_files_versions(self, max_version=None):
      print(" ENTERING et_all_files")
      versions_folder = os.path.join(self.OutputFolder, 'versions')
      pattern = os.path.join(versions_folder,'*')  # Adjust pattern to match files
      # all_files = sorted(glob(pattern))
      all_files = glob(pattern)
      print("all_file", all_files)
      print("len all file", len(all_files))
      print("max version", max_version)
      print("self config yamel labels", self.config_yaml["labels"])
      print("type self config", type(self.config_yaml["labels"]))

      list_of_labels = self.get_all_labels()

      # for i in range(len(self.config_yaml["labels"])):
      #     print(self.config_yaml["labels"][i]["name"])
      #     list_of_labels.append(self.config_yaml["labels"][i]["name"])
      #     # print("type", type(self.config_yaml["labels"][i]))

      print("list of labels", list_of_labels)
      print("all files", all_files)

      # Sort the all files list so that the list returned has the element in
      # the same order as compared to the label list (order) from the config
      # file

      all_files_label_sorted = []
      for label in list_of_labels:
          for version in range(max_version):
              for element in all_files:
                  if (label in element) and (
                          f"_v{(version + 1):02d}" in element):
                      # print(element)
                      all_files_label_sorted.append(element)

      print("all files label sorted", all_files_label_sorted)

      print("self config yaml", self.config_yaml["labels"])

      versions_dict = {}
      for i in range(max_version):
          list_of_files = []
          for element in all_files_label_sorted:
              if f"_v{(i + 1):02d}" in element:
                  print("all file[i] found", all_files_label_sorted[i])
                  list_of_files.append(element)
                  versions_dict[f"_v{(i + 1):02d}"] = list_of_files

              # versions_dict[f"_v{(i + 1):02d}"] = list_of_files.append(all_files[i])

      print("versions_dict", versions_dict)


      return versions_dict

  # Load versions
  def load_version(self, versions_dict, name_of_items):
      print(" ENTERING load_version")
      list_version_to_load = versions_dict[f"_{name_of_items}"]
      print("versions_dict item", list_version_to_load)
      print("load version", name_of_items) #ex v01 (what appears on the button)
      list_of_labels = self.get_all_labels()
      for segment_version_path in list_version_to_load:
          print("segment_version", segment_version_path)
          labelmap_node = slicer.util.loadLabelVolume(segment_version_path)
          print("create_vtk_segment labelmap node 1", labelmap_node)
          print("create_vtk_segment labelmap node type", type(labelmap_node))
          slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(
              labelmap_node, self.segmentationNode)
          print("verify importation segment to segmentation node")

          # Get the segmentation node
          segmentation = self.segmentationNode.GetSegmentation()
          print("create vtk ; print segmentation", segmentation)

          # Get the segment IDs
          segmentIDs = vtk.vtkStringArray()
          print("create vtk segment segmentIDs vtk string array", segmentIDs)
          segmentation.GetSegmentIDs(segmentIDs)
          print("segment get segment ids after adding segments",
                segmentation)

          # Set the name for each segment
          print("set name len of segment", segmentIDs.GetNumberOfValues())
          segmentID = segmentIDs.GetValue((segmentIDs.GetNumberOfValues() - 1))
          print("segmentID after setted", segmentID)
          segment = segmentation.GetSegment(segmentID)
          print("semgnet affetr setted", segment)
          for i in range(len(list_of_labels)):
              if list_of_labels[i] in segment_version_path:
                  label = list_of_labels[i]
                  break
              else :
                  label=None
          # i = list_version_to_load.index(segment_version_path)
          segmentName = f"{name_of_items}_{label}"
          print("segmentName", segmentName)  # Customize the name as needed
          segment.SetName(segmentName)
          # segment.SetID(segmentName)
          print("segmentation after renaming", segmentation)

      self.segmentationNode.Modified()
      self.subjectHierarchy()
      self.clean_hierarchy_folder()

  def unload_version(self, versions_dict, name_of_items):
      print(" ENTERING unload_version")
      list_version_to_unload = versions_dict[f"_{name_of_items}"]
      print("versions_dict item", list_version_to_unload)
      list_of_labels = self.get_all_labels()

      # Get the segmentation node
      segmentation = self.segmentationNode.GetSegmentation()

      # Get the segment IDs
      segmentIDs = vtk.vtkStringArray()
      segmentation.GetSegmentIDs(segmentIDs)
      print("segmentation get segmentIDS", segmentIDs)

      number_of_values = segmentIDs.GetNumberOfValues()
      # Iterate through all segments and print their names
      for i in range(number_of_values):
          segmentID = segmentIDs.GetValue(i)
          segment = segmentation.GetSegment(segmentID)
          segmentName = segment.GetName()
          print(f"Segment ID: {segmentID}, Segment Name: {segmentName}")
          for label in list_of_labels:
              if f"{name_of_items}_{label}" == segmentName:
                  segmentation.RemoveSegment(segmentID)

      self.segmentationNode.Modified()
      self.subjectHierarchy()
      self.clean_hierarchy_folder()

  # Set a color to the segments to a specific corresponding version, inspired
  # from the previous one
  def set_color_version(self):
      pass

  #Return an integer
  def get_latest_version_ref(self, filename):
      version = 0
      list_version = self.get_list_of_versions_ref(filename)
      if list_version == []:
          return version
      else:
          max_version = max(list_version)
          max_version = min(max_version,
                            98)  # to prevent exceeding 99 versions.
          print("max list_version before increment", max_version)
          return max_version


  #Return an integer
  def get_latest_version(self, filename):

      #could implement the paragraph below in new function to get all
      # versions of a specific file

      # list_version = []
      version = 0
      list_version = self.get_list_of_versions(filename)
      # if os.path.exists(f'{self.OutputFolder}{os.sep}versions'):
      #   elements = os.listdir(f'{self.OutputFolder}{os.sep}versions')
      #   for element in elements:
      #     element = element[:-len(self.config_yaml["volume_extension"])]
      #     print(" filename in get_latest_version", filename)
      #     print(" get latest version element", element)
      #     if filename in element:
      #         list_version.append(int(element[-2:]))
      #
      # print(" ttttt list version", list_version)

      #for list of all verison of a file = return list_version

      if list_version == []:
          return version
      else :
          max_version = max(list_version)
          max_version = min(max_version, 98) #to prevent exceeding 99 versions.
          print("max list_version before increment", max_version)
          return max_version

  def increment_latest_version(self, filename):
      latest_version = self.get_latest_version(filename)
      return f"_v{(latest_version + 1):02d}"

  def format_latest_version(self, filename):
      latest_version = self.get_latest_version(filename)
      return f"_v{(latest_version):02d}"




      # print(" in get_latest_version", elements)
      # for element in elements:
      #     if filename == element:





  def show_message_box(self, messageText=None):
      # Create a modal dialog
      dialog = qt.QMessageBox(slicer.util.mainWindow())
      dialog.setWindowTitle('Important Message')
      dialog.setText(f'{messageText}')

      # Add a single "OK" button
      dialog.addButton(qt.QMessageBox.Ok)

      # Show the message box as modal
      dialog.exec_()

      # After the message box is closed, further code execution resumes
      print("Dialog closed. Continuing with the code...")

  # # Call the function to show the message box
  # show_message_box()

  # Code execution will pause at the message box until the user clicks "OK".
  # After closing the message box, the code execution will resume.
  print("Continuing with the rest of the code...")


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

      print("test click browse maak")

    #maxime
  def onSelectOutputFolder(self):
      print("***You have just clicked to select the output folder.")
      self.OutputFolder = qt.QFileDialog.getExistingDirectory(None,"Open a folder", self.OUTPUT_DIR)
      print("***self.OutputFolder", self.OutputFolder)

      # Get the remaining cases files and save their name in a yaml file
      # Helped by ChatGPT
      print("***self.Cases", self.Cases)
      print("***self.VolumeNode.GetName()", self.VolumeNode.GetName())
      # Original list with nested objects
      original_list = self.Cases

      checkingRemainingCases = f'{self.OutputFolder}{os.sep}remainingCases.yaml'
      #create a copy of all cases
      checkingallCases = f'{self.OutputFolder}{os.sep}allCases.yaml'
      allCasesdata = {
          'FILES_SEG': self.allCases
      }
      if not os.path.exists(checkingallCases):
          print(f"***The path '{checkingallCases}' does not exists.")
          # Write data to a YAML file
          with open(checkingallCases, 'w') as file:
              yaml.dump(allCasesdata, file, default_flow_style=False)
              print("allCases worked")
      else :
          print(" the path all cases exists")
          with open(checkingallCases, 'r') as file:
              data = yaml.safe_load(file)
              self.allCases = data["FILES_SEG"]
              print(" self all cases just load", self.allCases)
              allCasesPath2 = []
              for i in range(len(self.allCases)):
                  for element in self.allCasesPath:
                      if self.allCases[i] in element:
                          allCasesPath2.append(element)
              print("allCasesPath2", allCasesPath2)
              self.allCasesPath = allCasesPath2



      # Example usage
      self.RemainingCases = checkingRemainingCases
      print("***yaml file path", self.RemainingCases)
      if os.path.exists(checkingRemainingCases):
          print(f"***The path '{checkingRemainingCases}' exists.")
          def extract_first_list_element_from_yaml(checkingRemainingCases):
              # Load the YAML file
              with open(checkingRemainingCases, 'r') as file:
                  yaml_data = yaml.safe_load(file)

              # Check if 'FILES_SEG' key exists in the YAML data
              if 'FILES_SEG' in yaml_data:
                  # Return the first element of the 'FILES_SEG' list
                  return yaml_data['FILES_SEG'][0]
              else:
                  # Handle the case where 'FILES_SEG' key is not found
                  print("'FILES_SEG' key not found in the YAML file.")
                  return None

          def extract_elements_from_yaml(checkingRemainingCases):
              # Load the YAML file
              with open(checkingRemainingCases, 'r') as file:
                  yaml_data = yaml.safe_load(file)

              # Check if 'FILES_SEG' key exists in the YAML data
              if 'FILES_SEG' in yaml_data:
                  # Return the first element of the 'FILES_SEG' list
                  return yaml_data['FILES_SEG']
              else:
                  # Handle the case where 'FILES_SEG' key is not found
                  print("'FILES_SEG' key not2 found in the YAML file.")
                  return None

          first_element = extract_first_list_element_from_yaml(checkingRemainingCases)
          print("First element in the 'FILES_SEG' list:", first_element)
          print("       ********* EXTRACTED!!! ")
          print("self case path", self.CasesPaths)

          yamlListeOfCases = extract_elements_from_yaml(checkingRemainingCases)
          self.yamlListName = yamlListeOfCases
          print("self yamllistofcase", self.yamlListName)

          self.currentCase = first_element
          self.currentCasePath = self.get_path_from_name(self.currentCase)

          ##get the corresponding index
          print("get corresponding index")
          print("self currentcase", self.currentCase)
          print("self current case path", self.currentCasePath)

          print(" self current index", self.currentCase_index)
          print("len yamlFileName", len(self.yamlListName))
          print(" len yamlPath", len(self.yamlListPath))
          print("self.allCases", len(self.allCases))
          self.get_corresponding_index()



          # Find the path of the case to be loaded.
          search_directory = self.CurrentFolder
          def find_file_by_name(search_directory, first_element):
              for root, dirs, files in os.walk(search_directory):
                  if first_element in files:
                      return os.path.join(root, first_element)
              return None

          PathToLoad = find_file_by_name(search_directory, first_element)

          # Find the path of the files to be in the case list
          def find_files(filenames, root_dir):
              file_paths = []
              for dirpath, _, files in os.walk(root_dir):
                  for file in files:
                      if file in filenames:
                          file_paths.append(os.path.join(dirpath, file))
              return file_paths

          # # Example usage:
          # filenames = yamlListName
          # print("root_dir", self.CurrentFolder)
          # root_dir = self.CurrentFolder

          yamlListPath = sorted(find_files(yamlListeOfCases,
                                           self.CurrentFolder))
          print("yamlListPath", yamlListPath)

          self.yamlListPath = yamlListPath
          print("len self yaml path", len(self.yamlListPath))
          print("self yaml list of Cases", self.yamlListPath)

          for i in range(len(self.Cases)): #tried with self.yaml and works
              # too = might create some bugs eventually
              print(" self case path i ", self.CasesPaths[i])
              print(" first element", PathToLoad)

              # if f'{PathToLoad}' == self.CasesPaths[i]:
              if f'{PathToLoad}' == self.allCasesPath[i]:
                  print("there we go")
                  print("self cases path i,", self.CasesPaths[i])
                  # print("self current index", self.current_index)
                  print("self current index", self.currentCase_index)
                  print("i", i)
                  # while self.currentCase_index < i:
                  #     print("current case is less than i", i)
                  #     self.onNextButton()
                  # break
                  self.currentCase_index = i
                  print("current case is less than i", i)
                  # self.onNextButton()
                  break

          self.update_UI_case_list()

      else:
          print(f"The path '{checkingRemainingCases}' does not exist.")

          # # Shallow copy
          # shallow_copied_list = copy.copy(original_list)
          #
          # # Deep copy
          # deep_copied_list = copy.deepcopy(original_list)
          #
          # print("Original list after deep copy modification:",
          #       original_list)  # Output: [['a', 2, 3], [4, 5, 6]]
          # print("Deep copied list:",
          #       deep_copied_list)  # Output: [['a', 2, 3], ['b', 5, 6]]
          #
          # volume_name = self.VolumeNode.GetName()
          # extension = '.nii.gz'  # TO MODIFY ACCORDING TO YAML FILE
          # remaining_cases = deep_copied_list
          # target_case = volume_name + extension
          #
          # # remaining_cases = [item for item in remaining_cases if
          # #                    item != target_case]

          # print("remaining cases", remaining_cases)

          # saving remaining cases in yaml file
          # file_paths = self.RemainingCases
          # directory = self.OutputFolder
          file_name = 'remainingCases.yaml'
          # file_path = os.path.join(directory, file_name)

          def save_files_seg_to_yaml(file_paths=self.RemainingCases, directory=self.OutputFolder,
                                     file_name=file_name):
              # Ensure the directory exists
              os.makedirs(directory, exist_ok=True)

              # Define the complete file path

              # Create a dictionary with the 'FILES_SEG' key
              data = {
                  'FILES_SEG': self.Cases
              }

              # Write the dictionary to the YAML file
              with open((os.path.join(directory, file_name)), 'w') as file:
                  yaml.dump(data, file, default_flow_style=False)

          save_files_seg_to_yaml()

  def selectGTReferences(self):
      print(" ENTERING selectGTReferences")
      self.GTFolder = qt.QFileDialog.getExistingDirectory(None,
                                                              "Open a folder",
                                                              self.GT_DIR)
      # print("self.GTFolder", self.GT_DIR)
      # print("self.GTFolder", self.GTFolder)


  def onToggleSegmentationVersions(self):
      print("test toggle segmentation")
      # self.toggleSegmentation = not self.toggleSegmentation
      print("sefl toggle Segmentation", self.toggleSegmentation)
      # if self.toggleSegmentation:
      self.open_selection_box()

  def open_selection_box(self):
      # Initialize clickedItems
      self.clickedItems = set()

      # Create the custom widget
      widget = qt.QWidget()
      widget.setWindowTitle(f"{self.currentCase}")
      widget.setLayout(qt.QVBoxLayout())

      # Set the minimum size for the widget
      widget.setMinimumSize(300, 200)  # Width: 300, Height: 200

      # Set the widget to stay on top
      widget.setWindowFlags(widget.windowFlags() | qt.Qt.WindowStaysOnTopHint)

      item_layout = qt.QGridLayout()
      widget.layout().addLayout(item_layout)

      # Add items to the selection box
      name = self.Cases[self.currentCase_index]
      filename = self.remove_file_extension(name)
      items = set(sorted(self.get_list_of_versions(filename)))
      print("items", items)
      name_of_items = []
      for i in range(len(items)):
          name_of_items.append(f"v{i+1:02d}")
      print("name of items", name_of_items)
      max_version = max(items, default=0) #avoid error if the case has no
      # previous segmentation
      num_columns = 1
      versions_dict = self.get_all_files_versions(max_version)
      print("version_dict", versions_dict)

      # Store button widgets in a dictionary
      self.buttons = {}

      def item_clicked(name_of_items):
          print(f"Item '{name_of_items}' clicked")
          button = self.buttons[name_of_items]
          if name_of_items not in self.clickedItems:
              print(f"New item '{name_of_items}' has not been clicked before.")
              self.itemClicked = True  # Mark this item as clicked
              self.load_version(versions_dict, name_of_items)
              button.setStyleSheet(
                  "background-color: green")  # Set button color to green
              self.clickedItems.add(name_of_items)  # Add to clicked items set
          else:
              print(f"Item '{name_of_items}' has already been clicked before.")
              self.itemClicked = False  # Unmark this item as clicked
              self.unload_version(versions_dict, name_of_items)
              button.setStyleSheet("")  # Revert button color to default
              self.clickedItems.remove(
                  name_of_items)  # Remove from clicked items set

      for i, item in enumerate(name_of_items):
          row = i // num_columns
          col = i % num_columns
          button = qt.QPushButton(item)
          button.clicked.connect(lambda _, name=item: item_clicked(
              name))  # Use lambda with default argument
          item_layout.addWidget(button, row, col)
          self.buttons[item] = button

          # def item_clicked(name_of_items):
      #     print(f"Item '{name_of_items}' clicked")
      #     if name_of_items not in self.clickedItems:
      #         print(f"New item '{name_of_items}' has not been clicked before.")
      #         self.itemClicked = True  # Mark this item as clicked
      #         self.load_version(versions_dict, name_of_items)
      #         self.clickedItems.add(name_of_items)  # Add to clicked items set
      #     else:
      #         print(f"Item '{name_of_items}' has already been clicked before.")
      #         self.itemClicked = False  # Unmark this item as clicked
      #         self.unload_version(versions_dict, name_of_items)
      #         self.clickedItems.remove(
      #             name_of_items)  # Remove from clicked items set
      #
      # for i, item in enumerate(name_of_items):
      #     row = i // num_columns
      #     col = i % num_columns
      #     button = qt.QPushButton(item)
      #     button.clicked.connect(lambda _, name=item: item_clicked(
      #         name))  # Connect the clicked signal
      #     item_layout.addWidget(button, row, col)

      # Add OK and Cancel buttons
      button_box = qt.QDialogButtonBox(
          qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel)
      button_box.accepted.connect(widget.close)
      button_box.rejected.connect(widget.close)
      widget.layout().addWidget(button_box)

      # Show the widget non-modally
      widget.show()

      # maxime

  def onAssessSegmentationButton(self):
      print("assess segmentation started! ")

      #set a counter for the number of iteration (pressed self asssment
      # self.count = 0

      # Get the list of the Ground Truth References segmentations
      ground_truth_list = [f for f in os.listdir(self.GTFolder) if
                                   os.path.isfile(os.path.join(self.GTFolder, f)) and
                                   not f.startswith('.') and not f.endswith(
                                       '.cache')]

      print("ground truth list", ground_truth_list)

      # Select a Random Case To Assess and Display it in the SliceViewer
      # ground_truth_list = os.listdir(self.GTFolder)
      random_item_filepath = random.choice(ground_truth_list)
      print("random item", random_item_filepath)
      filename = self.remove_file_extension(random_item_filepath)
      print("filename", filename)
      version_ref = self.check_version_ref(filename)
      print("version_ref", version_ref)

      list_of_labels = self.get_all_labels()
      print("list_of_labels", list_of_labels)
      filename_final = self.remove_version_extension(filename)
      filename_final = self.remove_label_extension(filename_final,list_of_labels)
      filename_final = filename_final[:-1]
      print("filename final", filename_final)

      # Get the Volume associated to the random_item_filepath
      volumePath = (f"{self.GTFolder}{os.sep}volumes{os.sep}{filename_final}{self.file_extension}")
      print("volumePath", volumePath)
      slicer.util.loadVolume(volumePath)

      # volume_node = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')
      # new_name = "NewVolumeName"
      # volume_node.SetName(new_name)

      # Get the current scalar volume node
      # Get the scalar volume node by its current name

      # Replace 'vtkMRMLScalarVolumeNode2' with the actual ID of your scalar volume node
      nodeID1 = 'vtkMRMLScalarVolumeNode1'
      volumeNodeMain = slicer.mrmlScene.GetNodeByID(nodeID1)

      count = self.countAssess+1

      nodeID2 = f'vtkMRMLScalarVolumeNode{count}'
      volumeNodeTest = slicer.mrmlScene.GetNodeByID(nodeID2)
      print("got node ID1 et nodeID2")
      print("get name node ID1", volumeNodeMain.GetName())
      print("get name node ID2", volumeNodeTest.GetName())
      print("finalename final  ebfore", filename_final)

      def setAssessName():
          if self.countAssess == 1:
            volumeNodeTest.SetName('NewVolumeName')
            return 'NewVolumeName'
          else :
            volumeNodeTest.SetName(f'NewVolumeName_{self.countAssess}')
            return f'NewVolumeName_{self.countAssess}'

      # if volumeNodeMain.GetName() in volumeNodeTest.GetName():
      #     newName = setAssessName()
      # # if filename_final in volumeNodeMain.GetName():
      #     print("*****test == worked!")
      #     # Set the new name of the volume node
      #     slicer.app.processEvents()  # Update the GUI
      #     print("name changed")
      # else :
      #     newName = setAssessName()
      #     slicer.app.processEvents()  # Update the GUI
      #     print("name changed2")

      newName = setAssessName()
      slicer.app.processEvents()
      print("newname", newName)

      #Increment the number of iteration to find easily the appropriate node
      # after
      self.countAssess+=1


      print("rady to test manual segmentation!")
      print("filename_final", filename_final)
      #get latest version
      latest_ref_version = self.get_latest_version_ref(filename_final)
      print("latest_ref_version", latest_ref_version)

      print("ground truth list", ground_truth_list)


      # Remove the name of the case (and the name of its segment)

      # Open the SegmentEditor and create new Segments

      print('voluem node name', volumeNodeTest.GetName())


      ###chat gpt
      print('chatgpot seg')
      # Step 1: Create a New Segmentation Node
      volumeNodeName = newName # Replace with your volume node name
      volumeNode = slicer.util.getNode(volumeNodeName)

      segmentationNode = slicer.mrmlScene.AddNewNodeByClass(
          'vtkMRMLSegmentationNode')
      curSegName = segmentationNode.SetName(volumeNode.GetName() +
                                          '_Segmentation')
      segmentation = segmentationNode.GetSegmentation()
      print(" segmentation", segmentation)
      print("Cure seg name", curSegName)
      #Create new segments and attribute them in the segmentaitron node
      for i in range(len(list_of_labels)):
          segmentation.AddEmptySegment()
          segmentID = segmentation.GetNthSegmentID(i)
          segment = segmentation.GetSegment(segmentID)
          segment.SetName(f"{newName}_{list_of_labels[i]}{self.file_extension}")

      print(f"Created new segmentation node: {segmentationNode.GetName()}")

      # Set the segmentation node in the Segmentation Editor
      segmentationEditorWidget = slicer.modules.SegmentEditorWidget.editor
      segmentationEditorWidget.setSegmentationNode(segmentationNode)
      print("segmentation node name after supposed to be setted", segmentationNode.GetName())

      # Set the source volume in the segmentation editor widget
      # sourceVolumeNode = slicer.util.getNode(volumeNodeName)
      segmentationEditorWidget.setMasterVolumeNode(volumeNode)

      self.set_color_label(segmentationNode, True)
      self.first_label_segment_name = f"{newName}_{list_of_labels[0]}{self.file_extension}"
      self.segmentationNode = segmentationNode

      print("first_label_assess", self.first_label_segment_name)

      self.onPushButton_select_label(self.first_label_segment_name, segmentationNode)

      ###HERE 20240606
      # Create a new segment editor node
      print(" now for creating a new segment editor node")
      # segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass(
      #     "vtkMRMLSegmentEditorNode")
      # segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
      # # Set the segment editor node in the widget
      # segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
      # # Now set the segmentation node
      # segmentEditorWidget.setSegmentationNode(segmentationNode)
      # # Finally, set the source volume node
      # segmentEditorWidget.setSourceVolumeNode(volumeNode)

      # segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
      # segmentEditorWidget.setSegmentationNode(segmentationNode)
      # segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
      # segmentEditorWidget.setSourceVolumeNode(volumeNode)
      self.onPushButton_segmeditor()

      ### Get the essential values for use in result
      self.assessOrigDict["filename"] = filename
      self.assessOrigDict["filename_final"] = filename_final
      self.assessOrigDict["volumePath"] = volumePath
      self.assessOrigDict["newName"] = newName
      self.assessOrigDict["latest_ref_version"] = latest_ref_version
      self.assessOrigDict["volumeNodeName"] = volumeNodeName
      self.assessOrigDict["segmentationNode"] = segmentationNode
      self.assessOrigDict["list_of_labels"] = list_of_labels
      self.assessOrigDict["ground_truth_list"] = ground_truth_list

      print(" self assessOrig Dict", self.assessOrigDict)
      # self.assessModifDict = {}


      # At each slice that is modified, a dice score is printed when leaving
      # the slice

  def set_color_label(self, segmentationNode, AssessSegmentationFlag=False):
      for label in self.config_yaml["labels"]:
          print("******* ****** *****")
          print("semgneaitonnode", segmentationNode)
          print(" label yaml data", label)
          print("label yaml name", label["name"])
          print(" rgb", label["color_r"], label["color_g"], label["color_b"])

          self.onNewLabelSegm(segmentationNode, label["name"], label["color_r"],
                              label["color_g"], label["color_b"], AssessSegmentationFlag)
          # label["lower_bound_HU"],
          # label["upper_bound_HU"])
          # print("sel on NewlabelSegm", self.onNewLabelSegm())

  def onGetResult(self):
      print(" ENTERING onGetResult")

      # Calculate the overall Dice Score between the reference segmentation
      # and the new one (saved in assessment folder)
      print("self assessing Dict", self.assessOrigDict)
      for element in self.assessOrigDict:
          print(element, self.assessOrigDict[element])
      list_of_label_map_to_compare = []
      for element in self.assessOrigDict["ground_truth_list"]:
          if self.assessOrigDict["filename_final"] in element:
              list_of_label_map_to_compare.append(element)

      print("\n")
      for element in list_of_label_map_to_compare:
          print("element", element)
      ### HERE END OF SUNDAY JUNE 09 20H32
      ### PROBLEM HERE IS TO CHECK IF GETS THE LATEST VERSION AND ALSO WHEN i
      # REDO ASSESSMENT





      # If Dice Score > threshold, then print/ dialog box! You passed
      # If Dice Score < threshold, then print dialog box! Your Dice Score.
      # Please retry and load a new volume to be assessed

  def onToggleInterpolation(self):
      print(" ENTERING onToggleInterpolation")
      volumeNode = slicer.mrmlScene.GetFirstNodeByClass(
                          'vtkMRMLVolumeNode')
      displayNode = volumeNode.GetDisplayNode()
      currentState = displayNode.GetInterpolate()
      displayNode.SetInterpolate(not currentState)
      print("current state interpolation", currentState)
      toggleButton = self.ui.toggleInterpolation
      if currentState == 0:
         toggleButton.setStyleSheet("background-color : green")
      else:
          toggleButton.setStyleSheet("background-color : red")


  def onCreateSegmentationButtonClicked(self):
      print("\n ENTERING onCreateSegmentationButton \n")

      ###MAGICAL LINE this makes working the paint button and node in seg
      segment_name = self.segment_name
      print("segment name on createsegmentaitn button", segment_name)
      self.onPushButton_select_label(segment_name)
      print("segment name on createsegmentaitn button", segment_name)

      #TO REMOVE
      # segment_name_initial = self.config_yaml["labels"][0]["name"]
      # print("segment name initial", segment_name_initial)
      # self.onPushButton_select_label(segment_name_initial)
      # Create a new segmentation node
      # segmentationNode = slicer.mrmlScene.AddNewNodeByClass(
      #     'vtkMRMLSegmentationNode')
      # print("segmentationNode", segmentationNode)
      # segmentationNode.CreateDefaultDisplayNodes()  # Create the display node as well
      # segmentationNode.SetName('NewSegmentation')
      #
      # # Create a new segmentation mask
      # segmentId = segmentationNode.GetSegmentation().AddEmptySegment(
      #     'NewSegment')
      # print("segment ID", segmentId)
      # logging.info(f"New segmentation mask created with ID: {segmentId}")
      print("**************segmentation created!!!!!")
      # segmentationNode = slicer.mrmlScene.GetNodeByID(
      #     "vtkMRMLSegmentationNode1")
      # print("segmentation node", segmentationNode)





      # # Get the current scene
      # scene = slicer.mrmlScene
      #
      # # Initialize lists to hold the names of volume and segmentation nodes
      # volume_node_names = []
      # segmentation_node_names = []
      #
      # # Iterate through all nodes in the scene
      # for i in range(scene.GetNumberOfNodes()):
      #     node = scene.GetNthNode(i)
      #
      #     # Check if the node is a volume node
      #     if node.IsA("vtkMRMLScalarVolumeNode"):
      #         volume_node_names.append(node.GetName())
      #
      #     # Check if the node is a segmentation node
      #     elif node.IsA("vtkMRMLSegmentationNode"):
      #         segmentation_node_names.append(node.GetName())
      #
      # # Print the list of volume node names
      # print("Volume Nodes:")
      # for name in volume_node_names:
      #     print(name)
      #
      # # Print the list of segmentation node names
      # print("\nSegmentation Nodes:")
      # for name in segmentation_node_names:
      #     print(name)
      #
      # print("volume nodes name list", volume_node_names)
      #
      # print("semgentation nodes name list", segmentation_node_names)
      #
      # # Names of the volume and segmentation nodes
      # volume_name = volume_node_names[0]
      # segmentation_name = segmentation_node_names[0]
      #
      # # Get the volume node and segmentation node
      # volumeNode = slicer.util.getNode(volume_name)
      # segmentationNode = slicer.util.getNode(segmentation_name)
      #
      # if segmentationNode:
      #     segmentation = segmentationNode.GetSegmentation()
      #     segmentIDs = segmentation.GetSegmentIDs()
      #
      #     for segmentID in segmentIDs:
      #         print("Segment ID:", segmentID)
      # else:
      #     print("Segmentation node not found.")
      #
      # # segmentID = slicer.util.getNode(segmentIDs[0])
      # print("segment ID ****", segmentID)
      #
      # segmentationNode = slicer.util.getNode(segmentation_name)
      # print("segmentationNode ****", segmentationNode)
      #


      # # Get the segmentation node (the current one)
      # self.SegmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      # print("self segmentationNode", self.segmentationNode)
      #
      # # Get the volume node (the current one)
      # self.VolumeNode = slicer.util.getNodesByClass('vtkMRMLVolumeNode')[0]
      #
      # # Get the label mal (signification? - mb added by chatgpt and works!
      # self.labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
      # # print("self label mao", self.labelmap_volume_node)
      # slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(
      #     self.SegmentationNode, self.labelmapVolumeNode, self.VolumeNode)
      #
      # slicer.app.processEvents()


      # # Get the geometry information of the volume node
      # spacing = volumeNode.GetSpacing()
      # origin = volumeNode.GetOrigin()
      # directionMatrix = vtk.vtkMatrix4x4()
      # volumeNode.GetIJKToRASMatrix(directionMatrix)
      #
      # # Get the binary labelmap representation of the segmentation
      # segmentationBinaryLabelmap = (
      #     segmentationNode.GetBinaryLabelmapRepresentation(volume_name,
      #                                                      segmentation_name))
      #
      # # Create a resampling filter
      # resampleFilter = vtk.vtkImageResample()
      # resampleFilter.SetInputData(segmentationBinaryLabelmap)
      # resampleFilter.SetOutputSpacing(spacing)
      # resampleFilter.SetOutputOrigin(origin)
      # resampleFilter.SetResliceAxes(directionMatrix)
      #
      # # Perform the resampling
      # resampleFilter.Update()
      #
      # # Convert the resampled image data back to a segmentation node
      # resampledImageData = slicer.util.arrayFromVolume(
      #     resampleFilter.GetOutput())
      # slicer.util.updateVolumeFromArray(resampledImageData, segmentationNode)

      # Display both volume and segmentation node in Segment Editor for annotation


      # # Get the current scene
      # scene = slicer.mrmlScene
      #
      # # Find the volume node by name
      # volume_node = scene.GetFirstNodeByName(volume_name)
      # if volume_node is None:
      #     raise RuntimeError(
      #         f"Volume node with name '{volume_name}' not found.")
      #
      # # Find the segmentation node by name
      # segmentation_node = scene.GetFirstNodeByName(segmentation_name)
      # if segmentation_node is None:
      #     raise RuntimeError(
      #         f"Segmentation node with name '{segmentation_name}' not found.")
      #
      # # Create a Segment Editor to link the segmentation and volume nodes
      # segment_editor_widget = slicer.qMRMLSegmentEditorWidget()
      # segment_editor_widget.setMRMLScene(slicer.mrmlScene)
      #
      # # Create and set up a Segment Editor node
      # segment_editor_node = slicer.mrmlScene.AddNewNodeByClass(
      #     "vtkMRMLSegmentEditorNode")
      # segment_editor_widget.setMRMLSegmentEditorNode(segment_editor_node)
      #
      # # Set the segmentation node in the Segment Editor
      # segment_editor_widget.setSegmentationNode(segmentation_node)
      #
      # # Set the volume node as the source volume
      # segment_editor_widget.setSourceVolumeNode(volume_node)
      #
      # # Ensure the segmentation geometry matches the volume geometry
      # segmentation_logic = slicer.modules.segmentations.logic()
      # segmentation_logic.SetReferenceImageGeometryParameterFromVolumeNode(
      #     segmentation_node, volume_node)
      #
      # # Optional: Update the views
      # slicer.app.processEvents()

      # print("segmentation node", segmentationNode)
      # print("segmentation id ****", segmentationNode)



    #maxime
  def onCreateSegmentationButton(self):
      print("\n ENTERING onCreateSegmentationButton \n")
      print("it works creation segmentation ")
      self.onCreateSegmentationButtonClicked()
      self.onPushButton_segmeditor()
      self.observeSegmentationNode()
      print("opened segm editor")

  def msg_warnig_delete_segm_node_clicked(self):
      if slicer.util.getNodesByClass('vtkMRMLSegmentationNode'):
        slicer.mrmlScene.RemoveNode(slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0])
    
  #load version maxime adapt
  def load_mask_v2(self):
      print("\n LOADING MASK V2 \n")
      print("IN LOADING MASK")
      print("self cases", self.Cases)
      self.loadMask = not self.loadMask
      print(" self load mask,", self.loadMask)

      # for element in  self.Cases:
      #     print("elenent", element)
      #     filename = self.remove_file_extension(element)
      #     version = self.get_version(filename)





      # # Get list of prediction names
      # msg_warning_delete_segm_node =qt.QMessageBox() # Typo correction
      # msg_warning_delete_segm_node.setText('This will delete the current segmentation. Do you want to continue?')
      # msg_warning_delete_segm_node.setIcon(qt.QMessageBox.Warning)
      # msg_warning_delete_segm_node.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
      # # if clikc ok, then delete the current segmentatio
      # msg_warning_delete_segm_node.setDefaultButton(qt.QMessageBox.Cancel)
      # response = msg_warning_delete_segm_node.exec() # calls remove node if ok is clicked
      # if response == qt.QMessageBox.Ok:
      #     self.msg_warnig_delete_segm_node_clicked()
      #
      # else:
      #     return
      #
      # try:
      #       self.predictions_names = sorted([re.findall(self.SEGM_REGEX_PATTERN,os.path.split(i)[-1]) for i in self.predictions_paths])
      #       self.called = False # restart timer
      # except AttributeError as e:
      #       msgnopredloaded=qt.QMessageBox() # Typo correction
      #       msgnopredloaded.setText('Please select the prediction directory!')
      #       msgnopredloaded.exec()
      #       # Then load the browse folder thing for the user
      #       self.onBrowseFolders_2Button()
      #
      # self.currentPredictionPath = ""
      # for p in self.predictions_paths:
      #     if self.currentCase in p:
      #         self.currentPredictionPath = p
      #         break
      #
      # if self.currentPredictionPath != "":
      #     # Then load the prediction segmentation
      #     slicer.util.loadSegmentation(self.currentPredictionPath)
      #     self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      #     self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      #     self.segmentEditorNode =  self.segmentEditorWidget.mrmlSegmentEditorNode()
      #     self.segmentEditorWidget.setSegmentationNode(self.segmentationNode)
      #     self.segmentEditorWidget.setSourceVolumeNode(self.VolumeNode)
      #     # set refenrence geometry to Volume node
      #     self.segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.VolumeNode)
      #     nn = self.segmentationNode.GetDisplayNode()
      #     # set Segmentation visible:
      #     nn.SetAllSegmentsVisibility(True)
      #     self.segmentationNode.GetDisplayNode().SetOpacity2DFill(0)
      #
      #     self.convert_nifti_header_Segment()
      #
      #     #### ADD SEGMENTS THAT ARE NOT IN THE SEGMENTATION ####
      #
      # else:
      #     msg_no_such_case = qt.QMessageBox()
      #     msg_no_such_case.setText('There are no mask for this case in the directory that you chose!')
      #     msg_no_such_case.exec()

      # update subject hierarchy
      # self.subjectHierarchy()

  #dr letourneau load mask function
  # def load_mask_v2(self):
  #     print("\n LOADING MASK V2 \n")
  #     print("IN LOADING MASK")
  #     # Get list of prediction names
  #     msg_warning_delete_segm_node =qt.QMessageBox() # Typo correction
  #     msg_warning_delete_segm_node.setText('This will delete the current segmentation. Do you want to continue?')
  #     msg_warning_delete_segm_node.setIcon(qt.QMessageBox.Warning)
  #     msg_warning_delete_segm_node.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
  #     # if clikc ok, then delete the current segmentatio
  #     msg_warning_delete_segm_node.setDefaultButton(qt.QMessageBox.Cancel)
  #     response = msg_warning_delete_segm_node.exec() # calls remove node if ok is clicked
  #     if response == qt.QMessageBox.Ok:
  #         self.msg_warnig_delete_segm_node_clicked()
  #
  #     else:
  #         return
  #
  #     try:
  #           self.predictions_names = sorted([re.findall(self.SEGM_REGEX_PATTERN,os.path.split(i)[-1]) for i in self.predictions_paths])
  #           self.called = False # restart timer
  #     except AttributeError as e:
  #           msgnopredloaded=qt.QMessageBox() # Typo correction
  #           msgnopredloaded.setText('Please select the prediction directory!')
  #           msgnopredloaded.exec()
  #           # Then load the browse folder thing for the user
  #           self.onBrowseFolders_2Button()
  #
  #     self.currentPredictionPath = ""
  #     for p in self.predictions_paths:
  #         if self.currentCase in p:
  #             self.currentPredictionPath = p
  #             break
  #
  #     if self.currentPredictionPath != "":
  #         # Then load the prediction segmentation
  #         slicer.util.loadSegmentation(self.currentPredictionPath)
  #         self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
  #         self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
  #         self.segmentEditorNode =  self.segmentEditorWidget.mrmlSegmentEditorNode()
  #         self.segmentEditorWidget.setSegmentationNode(self.segmentationNode)
  #         self.segmentEditorWidget.setSourceVolumeNode(self.VolumeNode)
  #         # set refenrence geometry to Volume node
  #         self.segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.VolumeNode)
  #         nn = self.segmentationNode.GetDisplayNode()
  #         # set Segmentation visible:
  #         nn.SetAllSegmentsVisibility(True)
  #         self.segmentationNode.GetDisplayNode().SetOpacity2DFill(0)
  #
  #         self.convert_nifti_header_Segment()
  #
  #         #### ADD SEGMENTS THAT ARE NOT IN THE SEGMENTATION ####
  #
  #     else:
  #         msg_no_such_case = qt.QMessageBox()
  #         msg_no_such_case.setText('There are no mask for this case in the directory that you chose!')
  #         msg_no_such_case.exec()
  #
  #     # update subject hierarchy
  #     self.subjectHierarchy()



  def convert_nifti_header_Segment(self):
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
                      new_segment_name = f"{self.currentCase}_{label['name']}"
                      print(f'new segment_name :: {new_segment_name}')
                      self.segmentationNode.GetSegmentation().GetNthSegment(i).SetName(new_segment_name)
                      # set color
                      self.segmentationNode.GetSegmentation().GetNthSegment(i).SetColor(label["color_r"] / 255,
                                                                                        label["color_g"] / 255,
                                                                                        label["color_b"] / 255)

  def update_current_case_paths_by_segmented_volumes(self):
      print('\n ENTERINE update_current_case_paths_by_segmented_volumes \n')
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

  def onSegmendEditorPushButton(self):

      print("\n ENTERING onSegmendEditorPushButton \n")

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

  # def onPushDefaultMin(self):
  #     with open(CONFIG_FILE_PATH, 'r') as file:
  #       fresh_config = yaml.safe_load(file)
  #       self.config_yaml["labels"][self.current_label_index]["lower_bound_HU"] = fresh_config["labels"][self.current_label_index]["lower_bound_HU"]
  #       self.setUpperAndLowerBoundHU(self.config_yaml["labels"][self.current_label_index]["lower_bound_HU"], self.config_yaml["labels"][self.current_label_index]["upper_bound_HU"])

  # def onPushDefaultMax(self):
  #     with open(CONFIG_FILE_PATH, 'r') as file:
  #       fresh_config = yaml.safe_load(file)
  #       self.config_yaml["labels"][self.current_label_index]["upper_bound_HU"] = fresh_config["labels"][self.current_label_index]["upper_bound_HU"]
  #       self.setUpperAndLowerBoundHU(self.config_yaml["labels"][self.current_label_index]["lower_bound_HU"], self.config_yaml["labels"][self.current_label_index]["upper_bound_HU"])

  def onPushButton_undo(self):
      self.segmentEditorWidget.undo()

  def onDropDownButton_label_select(self, value):
      print('\n ENTERING onDropDownButton_label_select \n')
      print("value ", value)


      self.current_label_index = value
      label = self.config_yaml["labels"][value]

      print("label", label)

      # self.setUpperAndLowerBoundHU(label["lower_bound_HU"], label["upper_bound_HU"])

      label_name = label["name"]
      print("label_name", label_name)

      try:
        print(" try test")
        volumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
        # print("volume node", volumeNode)


        print(" DropDownButton_label_select self current case",
              self.currentCase)
        print("label name", label_name)
        segment_name = f"{self.currentCase}_{label_name}"
        # self.onPushButton_select_label(segment_name, label["lower_bound_HU"], label["upper_bound_HU"])
        self.onPushButton_select_label(segment_name)
        print("try passed")
      except:
        print(" raised except")
        pass
      
  def onPushButton_Paint(self):
        print('\n ENTERING onPushButton_Paint \n')
        print(" MMMMMMMMMM onPushButton_Paint self segmentation modified",
              self.segmentationModified)
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
        # self.segmentEditorNode.SetMasterVolumeIntensityMask(True)
        # self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(self.LB_HU, self.UB_HU)
        # self.segmentEditorNode.SetOverwriteMode(slicer.vtkMRMLSegmentEditorNode.OverwriteAllSegments)
        

  def keyboard_toggle_fill(self):
      print('keyboard_toggle_fill')
      if self.ui.pushButton_ToggleFill.isChecked():
          self.ui.pushButton_ToggleFill.toggle()
          self.toggleFillButton()
      else:
          self.ui.pushButton_ToggleFill.toggle()
          self.toggleFillButton()


  def toggleFillButton(self):
      print('toggleFillButton')
      if  self.ui.pushButton_ToggleFill.isChecked():
          self.ui.pushButton_ToggleFill.setStyleSheet("background-color : lightgreen")
          self.ui.pushButton_ToggleFill.setText('Fill: ON')
          self.segmentationNode.GetDisplayNode().SetOpacity2DFill(100)
      else:
          self.ui.pushButton_ToggleFill.setStyleSheet("background-color : indianred")
          self.ui.pushButton_ToggleFill.setText('Fill: OFF')
          self.segmentationNode.GetDisplayNode().SetOpacity2DFill(0)

  def onPushButton_ToggleVisibility(self):
      print('onPushButton_ToggleVisibility')
      if self.ui.pushButton_ToggleVisibility.isChecked():
          self.ui.pushButton_ToggleVisibility.setStyleSheet("background-color : indianred")
          self.ui.pushButton_ToggleVisibility.setText('Visibility: OFF')
          self.segmentationNode.GetDisplayNode().SetAllSegmentsVisibility(False)
      else:
          self.ui.pushButton_ToggleVisibility.setStyleSheet("background-color : lightgreen")
          self.ui.pushButton_ToggleVisibility.setText('Visibility: ON')
          self.segmentationNode.GetDisplayNode().SetAllSegmentsVisibility(True)

  def togglePaintMask(self):
        print('togglePaintMask')
        if self.ui.pushButton_TogglePaintMask.isChecked():
            self.ui.pushButton_TogglePaintMask.setStyleSheet("background-color : lightgreen")
            self.ui.pushButton_TogglePaintMask.setText('Paint Mask ON')
            self.segmentEditorNode.SetMaskMode(slicer.vtkMRMLSegmentationNode.EditAllowedEverywhere)


  def onPushButton_segmeditor(self):
      print('onPushButton_segmeditor')
      print(" MMMMMMMMMM onPushButton_segmeditor self segmentation modified",
            self.segmentationModified)
      slicer.util.selectModule("SegmentEditor")
      first_segment_name = self.first_label_segment_name
      print("on push button segm editor", first_segment_name)
      self.onPushButton_select_label(first_segment_name)

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

  # def onLB_HU(self):
  #     try:
  #       self.LB_HU=self.ui.LB_HU.value
  #       self.segmentEditorNode.SetMasterVolumeIntensityMask(True)
  #       self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(self.LB_HU, self.UB_HU)
  #       self.config_yaml["labels"][self.current_label_index]["lower_bound_HU"] = self.LB_HU
  #     except:
  #       pass
      
  # def onUB_HU(self):
  #     try:
  #       self.UB_HU=self.ui.UB_HU.value
  #       self.segmentEditorNode.SetMasterVolumeIntensityMask(True)
  #       self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(self.LB_HU, self.UB_HU)
  #       self.config_yaml["labels"][self.current_label_index]["upper_bound_HU"] = self.UB_HU
  #     except:
  #       pass

  def check_match_label_name_value(self):
      """"
      Check match between lable name and values
      # seg.nrrd file = outputSegmFile
      # seg nifti file = outputSegmFileNifti
      # volume nifti file = outputVolfile
      #
      """
      print("\n ENTERING check_match_label_name_value  \n")
      # get the current label name
      # read with slicerio
      print('-'*20)
      print(f'self.currentCase::{self.currentCase}')
      print(f'self.outputSegmFile ::{self.outputSegmFile}')
      segmentation_info = slicerio.read_segmentation_info(self.outputSegmFile)
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
      if len(segment_names) != 3:
          raise ValueError('Number of segments not equal to 3')


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
      output_dir_segmentation_file_corrected = os.path.join(self.DefaultDir, 'Segmentation_file_corrected_slicerio')
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
      print("Checking for outlier labels")
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

class MySlicerModule(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "My Slicer Module"
        self.parent.categories = ["Examples"]
        self.parent.dependencies = []
        self.parent.contributors = ["Your Name (Your Institution)"]
        self.parent.helpText = """This is an example module to demonstrate integrating RenderManager."""
        self.parent.acknowledgementText = """This file was originally developed by Your Name, Your Institution."""


##errror is still present with code below [Qt] virtual int ctkVTKAbstractView::resumeRender() Cannot resume rendering, pause render count is already 0!
# class MySlicerModuleWidget(ScriptedLoadableModuleWidget):
#     def setup(self):
#         ScriptedLoadableModuleWidget.setup(self)
#
#         # Create a RenderManager instance
#         self.render_manager = RenderManager()
#
#         # Add a button to pause rendering
#         self.pauseButton = qt.QPushButton("Pause Rendering")
#         self.pauseButton.toolTip = "Pause rendering"
#         self.pauseButton.connect('clicked(bool)', self.onPauseRender)
#         self.layout.addWidget(self.pauseButton)
#
#         # Add a button to resume rendering
#         self.resumeButton = qt.QPushButton("Resume Rendering")
#         self.resumeButton.toolTip = "Resume rendering"
#         self.resumeButton.connect('clicked(bool)', self.onResumeRender)
#         self.layout.addWidget(self.resumeButton)
#
#     def onPauseRender(self):
#         render_window = slicer.app.layoutManager().threeDWidget(
#             0).threeDView().renderWindow()
#         self.render_manager.pause_render(render_window)
#
#     def onResumeRender(self):
#         render_window = slicer.app.layoutManager().threeDWidget(
#             0).threeDView().renderWindow()
#         self.render_manager.resume_render(render_window)
#
#
# class MySlicerModuleLogic(ScriptedLoadableModuleLogic):
#     def __init__(self):
#         pass
#
# class RenderManager:
#     def __init__(self):
#         self._pause_count = 0
#
#     def pause_render(self, render_window):
#         if self._pause_count == 0:
#             render_window.SetAbortRender(1)  # Pause rendering
#         self._pause_count += 1
#         print(f"Render paused, current pause count: {self._pause_count}")
#
#     def resume_render(self, render_window):
#         if self._pause_count > 0:
#             self._pause_count -= 1
#             if self._pause_count == 0:
#                 render_window.SetAbortRender(0)  # Resume rendering
#             print(f"Render resumed, current pause count: {self._pause_count}")
#         else:
#             print("Cannot resume rendering, pause render count is already 0!")
#
#     def is_rendering_paused(self):
#         return self._pause_count > 0




### maxime addings : mouse customs
# import vtk
# import slicer
import vtk

class CustomInteractorStyle(vtk.vtkInteractorStyleImage):
    def __init__(self, sliceWidget=None):
        self.AddObserver("RightButtonPressEvent", self.onRightButtonPressEvent)
        self.AddObserver("MouseMoveEvent", self.onMouseMoveEvent)
        self.AddObserver("RightButtonReleaseEvent", self.onRightButtonReleaseEvent)
        self.AddObserver("MouseWheelForwardEvent", self.onMouseWheelForwardEvent)
        self.AddObserver("MouseWheelBackwardEvent", self.onMouseWheelBackwardEvent)
        self.AddObserver("LeftButtonPressEvent", self.onLeftButtonPressEvent)
        self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonReleaseEvent)
        self.AddObserver("KeyPressEvent", self.onKeyPressEvent)
        self.AddObserver("KeyReleaseEvent", self.onKeyReleaseEvent)
        self.startPosition = None
        self.sliceWidget = sliceWidget
        # self.sliceWidget = slicer.app.layoutManager().sliceWidget('Red')
        # self.sliceWidget = slicer.app.layoutManager().sliceWidget('Yellow')
        # self.sliceWidget = slicer.app.layoutManager().sliceWidget('Red')
        self.sliceNode = self.sliceWidget.mrmlSliceNode()
        self.sliceLogic = slicer.app.applicationLogic().GetSliceLogic(self.sliceNode)
        self.panning = False
        self.zooming = False
        self.adjustingWindowLevel = False
        self.z_pressed = False

    def onRightButtonPressEvent(self, obj, event):
        self.startPosition = self.GetInteractor().GetEventPosition()
        self.panning = True
        self.OnRightButtonDown()
        return

    def onMouseMoveEvent(self, obj, event):
        if self.panning and self.startPosition:
            currentPosition = self.GetInteractor().GetEventPosition()
            deltaX = self.startPosition[0] - currentPosition[0]
            deltaY = self.startPosition[1] - currentPosition[1]

            # Adjust the image position based on mouse movement
            pan = self.sliceNode.GetXYZOrigin()
            self.sliceNode.SetXYZOrigin(pan[0] + deltaX, pan[1] + deltaY, pan[2])
            self.sliceNode.Modified()

            self.startPosition = currentPosition
        elif self.adjustingWindowLevel and self.startPosition:
            currentPosition = self.GetInteractor().GetEventPosition()
            deltaX = currentPosition[0] - self.startPosition[0]
            deltaY = self.startPosition[1] - currentPosition[1]

            # Adjust the window level and width based on mouse movement
            volumeNode = self.sliceLogic.GetBackgroundLayer().GetVolumeNode()
            displayNode = volumeNode.GetDisplayNode()
            currentWindowLevel = displayNode.GetLevel()
            currentWindowWidth = displayNode.GetWindow()

            newWindowLevel = currentWindowLevel + deltaY
            newWindowWidth = currentWindowWidth + deltaX

            displayNode.SetLevel(newWindowLevel)
            displayNode.SetWindow(newWindowWidth)

            self.startPosition = currentPosition

        elif self.zooming and self.startPosition:
            self.zoom()
            self.startPosition = self.GetInteractor().GetEventPosition()

        self.OnMouseMove()
        return

    def onRightButtonReleaseEvent(self, obj, event):
        self.startPosition = None
        self.panning = False
        self.OnRightButtonUp()
        return

    def onLeftButtonPressEvent(self, obj, event):
        self.startPosition = self.GetInteractor().GetEventPosition()
        self.adjustingWindowLevel = True
        self.OnLeftButtonDown()
        return

    def onLeftButtonReleaseEvent(self, obj, event):
        self.startPosition = None
        self.adjustingWindowLevel = False
        self.OnLeftButtonUp()
        return

    def onKeyPressEvent(self, obj, event):
        key = self.GetInteractor().GetKeySym()
        if key == "x":
            self.z_pressed = True
            # print("x key pressed")
        self.OnKeyPress()
        return

    def onKeyReleaseEvent(self, obj, event):
        key = self.GetInteractor().GetKeySym()
        if key == "x":
            self.z_pressed = False
            # print("x key released")
        self.OnKeyRelease()
        return

    def onMouseWheelForwardEvent(self, obj, event):
        if self.z_pressed:
            # print("Mouse scroll")
            self.zoom_in()
            # print("self zoom done")
        else:
            # Move to the next slice
            currentOffset = self.sliceLogic.GetSliceOffset()
            newOffset = currentOffset + self.getSliceSpacing()  # Move one slice forward
            self.sliceLogic.SetSliceOffset(newOffset)
            self.OnMouseWheelForward()
        return

    def onMouseWheelBackwardEvent(self, obj, event):
        if self.z_pressed:
            # print("Mouse scroll")
            self.zoom_out()
        else:
            # Move to the previous slice
            currentOffset = self.sliceLogic.GetSliceOffset()
            newOffset = currentOffset - self.getSliceSpacing()  # Move one slice backward
            self.sliceLogic.SetSliceOffset(newOffset)
            self.OnMouseWheelBackward()
        return

    def zoom_in(self):
        fov = self.sliceNode.GetFieldOfView()
        self.sliceNode.SetFieldOfView(fov[0] * 0.9, fov[1] * 0.9, fov[2])
        self.sliceNode.Modified()

    def zoom_out(self):
        fov = self.sliceNode.GetFieldOfView()
        self.sliceNode.SetFieldOfView(fov[0] / 0.9, fov[1] / 0.9, fov[2])
        self.sliceNode.Modified()

    def zoom(self):
        if self.startPosition:
            fov = self.sliceNode.GetFieldOfView()
            currentPos = self.GetInteractor().GetEventPosition()
            deltaY = self.startPosition[1] - currentPos[1]
            factor = 1.01 if deltaY > 0 else 0.99
            zoomSpeed = 10
            factor = factor ** (abs(deltaY) / zoomSpeed)
            self.sliceNode.SetFieldOfView(fov[0] * factor, fov[1] * factor, fov[2])
            self.sliceNode.Modified()

    def getSliceSpacing(self):
        volumeNode = self.sliceLogic.GetBackgroundLayer().GetVolumeNode()
        if volumeNode:
            spacing = volumeNode.GetSpacing()
            return spacing[2]  # Return the spacing along the Z-axis
        return 1.0  # Default spacing if volumeNode is not available

# # Get the interactor from the 'Yellow' slice view
# interactor = slicer.app.layoutManager().sliceWidget('Yellow').sliceView().interactor()
#
# # Apply the custom interactor style
# style = CustomInteractorStyle()
# interactor.SetInteractorStyle(style)





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
