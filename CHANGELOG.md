# Change Log

**All notable changes to this project will be documented in this file.**

## [2.1.4] - 2024-08-06
- Fixed the issue with nnunet or any nifti segmentations that loads as _Segment_1_ etc
- Now loads using the config file (remove the id in segment names) and uses the name and colors set in the config file.


```py

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

```

## [2.1.3] - 2024-05-01
- Added the option to get a line measurement for midline shift. Note, it considers only the 2nd measurement available, the first one is typically to get the ideal midline. It saves in the output folder as a csv and a screenshot capture. 
![MLSmeasure.png](images%2FMLSmeasure.png)
- Added a screenshot button save button that also saves the text description in the widget adjacent to it. 
![screeshot.png](images%2Fscreeshot.png)


## [2.1.2] - 2024-04-30

![images/slicertogglefill.gif](https://github.com/laurentletg/ICH_SEGMENTER_V2/blob/main/images/slicertogglefill.gif)
- Possibility to add keyboard shortcuts from the configuration file. Currently only the toggle fill on off is implemente
- Pass the method name (without 'self.' and '()') and the keyboard shortcut. Make sure this does not conflict with the default shortcuts.
```yaml
KEYBOARD_SHORTCUTS: 
  - method: "keyboard_toggle_fill"
    shortcut: "d"
```
Corresponds to section in `SEGMENTER_V2Widget.setup()` immediately after the widget connections. Adapted from the [3D Slicer script repository](https://slicer.readthedocs.io/en/latest/developer_guide/script_repository.html#customize-keyboard-shortcuts)
```py
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
```
For buttons that 'toggles' this method was created:
- [ ] create a more general method that can be used for all buttons that toggle on and off.
```py
  def keyboard_toggle_fill(self):
      print('keyboard_toggle_fill')
      if self.ui.pushButton_ToggleFill.isChecked():
          self.ui.pushButton_ToggleFill.toggle()
          self.toggleFillButton()
      else:
          self.ui.pushButton_ToggleFill.toggle()
          self.toggleFillButton()

```

## [2.1.1] - 2024-04-12

### Added
- Colored row in the patient list. Updates after saving a  segmentation. Will compare the list of cases to be annotated with the one in the output folder.This will highlight the changes in red and green. 
> ![Colored list.png](images%2FColored%20list.png)
- Added method to nest patient --> study -- > volume and segmentation nodes + added 2 test buttons to ui
- Added button to check and correct data type of the segmentation files. Since Slicer 5.6 this produces an error (screenshot below). A push button above the default directory checks for the dtype and cast to uint8 if not in that format. 
>![Slicer vector error float vs uint8.png](images%2FSlicer%20vector%20error%20float%20vs%20uint8.png)
