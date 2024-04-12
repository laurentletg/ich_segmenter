import slicer
import os, re, glob

def update_current_case_paths_by_segmented_volumes(CasesPaths, SegmentationFolder, segm_regex_pattern):
    print('test')
    segmentations = glob.glob(os.path.join(SegmentationFolder, '*.seg.nrrd'))
    segmented_IDs = [re.findall(segm_regex_pattern, os.path.basename(segmentation))[0] for  segmentation in segmentations]
    remaining_cases = [vol for vol in CasesPaths if vol not in segmented_IDs]
    print(f'CasesPaths - volumes to annotate: {len(CasesPaths)}')
    print(f'Segmented volumes: {len(segmented_IDs)}')
    print('Remaining cases: ', len(remaining_cases))
    print('Remaining cases: ', remaining_cases)
    print('Updating current cases paths...')
    return remaining_cases