from paddleocr import PaddleOCR
import os
import numpy as np
from analyse.draw_mask import draw_masks
from analyse.remove_mask import lama_operator
from analyse.process_ocr import union_text_boxes
import cv2
import shutil
ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False) 

def ocr_and_remove(img_path, output_dir):
    result = ocr.ocr(img_path)
    # result directory
    polys = []
    res = []
    text = []
    for box, (tr, ps) in result[0]:
        if (ps < 0.5): continue
        poly = list(np.array(box).astype(np.int32).reshape((-1)))
        polys.append(poly)
        res.append((poly[0], poly[1], poly[2], poly[5]))
        text.append(tr)
    
    mask = draw_masks(polys, img_path)

    if len(polys) == 0:
        shutil.copy(img_path, output_dir)
        return []
    
    inpaint_img:np.ndarray = lama_operator.inpaint_img_with_lama(img_path, mask)
    filename=os.path.basename(img_path)
    cv2.imwrite(os.path.join(output_dir, filename), inpaint_img)
    texts = union_text_boxes(res, text)
    return texts