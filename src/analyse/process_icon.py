from analyse.search_icon import clip_search_tool
from PIL import Image
import cv2
import numpy as np
from analyse.object import DeviceType
from collections import defaultdict

def crop_by_mask(image, mask):
    if image.shape[:2] != mask.shape:
        raise ValueError("Image and mask dimensions do not match.")
    
    _, binary_mask = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv2.contourArea)

    white_background = np.ones_like(image) * 255
    contour_mask = np.zeros_like(binary_mask)
    cv2.drawContours(contour_mask, [largest_contour], 0, 255, thickness=cv2.FILLED)
    cropped_image = cv2.bitwise_and(image, image, mask=contour_mask)

    inverted_mask = cv2.bitwise_not(contour_mask)
    white_background = cv2.bitwise_and(white_background, white_background, mask=inverted_mask)
    x, y, w, h = cv2.boundingRect(largest_contour)
    cropped_image = cv2.add(cropped_image, white_background)

    cropped_image = cropped_image[y:y+h, x:x+w]
    return cropped_image

    
def search(image, mask, times=0):
    icon_image = image.copy()
    icon_image = crop_by_mask(icon_image, mask)
    icon_image = cv2.cvtColor(icon_image, cv2.COLOR_BGR2RGB)
    icon_image = Image.fromarray(icon_image.astype('uint8'), 'RGB')
    type_list, text_type = clip_search_tool.search_by_image(icon_image)
    scores = defaultdict(int)
    max_type = "FAILED"
    max_time = 0
    for type, score in type_list:
        if type == "OTHER_DEVICE":
            type = "DEVICE"
        
        scores[type] = max(scores[type], score)
        if scores[type] > max_time:
            max_type = type
            max_time = scores[type]

    max_device_sim = 0
    for type, score in text_type:
        if type != "LINK":
            max_device_sim = max(max_device_sim, score)
        if type == "DEVICE":
            continue
        
        scores[type] += score
        if scores[type] > max_time:
            max_type = type
            max_time = scores[type]
    
    if (max_type == "LINK" or max_type == "FAILED"):
        scores["DEVICE"]  += max_device_sim
        if scores["DEVICE"] > max_time:
            max_type = "DEVICE"
        
    return DeviceType[max_type.upper()] if max_type in DeviceType.__members__ else DeviceType.DEVICE
