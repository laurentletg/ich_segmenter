volume_name = 'sub-ott002_acq-sag_T2w'

cases = [
            'sub-ott002_acq-sag_T2w.nii.gz', 'sub-ott003_acq-sag_T2w.nii.gz',
            'sub-ott004_acq-STIRsag_run-01_T2w.nii.gz', 'sub-ott004_acq-STIRsag_run-02_T2w.nii.gz',
            'sub-ott004_acq-STIRsag_run-03_T2w.nii.gz', 'sub-ott004_acq-sag_run-01_T2w.nii.gz',
            'sub-ott004_acq-sag_run-02_T2w.nii.gz', 'sub-ott004_acq-sag_run-03_T2w.nii.gz',
            'sub-ott004_acq-sag_run-04_T2w.nii.gz', 'sub-ott004_acq-sag_run-05_T2w.nii.gz',
            'sub-ott004_acq-sag_run-06_T2w.nii.gz'
        ]
#
#
extension = '.nii.gz'
#
target_case = volume_name + extension
#
# # def removeCaseCompleted() :
# #     for case in cases:
# #         if case == target_case:
# #             return cases
# #
# #     cases = [item for item in cases if item != target_case]
#
# # removeCaseCompleted()
#
# print(cases)
#
# # Example list and variable
remaining_cases = cases
# variable = 'banana'
#
# Remove all occurrences of the variable from the list
remaining_cases = [item for item in remaining_cases if item != target_case]

print(remaining_cases)  # Output: ['apple', 'cherry']

# import copy
#
# # Original list with nested objects
# original_list = [[1, 2, 3], [4, 5, 6]]
#
# # Shallow copy
# shallow_copied_list = copy.copy(original_list)
#
# # Deep copy
# deep_copied_list = copy.deepcopy(original_list)
#
# # Modify the shallow copy
# shallow_copied_list[0][0] = 'a'
#
# print("Original list after shallow copy modification:", original_list)  # Output: [['a', 2, 3], [4, 5, 6]]
# print("Shallow copied list:", shallow_copied_list)  # Output: [['a', 2, 3], [4, 5, 6]]
#
# # Modify the deep copy
# deep_copied_list[1][0] = 'b'
#
# print("Original list after deep copy modification:", original_list)  # Output: [['a', 2, 3], [4, 5, 6]]
# print("Deep copied list:", deep_copied_list)  # Output: [['a', 2, 3], ['b', 5, 6]]
