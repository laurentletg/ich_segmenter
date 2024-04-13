# Change Log

**All notable changes to this project will be documented in this file.**


## [2.1.1] - 2024-04-12

### Added
- Colored row in the patient list. Updates after saving a  segmentation. Will compare the list of cases to be annotated with the one in the output folder.This will highlight the changes in red and green. 
> ![Colored list.png](images%2FColored%20list.png)
- Added method to nest patient --> study -- > volume and segmentation nodes + added 2 test buttons to ui
- Added button to check and correct data type of the segmentation files. Since Slicer 5.6 this produces an error (screenshot below). A push button above the default directory checks for the dtype and cast to uint8 if not in that format. 
>![Slicer vector error float vs uint8.png](images%2FSlicer%20vector%20error%20float%20vs%20uint8.png)