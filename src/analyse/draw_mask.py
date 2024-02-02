
import cv2
import numpy as np


def draw_mask_by_points(points, image):
    points = np.array(points)
    cv2.fillPoly(image, [points], color=(255, 255, 255))
    return image


def draw_masks(coor, img_path, radius = 3):
    img = cv2.imread(img_path)
    img_mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)

    row, col, _ = img.shape

    for points in coor:
        xy1 = (max(points[0] - radius, 0), max(points[1] - radius, 0))
        xy2 = (min(points[2] + radius, col-1), max(points[3] - radius, 0))
        xy3 = (min(points[4] + radius, col-1), min(points[5] + radius, row-1))
        xy4 = (max(points[6] - radius, 0), min(points[7] + radius, row-1))
        points = np.array([xy1, xy2, xy3, xy4])

        img_mask = draw_mask_by_points(points, img_mask)
    return np.array(img_mask)