def load_mask_v2(self):
    # Get list of prediction names
    msg_warning_delete_segm_node = qt.QMessageBox()  # Typo correction
    msg_warning_delete_segm_node.setText('This will delete the current segmentation. Do you want to continue?')
    msg_warning_delete_segm_node.setIcon(qt.QMessageBox.Warning)
    msg_warning_delete_segm_node.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
    # if clikc ok, then delete the current segmentatio
    msg_warning_delete_segm_node.setDefaultButton(qt.QMessageBox.Cancel)
    response = msg_warning_delete_segm_node.exec()  # calls remove node if ok is clicked
    if response == qt.QMessageBox.Ok:
        self.msg_warnig_delete_segm_node_clicked(msg_warning_delete_segm_node)
    else:
        return

    try:
        self.predictions_names = sorted(
            [re.findall(self.SEGM_REGEX_PATTERN, os.path.split(i)[-1]) for i in self.predictions_paths])
        self.called = False  # restart timer
    except AttributeError as e:
        msgnopredloaded = qt.QMessageBox()  # Typo correction
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
        # First load the template segmentation based on the config file
        for label in self.config_yaml["labels"]:
            self.onNewLabelSegm(label["name"], label["color_r"], label["color_g"], label["color_b"],
                                label["lower_bound_HU"], label["upper_bound_HU"])

        # Then load the prediction segmentation

        slicer.util.loadSegmentation(self.currentPredictionPath)
        self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
        self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
        self.segmentEditorNode = self.segmentEditorWidget.mrmlSegmentEditorNode()
        self.segmentEditorWidget.setSegmentationNode(self.segmentationNode)
        self.segmentEditorWidget.setSourceVolumeNode(self.VolumeNode)
        # set refenrence geometry to Volume node
        self.segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.VolumeNode)
        nn = self.segmentationNode.GetDisplayNode()
        # set Segmentation visible:
        nn.SetAllSegmentsVisibility(True)
        self.segmentationNode.GetDisplayNode().SetOpacity2DFill(0)

        # Will not need to copy the segments to the apprpriate templated segments

        sourceSegmentName = "Segment_1"

        segmentation = segmentationNode.GetSegmentation()
        sourceSegmentId = segmentation.GetSegmentIdBySegmentName(sourceSegmentName)
        segmentation.CopySegmentFromSegmentation(segmentation, sourceSegmentId)

        #### ADD SEGMENTS THAT ARE NOT IN THE SEGMENTATION ####

    else:
        msg_no_such_case = qt.QMessageBox()
        msg_no_such_case.setText('There are no mask for this case in the directory that you chose!')
        msg_no_such_case.exec()
