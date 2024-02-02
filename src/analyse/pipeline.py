from analyse.ocr_and_remove import ocr_and_remove
from analyse.detect_and_remove import detect_and_remove
from analyse.line_detect import get_lines
from analyse.process_line import process_line
import os

def process_pipeline(img_path, debug, tmp_dir = None, erode=True):
    '''
    Process the image with the pipeline.
    '''
    if (tmp_dir is None):
        tmp_dir = os.path.join(os.environ["PROJECT_DIR"], "tmp")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
    # ocr_and_remove
    texts = ocr_and_remove(img_path, tmp_dir)
    
    tmp_path = os.path.join(tmp_dir, os.path.basename(img_path))
    # detect_and_remove
    devices, links, polys, blocks = detect_and_remove(tmp_path, tmp_dir, debug)
    
    lines = get_lines(tmp_path, tmp_dir, links, polys, blocks, debug, erode=erode)
    # lines = process_line(lines)
    
    return texts, devices, lines