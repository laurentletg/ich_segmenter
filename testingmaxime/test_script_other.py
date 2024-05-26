print("ceci est un test pour voir si execute fichier python dun endroit "
      "different")



# This script works only in 3DSlicer python console.

################# CONFIG FILE BEGIN ##########################

# Specify the absolute path where you want to write the file
output_folder = "/Users/maximebouthillier/gitmax/code/dr_letourneau/ICH_SEGMENTER_V2/testingmaxime"

# Specify the absolute path of the script you want to execute
script_file = "/Users/maximebouthillier/gitmax/code/testing/slicer_exploration_basic/src/script_file_to_execute.py"  #ex print 1212

################# CONFIG FILE END ##########################

import os
import subprocess

def write_results_from_script() :

    # Ensure that the output folder exists, create it if it doesn't
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Specify the output file name and path within the output folder
    output_file = os.path.join(output_folder, "output_file.txt")

    # Make connection between output folder and the script (comment to revise)
    file_to_execute = os.path.join(output_folder, script_file)
    command = ["python3", file_to_execute]

    # Open the file in write mode and write some content
    with open(output_file, "w") as f:
        subprocess.run(command, stdout=f)
        # f.write("Hello, world!\n")

    print("File has been written to:", output_file)

write_results_from_script()