from analyse.object import TextType, DeviceType, Line
from analyse.process_line import intersect
import math 

def get_basic_type(text_type:TextType)->TextType:
    '''
    Returns the basic type of the text type.
    '''
    t = text_type.value
    while (t >= 10):
        t = t // 10
    return TextType(t)

def left_right(bbox1, bbox2):
    '''
    Returns the index of the lefter bbox.
    Returns 0 if they overlap horizontally.
    '''
    if bbox1[0] > bbox2[2]: return 2
    if bbox1[2] < bbox2[0]: return 1
    return 0

def up_down(bbox1, bbox2):
    '''
    Returns the index of the upper bbox.
    Returns 0 if they overlap vertically.
    '''
    if bbox1[1] > bbox2[3]: return 2
    if bbox1[3] < bbox2[1]: return 1
    return 0


def calculate_distance_box(bbox1, bbox2):
    '''
    Calculate the distance between two boxes. All bbox are in xyxy format.
    '''
    dist = 0
    if left_right(bbox1, bbox2) == 1:
        dist += bbox2[0] - bbox1[2]
    elif left_right(bbox1, bbox2) == 2:
        dist += bbox1[0] - bbox2[2]
    else:
        dist -= 1
    
    if up_down(bbox1, bbox2) == 1:
        dist += bbox2[1] - bbox1[3]
    elif up_down(bbox1, bbox2) == 2:
        dist += bbox1[1] - bbox2[3]
    else:
        dist -= 1
    
    return dist

def calculate_distance_single_line(bbox, line):
    '''
    Calculate the distance between a box and a line. The bbox in xyxy format.
    Line in xyxy format indicating two ends.
    '''
    bbox_points = [(bbox[0], bbox[1]), (bbox[0], bbox[3]), (bbox[2], bbox[1]), (bbox[2], bbox[3])]

    # Calculate the distance from the point on the edge of the bbox to the line
    distance = float('inf')
    # Check the distance from the top edge of the bbox to the line
    if intersect(line, ((bbox[0], bbox[1]), (bbox[2], bbox[1]))) != (-1, -1):
        distance = -1
    
    if intersect(line, ((bbox[0], bbox[3]), (bbox[2], bbox[3]))) != (-1, -1):
        distance = -1
    
    if intersect(line, ((bbox[0], bbox[1]), (bbox[0], bbox[3]))) != (-1, -1):
        distance = -1
    
    if intersect(line, ((bbox[2], bbox[1]), (bbox[2], bbox[3]))) != (-1, -1):
        distance = -1
    
    distances = [math.dist(pa, pb) for pa in bbox_points for pb in line]
    distance = min(distance, min(distances))
    return distance

def calculate_distance_line(bbox, line:Line):
    last_point = line.line[0]
    min_distance = float("inf")
    for i in line.anchor:
        min_distance = min(min_distance, calculate_distance_single_line(bbox, (last_point, i)))
        last_point = i
    min_distance = min(min_distance, calculate_distance_single_line(bbox, (last_point, line.line[1])))
    return min_distance

def calculate_distance_point(bbox, point):
    '''
    The distance should base on the distance between the point and the closest point
    on the bbox edge to it. The bbox in xyxy format.
    '''
    x, y = point
    if len(bbox) == 4: x1, y1, x2, y2 = bbox
    else: (x1, y1), (x2, y2) = bbox
    bbox_points = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
    if x1 <= x <= x2 and y1 <= y <= y2:
        return -abs((x - (x1 + x2) / 2))-abs((y - (y1 + y2) / 2))
    distance = float('inf')
    if x1 <= x <= x2:
        distance = min(distance, abs(y - y1), abs(y - y2))
    if y1 <= y <= y2:
        distance = min(distance, abs(x - x1), abs(x - x2))
    distance = min(distance, 1.1 *min([math.dist((x, y), point) for point in bbox_points]))
    return distance

def text_device_match(text:TextType, device:DeviceType):
    # TODO: explicitly define the match rules. Must be a direct relative, not a collateral relative
    ts = str(text.value)[1:]
    ds = str(device.value)
    return ts.startswith(ds) or ds.startswith(ts)

def text_deep_device(text:TextType, device:DeviceType):
    ts = str(text.value)[1:]
    ds = str(device.value)
    return ts.startswith(ds)

def device_match(d1:DeviceType, d2:DeviceType, strict=True):
    d1s = str(d1.value)
    d2s = str(d2.value)
    if (strict): return d1s.startswith(d2s) or d2s.startswith(d1s)
    else: return d1s.startswith(d2s) or d2s.startswith(d1s) or d1s[:2] == d2s[:2]