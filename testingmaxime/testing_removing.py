import re
string = "sub-ott003_acq-sag_T2w.nii.gz"
regex = ".nii.gz"

print(string)
cleaned = re.sub(regex, "", string)
print(cleaned)
