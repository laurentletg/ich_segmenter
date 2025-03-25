![image](https://github.com/laurentletg/ICH_SEGMENTER_V2/assets/48111184/37787b77-a9e3-4603-a7b4-910a3ecfff5d)
# ich_segmenter
* 3D Slicer extension
* Manual medical image segmentation 

### [Change log](CHANGELOG.md)

![image](https://github.com/laurentletg/ICH_SEGMENTER_V2/blob/main/images/animated_ICH_slice_sweep.gif)

### Overview
This module is currently targeted at the segmentation of intracerebral hemorrhage (ICH), intraventricular hemorrhage (IVH) and perihematomal edema (PHE) in CT scans. It can be adapted to other tasks. 
Among other things, it allows the user to:
* Load a CT scan and its corresponding labels.
* Use thresholding to segment the ICH, IVH and PHE.
* Smooth the segmentations.
* Use standardized filenaming conventions.
* Record the annotatore name, level and revision step in the filenames. 
* Save the segmentations in NRRD format. A separate script is avalaible to convert the NRRD files to NIFTI format.
* Remove outliers from the segmentations based on the corresponding volume Housefield units (HU). For example, if the HU of a voxel is -300, it is likely that the voxel is not part of the ICH and represent air. The upper and lower HU thresholds are configurable in the `label_config.yml` file.
* Perform a QC to check that each label as the right label value. TODO: This part is hard-coded for the moment and works only for ICH = 1, IVH = 2, PHE = 3but could be adapted to be more flexible in the future. A separate is available to perform the later task. 

### Installation steps
1. Install [3D Slicer](https://download.slicer.org).  
2. Clone this repository.
3. Modify `label_config.yml` to describe your annotations. There can be as many or as few as you would like. The colors are configurable using RGB integer values between 0 and 255. The default HU thresholds for each label are also configurable. These can also be modified directly in the extension. Note that additional tools will appear in the user interface if one of the labels is either intracerebral hemorrhage (ICH) or perihematomal edema (PHE). 
4. Open 3D Slicer. 
5. Activate the checkbox `Enable developer mode` in `Edit -> Application Settings -> Developer -> Enable developer mode`. 
6. Add the path of this repository in `Edit -> Application Settings -> Modules -> Additional module paths`. 
    * There might be errors. These would be seen in the Python Console. 
7. The module can be found under `Examples -> SEGMENTER_V2`. 

### Trouble shooting 
* Qt might need to be installed. The first five steps of the following procedure might be useful for this: [procedure](https://web.stanford.edu/dept/cs_edu/resources/qt/install-mac). 
* If some modules are missing (`ModuleNotFoundError`), they must be added to the 3D Slicer environment by using the following commands in the Python Console: 
        `from slicer.util import pip_install`. Alternatively, it is possible to use : slicer.util.pip_install('XYZ')
        `pip_install("XYZ")` where `XYZ` is replaced by the proper library
> Minimally the following packages are not already available (copy and paste in the python interactor):
```py
slicer.util.pip_install('pandas')
slicer.util.pip_install('nibabel')
slicer.util.pip_install('pynrrd')
slicer.util.pip_install('pyyaml')
slicer.util.pip_install('slicerio')
```

### Usage
A configuration file `config.yaml` is required to use the extension. The configuration file is a YAML file that describes the input directories, regular expression pattern to extract the ID from the the labels that will be used for the segmentation.

### TODO:
- [ ] In the future, the IDs won't be incorporated in the segment names, only in the filenames. This will require a change in post-annotation QC script (separate repository).
- [ ] Add the QC check module within the extension and allow to check the label name : value correspondance based on the config file. 

![alt text](https://github.com/laurentletg/ICH_SEGMENTER_V2/blob/main/Slicer%20how%20to%20install%20package.png?raw=true)

### Other extensions that could be useful
* `SlicerJupyter` to be able to use Jupyter Notebooks connected to 3D Slicer. 

### Video tutorials
The videos are much less blurry if the mp4 files are downloaded to your computer. 

[Videos](https://drive.google.com/drive/folders/1iM5r3zn6414RSQQNnYzGXxsDnVgd-KjP?usp=sharing)

### Other resources
* [3D Slicer Tutorials](https://www.youtube.com/watch?v=QTEti9aY0vs&)
* [3D Slicer Documentation](https://www.slicer.org/wiki/Documentation/Nightly/Training)
