import os
import csv

Case_number = 'sub-003_acq_sagT2w'
Annotator_name = 'maxime'
Annotator_degree = 'resident'
Revision_step = '1'

def write_csv_in_folder():
    # Sample data, replace these with your actual variables
    Case_number = ['sub-003', 'sub-004', 'sub-005']
    Annotator_name = ['maxime', 'alice', 'bob']
    Annotator_degree = ['resident', 'expert', 'novice']
    Revision_step = [1, 2, 3]

    # Combine data into rows using zip
    data = list(
        zip(Case_number, Annotator_name, Annotator_degree, Revision_step))

    folder_path = '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output'
    file_name = 'metadata.csv'

    # Create the folder if it does not exist
    os.makedirs(folder_path, exist_ok=True)

    # Define the complete file path
    file_path = os.path.join(folder_path, file_name)

    # Check if the file already exists
    file_exists = os.path.isfile(file_path)

    # Write data to the CSV file
    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write header only if the file does not already exist
        if not file_exists:
            writer.writerow(
                ['Case number', 'Annotator Name', 'Annotator Degree',
                 'Revision Step'])

        # Write data rows
        for row in data:
            writer.writerow(row)

# Example usage
write_csv_in_folder()


