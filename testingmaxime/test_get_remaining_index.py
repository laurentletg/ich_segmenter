#get the name of the file in yaml file
#get the inex in case list
#update the current display index in slicer to this index
#load this volume

#get the name of the file in yaml file
import yaml


def extract_first_list_element_from_yaml(yaml_file_path):
    # Load the YAML file
    with open(yaml_file_path, 'r') as file:
        yaml_data = yaml.safe_load(file)

    # Check if 'FILES_SEG' key exists in the YAML data
    if 'FILES_SEG' in yaml_data:
        # Return the first element of the 'FILES_SEG' list
        return yaml_data['FILES_SEG'][0]
    else:
        # Handle the case where 'FILES_SEG' key is not found
        print("'FILES_SEG' key not found in the YAML file.")
        return None


# Example usage
yaml_file_path = '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/remainingCases.yaml'
first_element = extract_first_list_element_from_yaml(yaml_file_path)
print("First element in the 'FILES_SEG' list:", first_element)

# Example usage
yaml_file_path = '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/remainingCases.yaml'
first_element = extract_first_list_element_from_yaml(yaml_file_path)
print("First element in the YAML list:", first_element)

#get the inex in case list

def get_index_by_name(element_list, element_name):
    try:
        index = element_list.index(element_name)
        return index
    except ValueError:
        # Handle the case where the element does not exist in the list
        print(f"The element '{element_name}' does not exist in the list.")
        return None

# Example usage
my_list = self.cases
element_name = 'banana'
index = get_index_by_name(my_list, element_name)
print(f"The index of '{element_name}' in the list is:", index)



#update the current display index in slicer to this index
#load this volume