import os
import cv2 as cv
import numpy as np
from skimage import morphology
from analyse.process_line import process_line, lefter_point
# from process_line import process_line, lefter_point

def LineMid(binary, erod):
    bi = binary.copy()
    bi[bi <= 180] = 1
    bi[bi >= 180] = 0
    if (erod): bi = cv.erode(bi, kernel=(3,3), iterations=2)
    skeleton0 = morphology.skeletonize(bi, method="lee")  # 细化提取骨架
    skeleton = skeleton0.astype(np.uint8) * 255
    return skeleton

def getPoints(thinSrc, raudis=4, thresholdMax=6):
    height, width = thinSrc.shape[0], thinSrc.shape[1]
    tmp = thinSrc.copy()
    points = []
    for i in range(height):
        for j in range(width):
            if (tmp[i][j]) == 0:
                continue
            count = 0
            for k in range(i - raudis, i + raudis + 1):
                for l in range(j - raudis, j + raudis + 1):
                    if k < 0 or l < 0 or k > height - 1 or l > width - 1:
                        continue
                    elif tmp[k][l] == 255:
                        count += 1
            if count > thresholdMax:
                point = (j, i)
                points.append(point)
    return points

def on_border(l, poly):
    if abs(l[0]-l[2]) < 5 and poly[1] - 10 < l[1] < poly[3] + 10 and poly[1] - 10 < l[3] < poly[3] + 10:
        if abs(l[0] - poly[0]) < 10 or abs(l[0]-poly[2]) < 10: return True
    if abs(l[1]-l[3]) < 5 and poly[0] - 10 < l[0] < poly[2] + 10 and poly[0] - 10 < l[2] < poly[2] + 10:
        if abs(l[1] - poly[1]) < 10 or abs(l[1]-poly[3]) < 10: return True
    return False

def get_lines(img_path, output_dir, links=[], polys=[], blocks=[], debug=False, erode=True):
    src = cv.imread(img_path)
    col, row, _ = src.shape
    binary = src.copy()
    binary = cv.cvtColor(binary, cv.COLOR_BGR2GRAY)  # Convert src to grayscale
    if (debug): cv.imwrite(os.path.join(output_dir, "dst0.png"), binary)
    dst = LineMid(binary, erod=erode)

    if (debug): cv.imwrite(os.path.join(output_dir, "dst1.png"), dst)
    
    dst = cv.dilate(dst, (3,3), iterations=1)
    linesP = cv.HoughLinesP(dst, 1, np.pi / 180, 7, minLineLength=10, maxLineGap=15)
    lines = []
    blocks.append([0, 0, row, col])
    if linesP is not None:
        for i in range(0, len(linesP)):
            l = linesP[i][0]
            if len(blocks)>0 and any( on_border(l, block) for block in blocks): continue
            if (lefter_point((l[0], l[1]), (l[2], l[3])) == 1): lines.append([l[0], l[1], l[2], l[3]])
            else: lines.append([l[2], l[3], l[0], l[1]])
    
    blocks.pop()
    if (debug):
        for l in lines:
            cv.circle(dst, (l[0], l[1]), 3, 255, cv.FILLED)
            cv.circle(dst, (l[2], l[3]), 3, 255, cv.FILLED)
            cv.line(dst, (l[0], l[1]), (l[2], l[3]), 255, 3, cv.LINE_AA)
        cv.imwrite(os.path.join(output_dir, "lines_" + os.path.basename(img_path)), dst)
    
    lines = process_line(lines, polys, links, col, row)

    if (debug):
        dst = LineMid(binary, erod=erode)
        for l in lines:
            cv.circle(dst, l.line[0], 3, 255, cv.FILLED)
            cv.circle(dst, l.line[1], 3, 255, cv.FILLED)
            cv.line(dst, l.line[0], l.line[1], 255, 2, cv.LINE_AA)
 
        cv.imwrite(os.path.join(output_dir, "prlines_" + os.path.basename(img_path)), dst)
    
    return lines
    