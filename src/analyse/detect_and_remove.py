from ultralytics import YOLO
import numpy as np
from segment_anything import SamPredictor, sam_model_registry
from analyse.process_icon import search
import cv2
import os
from analyse.object import Device, DeviceType

ckpt_p = os.path.join(os.environ["PROJECT_DIR"], "models/sam_vit_h_4b8939.pth")
sam = sam_model_registry["vit_h"](checkpoint=ckpt_p)
sam.to(device="cuda")

yolo = YOLO(os.path.join(os.environ["PROJECT_DIR"], 'models/last.pt'))
predictor = SamPredictor(sam)


def predict_masks_with_sam(
        point_coords: "list[list[int]]",
):
    point_coords = np.array(point_coords)
    masks, _, _ = predictor.predict(
        box = point_coords
    )
    return masks

def detect_object(img_path, row, col, radius=3):
    li = [img_path]
    # Run inference on 'bus.jpg' with arguments
    result = yolo.predict(li, imgsz=640, conf=0.53, save=False)
    polys=[]
    blocks = []
    result = result[0].cpu()
    if len(result.boxes.conf) == 0: return [], [], []
    min_conf = min(result.boxes.conf)
    mean_conf = sum(result.boxes.conf) / len(result.boxes.conf)
    if (mean_conf - min_conf > 0.12): min_conf = min_conf + 0.02
    confs = []

    for bbox, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
        if conf < min_conf and cls == 0: continue
        x0 = max(int(bbox[0]) - radius, 0)
        x1 = min(int(bbox[2]) + radius, col-1)
        y0 = max(int(bbox[1]) - radius, 0)
        y1 = min(int(bbox[3]) + radius, row+1)
        if (cls == 0): 
            polys.append([x0,y0,x1,y1])
            confs.append(conf)
        else: blocks.append([int(bbox[0]),int(bbox[1]), int(bbox[2]), int(bbox[3])])
    
    return polys, blocks, confs

from collections import Counter

def most_common_color(image, mask):
    masked_image = np.where(mask[..., None] == 0, image, 0)
    pixels = [tuple(pixel) for pixel in masked_image.reshape(-1, 3) if np.any(pixel != 0)]
    tolerance = 10
    def color_key(rgb):
        return tuple((channel // tolerance) * tolerance for channel in rgb)

    grouped_colors = [color_key(rgb) for rgb in pixels]
    most_common = Counter(grouped_colors).most_common(1)

    if most_common:
        return most_common[0][0]
    else:
        return None
    
def detect_and_remove(img_path, output_dir, debug, bg_org=(255,255,255))->[Device]:
    img = cv2.imread(img_path)
    row, col, _ = img.shape
    polys, blocks,  confs = detect_object(img_path, row, col)
    devices = []
    links = []
    real_poly = []
    
    img = np.array(img)
    predictor.set_image(img)
    sizes = []
    for poly in polys:
        if len(poly) == 4: size = (poly[2] - poly[0]) * (poly[3] - poly[1])
        else: size = (poly[1][0] - poly[0][0]) * (poly[1][1] - poly[0][1])
        sizes.append(size)
    
    sizes = sorted(sizes)
    if len(sizes) > 0:
        medium = sizes[len(sizes) // 2]
        mean = sum(sizes) // len(sizes)
        if len(sizes) == 1: benchmark_size = medium
        else:  benchmark_size = medium * 0.6 + mean * 0.2 + sizes[-2] * 0.2

        for idx, poly in enumerate(polys):
            if len(poly) == 4: size = (poly[2] - poly[0]) * (poly[3] - poly[1])
            else: size = (poly[1][0] - poly[0][0]) * (poly[1][1] - poly[0][1])
            real_masks = np.zeros((row, col), dtype=np.uint8)
            masks = predict_masks_with_sam(poly)
            for mask in masks[:-1]:
                real_masks |= mask            
            real_masks *= 255
            real_masks = cv2.dilate(real_masks, (10, 10), iterations=3)
            device_type = search(img, real_masks, idx)

            if (device_type == DeviceType.LINK):
                bg_color = most_common_color(img[poly[0]:poly[2], poly[1]:poly[3], :], real_masks[poly[0]:poly[2], poly[1]:poly[3]])
                if (bg_color is None): bg_color = bg_org
                img[real_masks>0] = bg_color
                non_zero_indices = np.argwhere(real_masks != 0)
                y1, x1 = non_zero_indices[np.argmin(non_zero_indices[:, 0])]
                y2, x2 = non_zero_indices[np.argmax(non_zero_indices[:, 0])]
                y3, x3 = non_zero_indices[np.argmin(non_zero_indices[:, 1])]
                y4, x4 = non_zero_indices[np.argmax(non_zero_indices[:, 1])]
                if (y2 - y1 > x4 - x3):
                    links.append(((x1, y1), (x2, y2)))
                else:
                    links.append(((x3, y3), (x4, y4)))
                
                if (debug): cv2.imwrite(os.path.join(output_dir, str(idx) + "_" + os.path.basename(img_path)), img)         
                continue
            
            if ((size < 0.1 * benchmark_size or size > 3 * benchmark_size) and confs[idx] < 0.85):
                continue
            device = Device(poly, len(devices), device_type)
            devices.append(device)
            bg_color = most_common_color(img[poly[0]:poly[2], poly[1]:poly[3], :], real_masks[poly[0]:poly[2], poly[1]:poly[3]])
            if (bg_color is None): bg_color = bg_org
            img[real_masks>0] = bg_color
            if (debug): cv2.imwrite(os.path.join(output_dir, str(idx) + "_" + os.path.basename(img_path)), img)
            real_poly.append(poly)
    
    for idx, poly in enumerate(blocks):
        device = Device(poly, len(devices), DeviceType.BLOCK)
        devices.append(device)

    cv2.imwrite(os.path.join(output_dir, os.path.basename(img_path)), img)
    return devices, links, real_poly, blocks

def convert_bbox_format(bbox):
    '''
    Convert bbox from xywh format to xyxy
    '''
    x,y,w,h = bbox
    x1 = x
    x2 = x + w
    y1 = y
    y2 = y + h
    return [x1,y1,x2,y2]