import os
import yaml


# def save_list_to_yaml(my_list, directory, file_name):
#     # Ensure the directory exists
#     os.makedirs(directory, exist_ok=True)
#
#     # Define the complete file path
#     file_path = os.path.join(directory, file_name)
#
#     # Write the list to the YAML file
#     with open(file_path, 'w') as file:
#         yaml.dump(my_list, file)
#
#
# # Example usage
# my_list = ['apple', 'banana', 'cherry']
# directory = '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output'
# file_name = 'my_list.yaml'
#
# save_list_to_yaml(my_list, directory, file_name)


import os
import yaml


def save_files_seg_to_yaml(file_paths, directory, file_name):
    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)

    # Define the complete file path
    file_path = os.path.join(directory, file_name)

    # Create a dictionary with the 'FILES_SEG' key
    data = {
        'FILES_SEG': file_paths
    }

    # Write the dictionary to the YAML file
    with open(file_path, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)


# Example usage
file_paths = ['/Users/maximebouthillier/sub-ott002_acq-sag_T2w.nii.gz']
directory = '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output'
file_name = 'remainingCases.yaml'

save_files_seg_to_yaml(file_paths, directory, file_name)
