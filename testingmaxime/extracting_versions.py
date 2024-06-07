liste = ['sub-007009_acq-sag_T2w_PHE_v01.nii.gz', 'sub-007009_acq-sag_T2w_seg-L2-manual_v01.nii.gz', 'sub-007009_acq-sag_T2w_seg-L-manual_v01.nii.gz', 'sub-007004_acq-STIRsag_run-01_T2w_PHE_v01.nii.gz', 'sub-007004_acq-STIRsag_run-01_T2w_seg-L2-manual_v01.nii.gz', 'sub-007009_acq-STIRsag_run-01_T2w_PHE_v01.nii.gz', 'sub-007004_acq-STIRsag_run-01_T2w_seg-L-manual_v01.nii.gz', 'sub-007009_acq-STIRsag_run-01_T2w_seg-L-manual_v01.nii.gz', 'sub-007009_acq-STIRsag_run-01_T2w_seg-L2-manual_v01.nii.gz']
for element in liste:
    print(element)


# all_files = ['/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L2-manual_v04.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L-manual_v02.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_PHE_v04.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_PHE_v02.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L-manual_v04.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L2-manual_v02.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L-manual_v01.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L-manual_v03.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_PHE_v01.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L2-manual_v01.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L2-manual_v03.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_PHE_v03.nii.gz']
# all_files_label_sorted = []
# list_of_labels = ['seg-L-manual', 'seg-L2-manual', 'PHE']
# max_version = 4
#
# # for label in list_of_labels:
# #     for version in range(max_version):
# #         for element in all_files:
# #             if (label in element) and (f"_v{(version + 1):02d}" in element):
# #                 # print(element)
# #                 all_files_label_sorted.append(element)
# #
# # print(all_files_label_sorted)
# #
# # for element in all_files_label_sorted:
# #     print(element)
# #
# # print(len(all_files_label_sorted))
#
# # for version in range(max_version):
# #     for label in list_of_labels:
# #         for element in all_files:
# #             if (label in element) and (f"_v{(version + 1):02d}" in element):
# #                 # print(element)
# #                 all_files_label_sorted.append(element)
#
# # for element in all_files:
# #     for label in list_of_labels:
# #         for version in range(max_version):
# #             if (label in element) and (f"_v{(version+1):02d}" in element) :
# #                 print(element)
# #                 all_files_label_sorted.append(element)
# versions_dict ={'_v01': ['/Users/maximebouthillier/gitmax/data_confid'
#                         '/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L-manual_v01.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L2-manual_v01.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_PHE_v01.nii.gz'], '_v02': ['/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L-manual_v02.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L2-manual_v02.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_PHE_v02.nii.gz'], '_v03': ['/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L-manual_v03.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L2-manual_v03.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_PHE_v03.nii.gz'], '_v04': ['/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L-manual_v04.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_seg-L2-manual_v04.nii.gz', '/Users/maximebouthillier/gitmax/data_confid/test_sct_sci_data/output/versions/sub-ott002_acq-sag_T2w_PHE_v04.nii.gz']}
#
#
# for element in versions_dict:
#     print(len(versions_dict[element]), versions_dict[element])
