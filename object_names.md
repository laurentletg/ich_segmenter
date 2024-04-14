
# Folders
`CurrentFolder`: folder containg the volumes ('main working directory')
`output_dir`: top folder with outputs (segmentations and csv)
`self.output_seg_dir`: folder with segmentations
# Filenames
Main filename
```py
"{}_{}_{}.{}".format(output_file_pt_id_instanceUid, self.annotator_name, self.revision_step[0], extension)
```