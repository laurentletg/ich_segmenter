# To install a package in slicer python environment, use the following command:
# pip install --user package_name
import os
import logging
import qt, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from glob import glob
import re
import pandas as pd
import time
import slicerio # cannot install in slicer
import nrrd


VOLUME_FILE_TYPE = '*.nrrd' 
SEGM_FILE_TYPE = '*.seg.nrrd'
DEFAULT_VOLUMES_DIRECTORY = '/Users/laurentletourneau-guillon/Dropbox (Personal)/CHUM/RECHERCHE/2020ICHHEMATOMAS/2021_RSNA_ Kaggle_segmentation/2023 2023_03_07 RSNA SEGMENTATION 3 CLASSES/data'

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
      self.cancelButton = qt.QPushButton('Cancel')
      self.cancelButton.clicked.connect(self.pushCancel)
      layout.addWidget(self.continueButton)
      layout.addWidget(self.cancelButton)

      self.setLayout(layout)
      self.setWindowTitle("Semi-automatic PHE Tool")
      self.resize(400, 150)

   def UB_HU_valueChanged(self):
      self.UB_HU_value = self.semiAutoPHE_UB_HU_spinbox.value

   def LB_HU_valueChanged(self):
      self.LB_HU_value = self.semiAutoPHE_LB_HU_spinbox.value

   def pushContinue(self):
       self.segmenter.setUpperAndLowerBoundHU(self.LB_HU_value, self.UB_HU_value)
       # DelphTODO : call method in segmenter to apply threshold to PHE and hide segment (call PHE button first?)
       # DelphTODO : open next window for lasso select instructions, then close window and show lasso tool
       # DelphTODO : add button to apply ? or can it be automatic? 
       # DelphTODO : call method in segmenter to apply lasso exclusion and show segment 
       self.close()

   def pushCancel(self):
       self.close()
#
# ICH_SEGMENTER_V2
#

class ICH_SEGMENTER_V2(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "ICH_SEGMENTER_V2"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
    # TODO: update with short description of the module and a link to online module documentation
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#ICH_SEGMENTER_V2">module documentation</a>.
"""
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

### Timer class -custom class
#Class below could be at some point moved to a separate file
class Timer():
    def __init__(self, number=None):
        self.number = number
        self.total_time = 0
        self.inter_time = 0
        # counting flag to allow to PAUSE the time
        self.flag = False # False = not counting, True = counting (for pause button)


    def start(self):
        if self.flag == True:
            print("Timer already started for number ", self.number)
        if self.flag == False:
            print('*'*20,"STARTING TIME", '*'*20)
            print("Timer started for number", self.number) 
            # start counting flag (to allow to pause the time if False)
            self.flag = True
            self.start_time = time.time()
            
            
    def stop(self):
        # print("Timer stopped for number ", self.number)
        if self.flag == False:
            print("Timer already stopped for number ", self.number)
        if self.flag == True:
            print("Timer stopped for number ", self.number)
            self.inter_time = time.time() - self.start_time
            print('*'*20,"INTERMEDIATE TIME", '*'*20)
            print("Intermediate time for number ", self.number, " is ", self.inter_time)
            print('*'*20)
            self.total_time += self.inter_time
            print('#'*20, "TOTAL TIME", '#'*20)
            print("Total time for number ", self.number, " is ", self.total_time)
            print('#'*20)           
            self.flag = False
        
    def reset(self):
        print('Do you want to reset the timer?')
        answer = input('y/n')
        if answer == 'y':
            self.total_time = 0
            print("Timer reset")
        self.total_time = 0


#
# ICH_SEGMENTER_V2Widget
class ICH_SEGMENTER_V2Widget(ScriptedLoadableModuleWidget, VTKObservationMixin):
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
    self.ICH_segm_name = None
    self.predictions_names= None
    self.DefaultDir = DEFAULT_VOLUMES_DIRECTORY

    # ----- ANW Addition  ----- : Initialize called var to False so the timer only stops once
    self.called = False
    self.called_onLoadPrediction = False
    
    self.LB_HU = 30
    self.UB_HU = 90
    #   #Initialize timers (unique to each patients)
    self.timer1 = Timer(number=1)
    self.timer2 = Timer(number=2)
    self.timer3 = Timer(number=3)
    self.MostRecentPausedCasePath = ""

    
        # Add margin to the sides



  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ### Segment editor widget
    self.layout.setContentsMargins(4, 0, 4, 0)

    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/ICH_SEGMENTER_V4.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = ICH_SEGMENTER_V2Logic()
    
  
    self.ui.PauseTimerButton.setText('Pause')
    self.ui.getDefaultDir.connect('clicked(bool)', self.getDefaultDir)
    self.ui.BrowseFolders.connect('clicked(bool)', self.onBrowseFoldersButton)
    self.ui.SlicerDirectoryListView.clicked.connect(self.getCurrentTableItem)
    self.ui.ICHSegm.connect('clicked(bool)', self.onICHSegm)
    self.ui.IVHSegm.connect('clicked(bool)', self.onIVHSegm)
    self.ui.PHESegm.connect('clicked(bool)', self.onPHESegm)
    self.ui.SaveSegmentationButton.connect('clicked(bool)', self.onSaveSegmentationButton)
    self.ui.BrowseFolders_2.connect('clicked(bool)', self.onBrowseFolders_2Button)
    self.ui.LoadPrediction.connect('clicked(bool)', self.load_mask_v2)
    self.ui.Previous.connect('clicked(bool)', self.onPreviousButton)
    self.ui.Next.connect('clicked(bool)', self.onNextButton)
    self.ui.pushButton_Paint.connect('clicked(bool)', self.onPushButton_Paint)
    self.ui.PushButton_segmeditor.connect('clicked(bool)', self.onPushButton_segmeditor)  
    self.ui.pushButton_Erase.connect('clicked(bool)', self.onPushButton_Erase)  
    self.ui.pushButton_Smooth.connect('clicked(bool)', self.onPushButton_Smooth)  
    self.ui.pushButton_Small_holes.connect('clicked(bool)', self.onPushButton_Small_holes)  
    self.ui.pushButton_ICH_select.connect('clicked(bool)', self.onPushButton_select_ICH)
    self.ui.pushButton_IVH_select.connect('clicked(bool)', self.onPushButton_select_IVH)
    self.ui.pushButton_PHE_select.connect('clicked(bool)', self.onPushButton_select_PHE)
    self.ui.pushButton_SemiAutomaticPHE.connect('clicked(bool)', self.onPushButton_SemiAutomaticPHE)

    self.ui.StartTimerButton.connect('clicked(bool)', self.toggleStartTimerButton)
    self.enableStartTimerButton()

    self.ui.ThresholdLabel.setStyleSheet("font-weight: bold")
    self.ui.UB_HU.setMinimum(-32000)
    self.ui.LB_HU.setMinimum(-32000)
    self.ui.UB_HU.setMaximum(29000)
    self.ui.LB_HU.setMaximum(29000)

    ### ANW CONNECTIONS
    # Pause button
    self.ui.PauseTimerButton.connect('clicked(bool)', self.togglePauseTimerButton)

    # disable pause, segment, and paint buttons before "start" 
    self.disablePauseTimerButton()
    self.disableSegmentAndPaintButtons()

    # Toggle on of fill button
    self.ui.pushButton_ToggleFill.connect('clicked(bool)', self.toggleFillButton)
    self.ui.pushButton_ToggleFill.setStyleSheet("background-color : indianred")
    # Toggle on of segmentation editor
    self.ui.SegmentWindowPushButton.connect('clicked(bool)', self.onSegmendEditorPushButton)
    self.ui.SegmentWindowPushButton.setStyleSheet("background-color : lightgray")
    # self.ui.radioButton_Edema.connect('clicked(bool)', self.onCheckEdema)

    # Change color of lcd screen
    self.ui.lcdNumber.setStyleSheet("background-color : black")
    
    # Change the value of the upper and lower bound of the HU
    self.ui.UB_HU.setValue(self.UB_HU)
    self.ui.LB_HU.setValue(self.LB_HU)
    self.ui.UB_HU.valueChanged.connect(self.onUB_HU)
    self.ui.LB_HU.valueChanged.connect(self.onLB_HU)

    ### ANW ICH TYPE/LOCATION CONNECTIONS
    self.listichtype = [self.ui.ichtype1, self.ui.ichtype2, self.ui.ichtype3, self.ui.ichtype4, self.ui.ichtype5,
                        self.ui.ichtype6, self.ui.ichtype7, self.ui.ichtype8, self.ui.ichtype9]
    self.listichloc = [self.ui.ichloc1, self.ui.ichloc2, self.ui.ichloc3, self.ui.ichloc4, self.ui.ichloc5,
                       self.ui.ichloc6, self.ui.ichloc7, self.ui.ichloc8, self.ui.ichloc9, self.ui.ichloc10]

    self.listEMs = [self.ui.EM_barras_density, self.ui.EM_barras_margins, self.ui.EM_black_hole, self.ui.EM_blend,
                    self.ui.EM_fl_level, self.ui.EM_hypodensity, self.ui.EM_island, self.ui.EM_satellite, self.ui.EM_swirl]
  
  def setUpperAndLowerBoundHU(self, inputLB_HU, inputUB_HU):
      self.LB_HU = inputLB_HU
      self.UB_HU = inputUB_HU
      self.ui.UB_HU.setValue(self.UB_HU)
      self.ui.LB_HU.setValue(self.LB_HU)
  
  def enableSegmentAndPaintButtons(self):
    self.ui.ICHSegm.setEnabled(True)
    self.ui.IVHSegm.setEnabled(True)
    self.ui.PHESegm.setEnabled(True)
    self.ui.pushButton_ICH_select.setEnabled(True)
    self.ui.pushButton_IVH_select.setEnabled(True)
    self.ui.pushButton_PHE_select.setEnabled(True)

  def disableSegmentAndPaintButtons(self):
    self.ui.ICHSegm.setEnabled(False)
    self.ui.IVHSegm.setEnabled(False)
    self.ui.PHESegm.setEnabled(False)
    self.ui.pushButton_ICH_select.setEnabled(False)
    self.ui.pushButton_IVH_select.setEnabled(False)
    self.ui.pushButton_PHE_select.setEnabled(False)
    
  def getDefaultDir(self):
      self.DefaultDir = qt.QFileDialog.getExistingDirectory(None,"Open default directory", self.DefaultDir, qt.QFileDialog.ShowDirsOnly)
      print(f'This is the Default Directory : {self.DefaultDir}')

  def onBrowseFoldersButton(self):
      print('Clicked Browse Button')
    #   print(f'Current path {self.DefaultDir}')
      # LLG get dialog window to ask for directory
      self.CurrentFolder= qt.QFileDialog.getExistingDirectory(None,"Open a folder", self.DefaultDir, qt.QFileDialog.ShowDirsOnly)
    #   print('Current Folder')
    #   print(self.CurrentFolder)
      self.updateCurrentFolder()
      # LLG GET A LIST OF cases WITHIN CURRENT FOLDERS (SUBDIRECTORIES). List comp to get only the case
    #   print(f'{self.CurrentFolder}{os.sep}{VOLUME_FILE_TYPE}')
      self.CasesPaths = sorted(glob(f'{self.CurrentFolder}{os.sep}{VOLUME_FILE_TYPE}'))
    #   print('Case paths::::')
    #   print(self.CasesPaths)
      self.Cases = sorted([re.findall(r'Volume_(ID_[a-zA-Z\d]+)',os.path.split(i)[-1])[0] for i in self.CasesPaths])
    #   print('Case numbers::::')
    #   print(self.Cases)
      self.ui.SlicerDirectoryListView.clear()
      # Populate the SlicerDirectoryListView
      self.ui.SlicerDirectoryListView.addItems(self.Cases)
      # List view s
    #   self.ui.SlicerDirectoryListView.clicked.connect(self.getCurrentTableItem)
      # # SET CURRENT INDEX AT 0 === THIS IS THE CENTRAL THING THAT HELPS FOR CASE NAVIGATION
      self.currentCase_index = 0
      self.updateCaseAll()
      self.loadPatient()


      """_summary_
      2 ways to update self.currentCase_index:
      1. When the user clicks on the list view
      2. When the user clicks on the next or previous button
      """

  def updateCaseAll(self):
      # All below is dependent on self.currentCase_index updates, 
      self.currentCase = self.Cases[self.currentCase_index]
      self.currentCasePath = self.CasesPaths[self.currentCase_index]
    #   self.updateCaseIndexQLineEdit(self.currentCase_index)
      self.updateCurrentPatient()
      # Highlight the current case in the list view (when pressing on next o)
      self.ui.SlicerDirectoryListView.setCurrentItem(self.ui.SlicerDirectoryListView.item(self.currentCase_index))
    #   self.ui.SlicerDirectoryListView.updateCaseIndexQLineEdit(self.currentCase_index)

      
  def getCurrentTableItem(self):
      # ----- ANW Addition ----- : Reset timer when change case and uncheck all checkboxes
      self.resetTimer()
      self.uncheckAllBoxes()
      self.clearTexts()

      # When an item in SlicerDirectroyListView is selected the case number is printed
      #below we update the case index and we need to pass one parameter to the methods since it takes 2 (1 in addition to self)
      self.updateCaseIndex(self.ui.SlicerDirectoryListView.currentRow) # Index starts at 0
      # Update the case index
      self.currentCase_index = self.ui.SlicerDirectoryListView.currentRow
      # Same code in onBrowseFoldersButton, need to update self.currentCase
      # note that updateCaseAll() not implemented here - it is called when a case is selected from the list view or next/previous button is clicked
      self.currentCase = self.Cases[self.currentCase_index]
      self.currentCasePath = self.CasesPaths[self.currentCase_index]
      self.updateCurrentPatient()
      self.loadPatient()
      print('*'*50)
      print(f'Current case in SlicerDirectroyListView ::: {self.ui.SlicerDirectoryListView.currentItem().text()}')
      # Below gives the row number == index to be used to select elements in the list
      print(f'Current row in  SlicerDirectroyListView ::: {self.ui.SlicerDirectoryListView.currentRow}')
      print('Current caseCase_index :::', self.currentCase_index)

      # self.updateCurrentFolder()
      # self.loadPatient()

      # ----- ANW Addition ----- : Reset timer when change case, also reset button status
      self.resetTimer()

  def updateCaseIndex(self, index):
      # ----- ANW Modification ----- : Numerator on UI should start at 1 instead of 0 for coherence
      self.ui.FileIndex.setText('{} / {}'.format(index+1, len(self.Cases)))

  def updateCurrentFolder(self):
      # self.ui.CurrecntFolder.setText(os.path.join(self.CurrentFolder,self.currentCase))
      self.ui.CurrentFolder.setText('Current folder : \n...{}'.format(self.CurrentFolder[-80:]))
      
  def updateCurrentPatient(self):
      self.ui.CurrentPatient.setText(f'Current case : {self.currentCase}')
      self.updateCaseIndex(self.currentCase_index)
  
  def updateCurrentSegmenationLabel(self):
      self.ui.CurrentSegmenationLabel.setText('Current segment : {}'.format(self.ICH_segm_name))
      
  def loadPatient(self):
      slicer.mrmlScene.Clear()
      slicer.util.loadVolume(self.currentCasePath)
      self.VolumeNode = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')[0]
      self.updateCaseAll()
      self.ICH_segm_name = None
      self.ui.CurrentSegmenationLabel.setText('New patient loaded - No segmentation created!')
      # Adjust windowing (no need to use self. since this is used locally)
      Vol_displayNode = self.VolumeNode.GetDisplayNode()
      Vol_displayNode.AutoWindowLevelOff()
      Vol_displayNode.SetWindow(85)
      Vol_displayNode.SetLevel(45)
      self.newSegmentation()

    #  self.startTimer()
    #   self.timer_router()
    #   
# 
  
  # Getter method to get the segmentation node name    - Not sure if this is really useful here. 
  @property
  def segmentationNodeName(self):
    return f'{self.currentCase}_segmentation'
  
      
  def newSegments(self):
      pass
    # #   Generate 3 classes of segmentations automatically
    #   # Create segment names 
    #   self.ICH_segment_name = "{}_ICH".format(self.currentCase)
    #   self.IVH_segment_name = "{}_IVH".format(self.currentCase)
    #   self.PHE_segment_name = "{}_PHE".format(self.currentCase)
    #   print(f'Segmentation name:: {self.ICH_segment_name}')
    #   # Create segment editor widget and node
    #   self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
    #   self.segmentEditorNode = self.segmentEditorWidget.mrmlSegmentEditorNode()
    #   # Create segmentation node
    #   self.segmentationNode=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    #   # Set segmentation node name
    #   self.segmentationNode.SetName(self.segmentationNodeName)
    #   # Set segmentation node to segment editor
    #   self.segmentEditorWidget.setSegmentationNode(self.segmentationNode)
    #   # Set master volume node to segment editor
    #   self.segmentEditorWidget.setMasterVolumeNode(self.VolumeNode)
    #   # set refenrence geometry to Volume node (important for the segmentation to be in the same space as the volume)
    #   self.segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.VolumeNode)
    #   #below will add a 'segment' in the segmentatation node which is called 'self.ICH_segm_name (for each of the 3 classes)
    #   self.addedSegmentID = self.segmentationNode.GetSegmentation().AddEmptySegment(self.ICH_segment_name)
    #   self.addedSegmentID = self.segmentationNode.GetSegmentation().AddEmptySegment(self.IVH_segment_name)
    #   self.addedSegmentID = self.segmentationNode.GetSegmentation().AddEmptySegment(self.PHE_segment_name)
      
      
    # #   # Get the shn thing to retrieve the segment names <enums for the segment names>
    # #   self.shn = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    # #   self.items = vtk.vtkIdList()
    # #   self.sc = self.shn.GetSceneItemID()
    # #   self.shn.GetItemChildren(self.sc, self.items, True)
      
      
    #   #Initialize timers (unique to each patients)
    #   self.timer1 = Timer(number=1)
    #   self.timer2 = Timer(number=2)
    #   self.timer3 = Timer(number=3)
      
  def onPushButton_NewMask(self):
      self.newSegments()
      
            
  def onPreviousButton(self):
      # ----- ANW Addition ----- : Reset timer when change case and uncheck all checkboxes
      self.resetTimer()
      self.uncheckAllBoxes()
      self.clearTexts()

      #Code below avoid getting in negative values. 
      self.currentCase_index = max(0, self.currentCase_index-1)
      print('Previous clicked', self.currentCase_index)
      # self.updateCaseAll()
      self.updateCaseAll()
      self.loadPatient()


  

  def onNextButton(self):
      # ----- ANW Addition ----- : Reset timer when change case and uncheck all checkboxes
      self.resetTimer()
      self.uncheckAllBoxes()
      self.clearTexts()

      print('Clicked Next Button', self.DefaultDir)
      # ----- ANW Modification ----- : Since index starts at 0, we need to do len(cases)-1 (instead of len(cases)+1).
      # Ex. if we have 10 cases, then len(case)=10 and index goes from 0-9,
      # so we have to take the minimum between len(self.Cases)-1 and the currentCase_index (which is incremented by 1 everytime we click the button)
      self.currentCase_index = min(len(self.Cases)-1, self.currentCase_index+1)
      # self.updateCaseAll()
      self.updateCaseAll()
      # self.currentCase = os.path.join(self.CurrentFolder,self.Cases[self.currentCase_index])
      self.loadPatient()
      print('*'*50)
      print('Next clicked, current caseCase_index :::', self.currentCase_index)




  def newSegmentation(self):
       #   Generate 3 classes of segmentations automatically
    #   # Create segment names 

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
      self.segmentEditorWidget.setMasterVolumeNode(self.VolumeNode)
      # set refenrence geometry to Volume node (important for the segmentation to be in the same space as the volume)
      segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.VolumeNode)
      self.new3Segments() # generate 3 segments at load time
      
  
  # Load all segments at once    
  def new3Segments(self):
        self.onICHSegm()
        self.onIVHSegm()
        self.onPHESegm()
        self.onPushButton_select_ICH() # select ICH segment by default

        # self.startTimer()

  def newSegment(self, segment_name=None):
    
      self.segment_name = f"{self.currentCase}_{segment_name}"
      print(f'Current segment name is {self.segment_name}')
      srcNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      srcSegmentation = srcNode.GetSegmentation()
      print(f'src Segmentation IDs :: {srcSegmentation.GetSegmentIDs()}')
      print(f'segment name :: {segment_name}')
      

      #Below will create a new segment if there are no segments in the segmentation node, avoid overwriting existing segments
      if not srcSegmentation.GetSegmentIDs(): # if there are no segments in the segmentation node
        print(f'Creating new segment {self.segment_name}')
        self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
        self.segmentationNode.GetSegmentation().AddEmptySegment(self.segment_name)
      
      # if there are segments in the segmentation node, check if the segment name is already in the segmentation node
      
      if any([self.segment_name in i for i in srcSegmentation.GetSegmentIDs()]):
            print('segment already exists, not creating a new one')
      else:
            print(f'Creatin a new segment {self.segment_name}')
            self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
            self.segmentationNode.GetSegmentation().AddEmptySegment(self.segment_name)

      return self.segment_name

  def onICHSegm(self):
      self.ICH_segment_name = self.newSegment('ICH')  
    #   slicer.util.selectModule("SegmentEditor")
      # below is the code to select the segment in the segment editor (from the segmentation node))
      self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      Segmentation = self.segmentationNode.GetSegmentation()
      self.SegmentID = Segmentation.GetSegmentIdBySegmentName(self.ICH_segment_name)
      print(f'this is the segment ID {self.SegmentID}')
      segmentICH = Segmentation.GetSegment(self.ICH_segment_name)
      segmentICH.SetColor(255/255,10/255,10/255) # set color to red
      self.onPushButton_select_ICH()
      
      # import vtkSegmentationCorePython as vtkSegmentationCore
      # segmentationNode = getNode('Segmentation')
      # segmentation = segmentationNode.GetSegmentation()
      # segment = segmentation.GetSegment(segmentation.GetNthSegmentID(0))
      # segment.SetColor(0,0,1)


  def onIVHSegm(self):
      # slicer.util.selectModule("SegmentEditor")
      self.IVH_segment_name = self.newSegment('IVH') 
      self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      Segmentation = self.segmentationNode.GetSegmentation()
      self.SegmentID = Segmentation.GetSegmentIdBySegmentName(self.IVH_segment_name)
    #   self.segment_name3 = self.shn.GetItemName(self.items.GetId(3))
      segmentIVH = Segmentation.GetSegment(self.IVH_segment_name)
      segmentIVH.SetColor(230/255,230/255,70/255) #set color to yellow
      self.onPushButton_select_IVH()

    #   self.startTimer()
    #   self.called = False    
    #   self.segment_category = 'IVH'

    
  def onPHESegm(self):
      self.PHE_segment_name = self.newSegment('PHE') 
    
      self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      Segmentation = self.segmentationNode.GetSegmentation()
      self.SegmentID = Segmentation.GetSegmentIdBySegmentName(self.PHE_segment_name)
    #   self.segment_name4 = self.shn.GetItemName(self.items.GetId(4))
      segmentPHE = Segmentation.GetSegment(self.PHE_segment_name)
      segmentPHE.SetColor(11/255,80/255,255/255) #set color to blue
      self.onPushButton_select_PHE()


      # ----- ANW Addition ----- : Reset called to False when new segmentation is created to restart the timer
    #   self.called = False
    #   self.segment_category = 'PHE'

   
#   def time_allocation(self):
#       if self.segment_category == 'ICH':
#           self.ICH_time += self.total_time
#       if self.segment_category == 'IVH':
#           self.IVH_time += self.total_time
#       if self.segment_category == 'PHE':
#           self.PHE_time += self.total_time 
   
  def onPushButton_select_ICH(self):  
      print('selecting ICH segment')
      self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      Segmentation = self.segmentationNode.GetSegmentation()
      self.SegmentID = Segmentation.GetSegmentIdBySegmentName(self.ICH_segment_name)
      self.segmentEditorNode.SetSelectedSegmentID(self.SegmentID)
      self.updateCurrentSegmenationLabel()
      self.setUpperAndLowerBoundHU(30, 90)
      self.onPushButton_Paint()
  
      self.number=1
      if (self.MostRecentPausedCasePath != self.currentCasePath):
        self.timer1 = Timer(number=1) # new path, new timer
      else:
        self.timer1.start() # same path, restart same timer 

      self.timer_router()
      print(f'this is the current active segment {self.SegmentID}')
      
  def onPushButton_select_IVH(self):
      print('selecting IVH segment')
      self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      Segmentation = self.segmentationNode.GetSegmentation()
      self.SegmentID = Segmentation.GetSegmentIdBySegmentName(self.IVH_segment_name)
      self.segmentEditorNode.SetSelectedSegmentID(self.SegmentID)
      self.updateCurrentSegmenationLabel()
      self.setUpperAndLowerBoundHU(30, 90)
      self.onPushButton_Paint()
  
      self.number=2
      if (self.MostRecentPausedCasePath != self.currentCasePath):
        self.timer2 = Timer(number=2) # new path, new timer
      else:
        self.timer2.start() # same path, restart same timer 
      self.timer_router()
      print(f'this is the current active segment {self.SegmentID}')
      
      
  def onPushButton_select_PHE(self):
      print('selecting PHE segment')
      self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      Segmentation = self.segmentationNode.GetSegmentation()
      self.SegmentID = Segmentation.GetSegmentIdBySegmentName(self.PHE_segment_name)
      self.segmentEditorNode.SetSelectedSegmentID(self.SegmentID)
      self.updateCurrentSegmenationLabel()
      self.setUpperAndLowerBoundHU(5, 33)
      self.onPushButton_Paint()
  
      self.number=3
      if (self.MostRecentPausedCasePath != self.currentCasePath):
        self.timer3 = Timer(number=3) # new path, new timer
      else:
        self.timer3.start() # same path, restart same timer 
      self.timer_router()
      print(f'this is the current active segment {self.SegmentID}')

  def onPushButton_SemiAutomaticPHE(self):
      print("Pushed Semi-automatic PHE button :)")
      toolWindow = SemiAutoPheToolThresholdWindow(self)
      toolWindow.show()
 
 #### TIMER BLOCK ####
      
  def startTimer(self):
      print('ICH segment name::: {}'.format(self.ICH_segment_name))
      self.counter = 0
      # Add flag to avoid counting time when user clicks on save segm button
      self.flag2 = True
      print("STARTING TIMER !!!!")

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
      if self.flag2: # add flag to avoid counting time when user clicks on save segm button
            # the timer sends a signal every second (1000 ms). 
          self.counter += 1  # the self.timer.timeout.connect(self.updatelcdNumber) function is called every second and updates the counter

      self.ui.lcdNumber.display(self.counter/10)


  def stopTimer(self):
      # If already called once (i.e when user pressed save segm button but forgot to annotator name), simply return the time
      if self.called:
          return self.total_time
      else:
          try:
              print('STOPPING TIMER!')
              self.total_time = self.counter/10
              self.timer.stop()
              print(f"Total segmentation time: {self.total_time} seconds")
              self.flag2 = False  # Flag is for the timer to stop counting
              self.called = True
            #   self.time_allocation()
              return self.total_time
          except AttributeError as e:
              print(f'!!! YOU DID NOT START THE COUNTER !!! :: {e}')
              return None

  def resetTimer(self):
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

  # def togglePauseTimerButton(self):
  #     # if button is checked
  #     if self.ui.PauseTimerButton.isChecked():
  #         # setting background color to light-blue
  #         self.ui.PauseTimerButton.setStyleSheet("background-color : lightblue")
  #         self.ui.PauseTimerButton.setText('Restart')
  #         self.intermediate_time = round((time.perf_counter() - self.start_time), 2)
  #         self.timer.stop()
  #
  #     # if it is unchecked
  #     else:
  #         # set background color back to light-grey
  #         self.ui.PauseTimerButton.setStyleSheet("background-color : lightgrey")
  #         self.ui.PauseTimerButton.setText('Pause')
  #         self.timer.start(1000)

  def toggleStartTimerButton(self):
      if (self.ui.SlicerDirectoryListView.count > 0):
        if self.ui.StartTimerButton.isChecked():
            self.startTimer()

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
          self.timer1.stop()
          self.timer2.stop()
          self.timer3.stop()
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
          self.flag = True

          self.enableSegmentAndPaintButtons()

  # for the timer Class not the LCD one
  def timer_router(self):
      # Create dictionary of timers methods to call based on the number
      self.dict_router = {
        1: self.timer1, 
        2: self.timer2,
        3: self.timer3
        }
    
      # Excute the method
      # using get method to avoid key error if the number is not in the dictionary (not instanciated)
      # Stat the time with self.number flag (active label)
      self.dict_router.get(self.number).start()
      # Uncheck the pause button if it was paused (i.e. restart if we click on the segment)
      self.flag = True
      
      #Below is the most elegant way to do it 
      # stop the other timers (not the one that was just started))
      for key in self.dict_router:
          if key != self.number:
              self.dict_router.get(key).stop()  
      
      # Stop the other timers (not the one that was just started))
      # Not the best way to do it but it works
      # if self.number == 1:
      #     self.timer2.stop()
      #     self.timer3.stop()
      # elif self.number == 2:
      #     self.timer1.stop()
      #     self.timer3.stop()
      # elif self.number == 3:
      #     self.timer1.stop()
      #     self.timer2.stop()
      # else:
      #     print("No timer started")
            
  def createFolders(self):
      self.revision_step = self.ui.RevisionStep.currentText
      if len(self.revision_step) != 0:
          self.output_dir_labels= os.path.join(self.CurrentFolder, f'Labels_{self.annotator_name}_{self.revision_step[0]}') # only get the number
          os.makedirs(self.output_dir_labels, exist_ok=True)
          # add a subfolder with nifti segmentations
          self.output_dir_labels_nii = os.path.join(self.CurrentFolder, f'Labels_nii_{self.annotator_name}_{self.revision_step[0]}')
          os.makedirs(self.output_dir_labels_nii, exist_ok=True)
          # Create separate folder
          self.output_dir_time= os.path.join(self.CurrentFolder, f'Time_{self.annotator_name}_{self.revision_step[0]}')
          os.makedirs(self.output_dir_time, exist_ok=True)
    
          self.output_dir_vol_nii= os.path.join(self.CurrentFolder, f'Volumes_nii')
          os.makedirs(self.output_dir_vol_nii, exist_ok=True)
          
      else:
          print('Please select revision step !!!')
          msgboxtime = qt.QMessageBox()
          msgboxtime.setText("Segmentation not saved : revision step is not defined!  \n Please save again with revision step!")
          msgboxtime.exec()



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
      self.checked_ichtype = ','.join(self.checked_ichtype)
      self.checked_ichloc = ','.join(self.checked_ichloc)
      self.checked_ems = ','.join(self.checked_ems)
      return self.checked_ichtype, self.checked_ichloc, self.checked_ems

  def uncheckAllBoxes(self):
      self.allcheckboxes = self.listichtype + self.listichloc + self.listEMs
      for i in self.allcheckboxes:
          i.setChecked(False)

  def clearTexts(self):
      self.ui.ichtype_other.clear()
      self.ui.EM_comments.clear()


  # def rearrangeNRRDSegments(self):
  #     # Ideally, we would implement this: https://github.com/Slicer/Slicer/issues/5044 but I don't know how...
  #     # open the tmp file, rearrange, save new rearranged file and remove tmp file.
  #     # I tried to overwrite the original file without using tmp file but it doesn't work...
  #     self.srcFile = self.tmp
  #     self.dstFile = os.path.join(self.output_dir_labels,
  #                                 "{}_{}_{}.seg.nrrd".format(self.currentCase, self.annotator_name,
  #                                                            self.revision_step[0]))
  #
  #     segment_names_to_labels = [(self.ICH_segment_name, 1), (self.IVH_segment_name, 2), (self.PHE_segment_name, 3)]
  #
  #     segmentation_info = slicerio.read_segmentation_info(self.srcFile)
  #     voxels, header = nrrd.read(self.srcFile)
  #     extracted_voxels, extracted_header = slicerio.extract_segments(voxels, header, segmentation_info,
  #                                                                    segment_names_to_labels)
  #     nrrd.write(self.dstFile, extracted_voxels, extracted_header)
  #     os.remove(self.tmp)




  # ----- Modification -----
  def onSaveSegmentationButton(self):
      #By default creates a new folder in the volume directory 
      # Stop the timer when the button is pressed
      self.time = self.stopTimer()
      #Stop timer of the Timer class
      for v in self.dict_router.values():
            v.stop()
      self.annotator_name = self.ui.Annotator_name.text
      self.annotator_degree = self.ui.AnnotatorDegree.currentText

      # get ICH types and locations
      self.checked_ichtype, self.checked_ichloc, self.checked_ems = self.checkboxChanged()
      self.ichtype_other = self.ui.ichtype_other.text
      self.em_comments = self.ui.EM_comments.text

      
      # Create folders if not exist
      self.createFolders()
      
      # Make sure to select the first segmentation node  (i.e. the one that was created when the module was loaded, not the one created when the user clicked on the "Load mask" button)
      self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]


      # Save if annotator_name is not empty and timer started:
      if self.annotator_name and self.time is not None:
          print('Saving time')
          print(f'total time for ICH:: {self.timer1.total_time:0.2f}')
          print(f'total time for IVH:: {self.timer2.total_time:0.2f}')
          print(f'total time for PHE:: {self.timer3.total_time:0.2f}')  
          # Save time to csv
          self.df = pd.DataFrame(
              {'Case number': [self.currentCase], 
               'Annotator Name': [self.annotator_name], 
               'Annotator degree': [self.annotator_degree],
               'Time': [self.ui.lcdNumber.value], 
               'Revision step': [self.revision_step[0]], 
               'Time ICH':[self.timer1.total_time], 
               'Time IVH':[self.timer2.total_time], 
               'Time PHE':[self.timer3.total_time], 
               'ICH type': self.checked_ichtype,
               'ICH location': self.checked_ichloc,
               'Expansion markers': self.checked_ems,
               'Other ICH type': [self.ichtype_other],
               'Other expansion markers': [self.em_comments]})
          self.outputTimeFile = os.path.join(self.output_dir_time,
                                             '{}_Case_{}_time_{}.csv'.format(self.annotator_name, self.currentCase, self.revision_step[0]))
          if not os.path.isfile(self.outputTimeFile):
              self.df.to_csv(self.outputTimeFile)
          else:
              print('This time file already exists, appending new line to file!')
              self.df.to_csv(self.outputTimeFile, mode='a', header=False)

          # Save .seg.nrrd file
          
          self.outputSegmFile = os.path.join(self.output_dir_labels,
                                                 "{}_{}_{}.seg.nrrd".format(self.currentCase, self.annotator_name, self.revision_step[0]))

          # self.tmp = os.path.join(self.output_dir_labels,
          #                         "{}_{}_{}_tmp.seg.nrrd".format(self.currentCase, self.annotator_name,
          #                                                        self.revision_step[0]))

          if not os.path.isfile(self.outputSegmFile):
              slicer.util.saveNode(self.segmentationNode, self.outputSegmFile )
              # slicer.util.saveNode(self.segmentationNode, self.tmp)

          else:
              print('This .nrrd file already exists')
              msg2 = qt.QMessageBox()
              msg2.setWindowTitle('Save As')
              msg2.setText(
                  f'The file {self.currentCase}_{self.annotator_name}_{self.revision_step[0]}.seg.nrrd already exists \n Do you want to replace the existing file?')
              msg2.setIcon(qt.QMessageBox.Warning)
              msg2.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
              msg2.buttonClicked.connect(self.msg2_clicked)
              msg2.exec()

          # self.rearrangeNRRDSegments()

          # Save alternative nitfi segmentation
          # Export segmentation to a labelmap volume
          # Note to save to nifti you need to convert to labelmapVolumeNode
          self.labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
          slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(self.segmentationNode,
                                                                                   self.labelmapVolumeNode,
                                                                                   self.VolumeNode)

          self.outputSegmFileNifti = os.path.join(self.output_dir_labels_nii,
                                                  "{}_{}_{}.nii.gz".format(self.currentCase, self.annotator_name, self.revision_step[0]))

          if not os.path.isfile(self.outputSegmFileNifti):
              slicer.util.saveNode(self.labelmapVolumeNode, self.outputSegmFileNifti)
          else:
              print('This .nii.gz file already exists')
              msg3 = qt.QMessageBox()
              msg3.setWindowTitle('Save As')
              msg3.setText(
                  f'The file {self.currentCase}_{self.annotator_name}_{self.revision_step[0]}.nii.gz already exists \n Do you want to replace the existing file?')
              msg3.setIcon(qt.QMessageBox.Warning)
              msg3.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
              msg3.buttonClicked.connect(self.msg3_clicked)
              msg3.exec()

          # Saving messages
          print((f'Saving case : {self.VolumeNode.GetName()}'))
          self.ui.CurrentSegmenationLabel.setText(f'Case {self.VolumeNode.GetName()} saved !')
          
          # Saving a nii.gz version of the volume
          self.outputVolfile = os.path.join(self.output_dir_vol_nii,"{}.nii.gz".format(self.currentCase))
          
          if not os.path.isfile(self.outputVolfile):
              slicer.util.saveNode(self.VolumeNode, self.outputVolfile)
          else:
              print('This .nii.gz file already exists')
              msg4 = qt.QMessageBox()
              msg4.setWindowTitle('Save As')
              msg4.setText(
                  f'The file {self.currentCase}.nii.gz already exists \n Do you want to replace the existing file?')
              msg4.setIcon(qt.QMessageBox.Warning)
              msg4.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
              msg4.buttonClicked.connect(self.msg4_clicked)
              msg4.exec()

      # If annotator_name empty or timer not started.
      else:
          if not self.annotator_name:
              print('Empty annotator name !!!')
              msgboxtime = qt.QMessageBox()
              msgboxtime.setText("Segmentation not saved : no annotator name !  \n Please save again with your name!")
              msgboxtime.exec()
          elif self.time is None:
              print('You did not start the timer !!!')
              msgboxtime = qt.QMessageBox()
              msgboxtime.setText(
                  "You did not start a timed segmentation. \n Please press the 'New ICH segm' button to start a timed segmentation")
              msgboxtime.exec()


      try:
        self.SlicerVolumeName = re.findall('Volume_(ID_[a-zA-Z\d]+)', self.VolumeNode.GetName())[0]
        print(f'Volume Node accoding to slicer :: {self.SlicerVolumeName}')
        print('Volume Name according to GUI: {}'.format(self.currentCase))
        assert self.currentCase == self.SlicerVolumeName
        print('Matched Volume number (sanity check)!')
      except AssertionError as e:
        print('Mismatch in case error :: {}'.format(str(e)))
      
      
      # #delete instances of class timer (regenerated when  new case loaded)
      # del self.timer1, self.timer2, self.timer3
      # self.time = 0

  def msg2_clicked(self, msg2_button):
      if msg2_button.text == 'OK':
          slicer.util.saveNode(self.segmentationNode, self.outputSegmFile)
          # slicer.util.saveNode(self.segmentationNode, self.tmp)
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
      self.predictionFolder= qt.QFileDialog.getExistingDirectory(None,"Open a folder", self.DefaultDir, qt.QFileDialog.ShowDirsOnly)

      self.predictions_paths = sorted(glob(os.path.join(self.predictionFolder, f'{SEGM_FILE_TYPE}')))
      print(self.predictions_paths)

      try:
        assert len(self.CasesPaths) == (len(self.predictions_paths) or len(self.predictions_paths_NIFTI))
      except AssertionError as e:
        print('Not the same number of Volumes and predictions !')
        msgboxpred = qt.QMessageBox()
        msgboxpred.setText("Not the same number of Volumes and predictions !")
        msgboxpred.exec()
      
      # self.prediction_name = 

  def msg_warnig_delete_segm_node_clicked(self, msg_warnig_delete_segm_node_button):
      if msg_warnig_delete_segm_node_button.text == 'OK':
        srcNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
        slicer.mrmlScene.RemoveNode(srcNode)
      else:
          return
    
    
  def load_mask_v2(self):
      # Get list of prediction names
      msg_warnig_delete_segm_node =qt.QMessageBox() # Typo correction
      msg_warnig_delete_segm_node.setText('This will delete the current segementation. Do you want to continue?')
      msg_warnig_delete_segm_node.setIcon(qt.QMessageBox.Warning)
      msg_warnig_delete_segm_node.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
      msg_warnig_delete_segm_node.buttonClicked.connect(self.msg_warnig_delete_segm_node_clicked)
      msg_warnig_delete_segm_node.exec() # calls remove node if ok is clicked
      
    #   msgnopredloaded.exec()
    #   # Then load the browse folder thing for the user
    #   self.onBrowseFolders_2Button()
      
      try:
        self.predictions_names = sorted([re.findall(r'(ID_[a-zA-Z\d]+)_segmentation.seg.nrrd',os.path.split(i)[-1]) for i in self.predictions_paths])
        print(self.predictions_names)
        self.called = False # restart timer
      except AttributeError as e:
            msgnopredloaded=qt.QMessageBox() # Typo correction
            msgnopredloaded.setText('Please select the prediction directory!')
            msgnopredloaded.exec()
            # Then load the browse folder thing for the user
            self.onBrowseFolders_2Button()
      # Match the prediction names that corresponds to the loaded segmentatiion
      # self.currentPrediction_Index, self.currentPrediction_ID = [(i,j) for i,j in enumerate(self.predictions_names) if j == self.currentCase][0]
      
      self.currentPrediction_Index, self.currentPrediction_ID = [(i, self.predictions_names[i]) for i in range(len(self.predictions_names)) if i == self.currentCase_index][0] # return a list of tuples
      print(f'Current case :: {self.currentCase}')
      print(f'Current prediction ID :: {self.currentPrediction_ID }')
      print(f'Current case index :: {self.currentCase_index}')
      print(f'Current prediction index :: {self.currentPrediction_Index}')
      
      self.currentPredictionPath = self.predictions_paths[self.currentCase_index]
      print(self.currentPrediction_ID)
      print(self.currentPrediction_Index)
      print(f'Current prediction path :: {self.currentPredictionPath}')
      
      slicer.util.loadSegmentation(self.currentPredictionPath)
    #   self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[1]
      # 'ACTIVATE' segmentation node in Slicer
      # slicer.util.loadSegmentation(self.currentCasePath)
      self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      self.segmentEditorNode =  self.segmentEditorWidget.mrmlSegmentEditorNode()
      self.segmentEditorWidget.setSegmentationNode(self.segmentationNode)
      self.segmentEditorWidget.setMasterVolumeNode(self.VolumeNode)
      # set refenrence geometry to Volume node
      self.segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.VolumeNode)
      # self.segmentationNode= slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLSegmentationNode")
      # if self.segmentationNode:
      #       self._parameterNode.SetNodeReferenceID("InputVolume", self.segmentationNode.GetID())
      nn = self.segmentationNode.GetDisplayNode()
      # set Segmentation visible:
      nn.SetAllSegmentsVisibility(True)
      
      # Update the segmentation name (needed for saving the segmentation)
      self.ICH_segm_name = self.segmentationNode.GetName()

      # Start timer
      # self.startTimer()
      
      #### ADD SEGMENTS THAT ARE NOT IN THE SEGMENTATION ####
      self.onICHSegm()
      self.onIVHSegm()
      self.onPHESegm()

  def onSegmendEditorPushButton(self):

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


      # self.ui.SegmentWindowPushButton.show()


  def onPushButton_Paint(self):
      if self.ui.pushButton_Paint.isChecked():
          self.ui.pushButton_Paint.setStyleSheet("background-color : lightgreen")
          self.ui.pushButton_Paint.setText('Paint Mask ON')
          self.segmentEditorWidget.setActiveEffectByName("Paint")
          # Note it seems that sometimes you need to activate the effect first with :
          # Assign effect to the segmentEditorWidget using the active effect
          self.effect = self.segmentEditorWidget.activeEffect()
          self.effect.activate()
          self.effect.setParameter('BrushSphere',1)
          #Seems that you need to activate the effect to see it in Slicer
          # Set up the mask parameters (note that PaintAllowed...was changed to EditAllowed)
          self.segmentEditorNode.SetMaskMode(slicer.vtkMRMLSegmentationNode.EditAllowedEverywhere)
          #Set if using Editable intensity range (the range is defined below using object.setParameter)
          self.segmentEditorNode.SetMasterVolumeIntensityMask(True)
          self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(self.LB_HU, self.UB_HU)
          self.segmentEditorNode.SetOverwriteMode(slicer.vtkMRMLSegmentEditorNode.OverwriteAllSegments)
      else:
          self.ui.pushButton_Paint.setStyleSheet("background-color : indianred")
          self.ui.pushButton_Paint.setText('Paint Mask OFF')
          self.segmentEditorWidget.setActiveEffectByName("Paint")
          self.effect = self.segmentEditorWidget.activeEffect()
          #Seems that you need to activate the effect to see it in Slicer
          self.effect.activate()
          # Set up the mask parameters (note that PaintAllowed...was changed to EditAllowed)
          self.segmentEditorNode.SetMaskMode(slicer.vtkMRMLSegmentationNode.EditAllowedEverywhere)
          #Set if using Editable intensity range (the range is defined below using object.setParameter)
          self.segmentEditorNode.SetMasterVolumeIntensityMask(False)
          self.segmentEditorNode.SetOverwriteMode(slicer.vtkMRMLSegmentEditorNode.OverwriteAllSegments)
            

  def toggleFillButton(self):
    #   self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      if self.ui.pushButton_ToggleFill.isChecked():
          self.ui.pushButton_ToggleFill.setStyleSheet("background-color : lightgreen")
          self.ui.pushButton_ToggleFill.setText('Fill ON')
          self.segmentationNode.GetDisplayNode().SetOpacity2DFill(0)
      # if it is unchecked
      else:
          self.ui.pushButton_ToggleFill.setStyleSheet("background-color : indianred")
          self.ui.pushButton_ToggleFill.setText('Fill OFF')
          self.segmentationNode.GetDisplayNode().SetOpacity2DFill(100)

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
      #Seems that you need to activate the effect to see it in Slicer
      self.effect.activate()
      self.segmentEditorNode.SetMasterVolumeIntensityMask(False)

  def onPushButton_Smooth(self):
      # pass
      # Smoothing
      self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      self.segmentEditorWidget.setActiveEffectByName("Smoothing")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("SmoothingMethod", "MEDIAN")
      effect.setParameter("KernelSizeMm", 3)
      effect.self().onApply()


      
  def onPushButton_Small_holes(self):
      # pass
      # Fill holes smoothing
      self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      self.segmentEditorWidget.setActiveEffectByName("Smoothing")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("SmoothingMethod", "MORPHOLOGICAL_CLOSING")
      effect.setParameter("KernelSizeMm", 3)
      effect.self().onApply()

  def onLB_HU(self):
      self.LB_HU=self.ui.LB_HU.value

      self.segmentEditorNode.SetMasterVolumeIntensityMask(True)
      self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(self.LB_HU, self.UB_HU)
  
  def onUB_HU(self):
      self.UB_HU=self.ui.UB_HU.value

      self.segmentEditorNode.SetMasterVolumeIntensityMask(True)
      self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(self.LB_HU, self.UB_HU)

#ICH_SEGMENTER_V2Logic
#

class ICH_SEGMENTER_V2Logic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    if not parameterNode.GetParameter("Threshold"):
      parameterNode.SetParameter("Threshold", "100.0")
    if not parameterNode.GetParameter("Invert"):
      parameterNode.SetParameter("Invert", "false")

  def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True):
    """
    Run the processing algorithm.
    Can be used without GUI widget.
    :param inputVolume: volume to be thresholded
    :param outputVolume: thresholding result
    :param imageThreshold: values above/below this threshold will be set to 0
    :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
    :param showResult: show output volume in slice viewers
    """

    if not inputVolume or not outputVolume:
      raise ValueError("Input or output volume is invalid")

    import time
    startTime = time.time()
    logging.info('Processing started')

    # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
    cliParams = {
      'InputVolume': inputVolume.GetID(),
      'OutputVolume': outputVolume.GetID(),
      'ThresholdValue' : imageThreshold,
      'ThresholdType' : 'Above' if invert else 'Below'
      }
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
    # We don't need the CLI module node anymore, remove it to not clutter the scene with it
    slicer.mrmlScene.RemoveNode(cliNode)

    stopTime = time.time()
    logging.info(f'Processing completed in {stopTime-startTime:.2f} seconds')


#
#ICH_SEGMENTER_V2Test


class ICH_SEGMENTER_V2Test(ScriptedLoadableModuleTest):
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
    self.test_ICH_SEGMENTER_V21()

  def test_ICH_SEGMENTER_V21(self):
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

    import SampleData
    registerSampleData()
    inputVolume = SampleData.downloadSample('ICH_SEGMENTER_V21')
    self.delayDisplay('Loaded test data set')

    inputScalarRange = inputVolume.GetImageData().GetScalarRange()
    self.assertEqual(inputScalarRange[0], 0)
    self.assertEqual(inputScalarRange[1], 695)

    outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    threshold = 100

    # Test the module logic

    logic = ICH_SEGMENTER_V2Logic()

    # Test algorithm with non-inverted threshold
    logic.process(inputVolume, outputVolume, threshold, True)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], threshold)

    # Test algorithm with inverted threshold
    logic.process(inputVolume, outputVolume, threshold, False)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], inputScalarRange[1])

    self.delayDisplay('Test passed')
