from functools import cmp_to_key
import math
from analyse.union_find import UnionFind
from analyse.object import Line
from analyse.constant import bus_thrs, op_thrs, int_thrs
import logging

ADJUST_RATIO = 1
def get_slope_intercept(line):
    '''
    Calculate the slope and intercept of a line.
    '''
    if (len(line) == 4): x1, y1, x2, y2 = line
    elif (len(line) == 2): (x1,y1), (x2,y2) = line

    # Calculate the slope of the line
    slope = (y2 - y1) / (x2 - x1) if abs(x2 - x1) > ADJUST_RATIO else float('inf')

    # Calculate the intercept of the line
    intercept = y1 - slope * x1 if slope != float('inf') else x2

    return slope, intercept

def same_float(a, b, threshold=None):
    if (threshold is None): return a == b == float("inf") or abs(a - b) <= (0.2 if abs(a) <= 10 and abs(b) <= 10 else 0.02 * min(abs(a), abs(b)) )
    else: return a == b == float("inf") or abs(a-b) <= threshold * ADJUST_RATIO

def lefter_point(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    if (not same_float(x1, x2, 1)):
        return 1 if x1<x2 else 2
    else:
        return 1 if y1<y2 else 2
    
def is_overlap(line1, line2):
    slope1, intercept1 = get_slope_intercept(line1)
    slope2, intercept2 = get_slope_intercept(line2)

    if (len(line1) == 4): x1, y1, x2, y2 = line1
    elif (len(line1) == 2): (x1, y1), (x2, y2) = line1

    if (len(line2) == 4): x3, y3, x4, y4 = line2
    elif (len(line2) == 2): (x3, y3), (x4, y4) = line2

    if (min(x1, x2) - op_thrs * ADJUST_RATIO > max(x3, x4) or max(x1, x2) + op_thrs * ADJUST_RATIO < min(x3, x4)): return False
    if (min(y1, y2) - op_thrs * ADJUST_RATIO > max(y3, y4) or min(y3, y4) - op_thrs * ADJUST_RATIO > max(y1, y2)): return False

    # Check if the lines overlap within a threshold
    if same_float(slope1, slope2) and same_float(intercept1, intercept2):
        return True
    
    if (slope1 == float('inf')):
        if (same_float(x1, x3, op_thrs) and same_float(x3, x4, op_thrs)): return True
    else:
        yy3 = x3 * slope1 + intercept1
        yy4 = x4 * slope1 + intercept1
        if (same_float(yy3, y3, op_thrs) and same_float(yy4, y4, op_thrs)): return True
    
    if (slope2 == float('inf')):
        if (same_float(x1, x3, op_thrs) and same_float(x1, x2, op_thrs)): return True
    else:
        yy1 = x1 * slope2 + intercept2
        yy2 = x2 * slope2 + intercept2
        if (same_float(yy1, y1, op_thrs) and same_float(yy2, y2, op_thrs)): return True
    
    return False

def combine1(lines, polys = []):
    '''
    Check all pair of lines and combine the overlapped ones
    '''    
    for i in range(len(lines)):
        if (lines[i] is None): continue
        found = True
        while found:
            found = False
            for j in range(len(lines)):
                if (lines[j] is None): continue
                if is_overlap(lines[i], lines[j]) and i!=j:
                    found = True
                    if (len(lines[i]) == 4):
                        if lefter_point((lines[i][0], lines[i][1]), (lines[j][0], lines[j][1])) == 1: st = i
                        else: st = j
                        if lefter_point((lines[i][2], lines[i][3]), (lines[j][2], lines[j][3])) == 2: en = i
                        else: en = j
                        lines[i] = [lines[st][0], lines[st][1], lines[en][2], lines[en][3]]
                    else:
                        if lefter_point(lines[i][0], lines[j][0]) == 1: st = i
                        else: st = j
                        if lefter_point(lines[i][1], lines[j][1]) == 2: en = i
                        else: en = j
                        lines[i] = [lines[st][0], lines[en][1]]
                    lines[j] = None
    
    if (len(polys) > 0):
        for i in range(len(lines)):
            l = lines[i]
            if l is None: continue
            if any(poly[0]<l[0]<poly[2] and poly[0]<l[2]<poly[2] and poly[1]<l[1]<poly[3] and poly[1]<l[3]<poly[3] for poly in polys): lines[i] = None
    
    lines = [line for line in lines if line is not None]
    if len(lines) == 0: return lines
    # Flatten the sets in point_of_line and store the points in a list
    if len(lines[0]) == 4:
        points = [[line[i*2], line[i*2+1]] for line in lines for i in range(2)]
    else:
        points = [line[i] for line in lines for i in range(2)]
    
    # Aggregate the points into groups based on their proximity
    aggregated_points = aggregate_points(points)

    for i in range(len(lines)):
        if len(lines[i]) == 2:
            lines[i] = [aggregated_points[i*2], aggregated_points[i*2+1]]
        else:
            lines[i][0], lines[i][1] = aggregated_points[i*2]
            lines[i][2], lines[i][3] = aggregated_points[i*2+1]
        for j in range(i):
            if aggregated_points[i*2] == aggregated_points[j*2] and aggregated_points[i*2+1] == aggregated_points[j*2+1] :
                lines[i] = None
                break
    
    lines = [line for line in lines if line is not None]
    return lines
    

def intersect(line1, line2, sp = False)->(int,int):
    if len(line1) == 4: x1, y1, x2, y2 = line1
    else: (x1, y1), (x2, y2) = line1
    if len(line2) == 4: x3, y3, x4, y4 = line2
    else: (x3, y3), (x4, y4) = line2

    s1, e1 = (x1,y1), (x2,y2)
    s2, e2 = (x3,y3), (x4,y4)
    if (s1 == s2 or s1 == e2):
        return s1 if sp else (-1,-1)
    
    if (e1 == s2 or e1 == e2):
        return e1 if sp else (-1,-1)
    
    # Calculate the slopes of the lines
    slope1, _ = get_slope_intercept(line1)
    slope2, _ = get_slope_intercept(line2)

    # Check if the lines are parallel
    if slope1 == slope2:
        return (-1,-1)

    # Calculate the intersection point
    if slope1 == float('inf'):
        intersection_x = x1
        intersection_y = slope2 * (intersection_x - x3) + y3
    elif slope2 == float('inf'):
        intersection_x = x3
        intersection_y = slope1 * (intersection_x - x1) + y1
    else:
        intersection_x = (slope1 * x1 - slope2 * x3 + y3 - y1) / (slope1 - slope2)
        intersection_y = y1 + slope1 * (intersection_x - x1)

    # Check if the intersection point is within the line segments
    if (min(x1, x2) - int_thrs * ADJUST_RATIO < intersection_x < max(x1, x2) + int_thrs * ADJUST_RATIO and
            min(y1, y2) - int_thrs * ADJUST_RATIO < intersection_y < max(y1, y2) + int_thrs * ADJUST_RATIO and
            min(x3, x4) - int_thrs * ADJUST_RATIO < intersection_x < max(x3, x4) + int_thrs * ADJUST_RATIO and
            min(y3, y4) - int_thrs * ADJUST_RATIO < intersection_y < max(y3, y4) + int_thrs * ADJUST_RATIO):
        return [intersection_x, intersection_y]

    return (-1,-1)

def cut(line1, line2):
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2

    intersection_x, intersection_y = intersect(line1, line2)
    if (intersection_x < 0 or intersection_y < 0): return line1, line2

    # Cut line1 into two halves at the intersection point
    line1_half1 = (x1, y1, intersection_x, intersection_y)
    line1_half2 = (intersection_x, intersection_y, x2, y2)

    # Cut line2 into two halves at the intersection point
    line2_half1 = (x3, y3, intersection_x, intersection_y)
    line2_half2 = (intersection_x, intersection_y, x4, y4)

    return line1_half1, line1_half2, line2_half1, line2_half2

def aggregate_points(points, MAX_DIST=4.0):
    aggr = [-1] * len(points)  # Initialize with -1, indicating no group assigned

    def find_representative_point(group):
        # Calculate the centroid of the group
        x_sum = sum(points[point][0] for point in group)
        y_sum = sum(points[point][1] for point in group)
        return ((x_sum / len(group)), (y_sum / len(group)))

    for i in range(len(points)):
        if aggr[i] == -1:  
            group = [i]
            # Find other points within MAX_DIST
            for j in range(i + 1, len(points)):
                if aggr[j] == -1 and math.dist(points[i], points[j]) < MAX_DIST * ADJUST_RATIO:
                    group.append(j)
            representative_point = find_representative_point(group)        
            # Update aggr for all points in the group
            for point_index in group:
                aggr[point_index] = representative_point

    return aggr

def cut_lines(lines):
    '''
    Cut the lines that are intersected until there is no intersection.
    '''
    point_of_line = [[] for _ in range(len(lines))]  # Initialize point_of_line as a list of empty sets

    # Add the start and end points of each line to the corresponding set in point_of_line
    for i in range(len(lines)):
        point_of_line[i].append(lines[i][:2])
        point_of_line[i].append(lines[i][2:])

    # Find the intersection points between lines and add them to the corresponding sets in point_of_line
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            intersection = intersect(lines[i], lines[j])
            if intersection != (-1, -1):
                point_of_line[i].append(intersection)
                point_of_line[j].append(intersection)
    
    for i in range(len(lines)):
        point_of_line[i] = sorted(point_of_line[i], key=cmp_to_key(lambda x,y: -1 if lefter_point(x,y)==1 else 1))

    # Flatten the sets in point_of_line and store the points in a list
    points = [point for line_points in point_of_line for point in line_points]
    
    # Aggregate the points into groups based on their proximity
    aggregated_points = aggregate_points(points)

    cut_lines = []
    sum = 0

    for i in range(len(lines)):
        ptl = len(point_of_line[i])
        for j in range(sum, sum+ptl-1):
            if aggregated_points[j] != aggregated_points[j+1]:
                cut_lines.append((aggregated_points[j], aggregated_points[j+1]))
        sum += ptl
        
    return cut_lines

def get_common_endpoint(line1, line2)->(int,int):
    '''
    Get the common endpoint of two lines.
    '''
    if (len(line1) == 4): x1, y1, x2, y2 = line1
    elif (len(line1) == 2): (x1,y1), (x2,y2) = line1

    if (len(line2) == 4): x3, y3, x4, y4 = line2
    elif (len(line2) == 2): (x3,y3), (x4,y4) = line2

    if (x1,y1) == (x3,y3) or (x1,y1) == (x4,y4): return (x1,y1)
    if (x2,y2) == (x3,y3) or (x2,y2) == (x4,y4): return (x2,y2)

    return (-1,-1)

def slope_vertical(slope1, slope2) -> bool:
    if (same_float(slope1, 0)): return slope2 == float('inf')
    if (slope1 == float('inf')): return same_float(slope2, 0)
    return same_float(slope1 * slope2, -1)

def build_line(group):
    degrees = {}
    
    for i, line in enumerate(group):
        (x1, y1), (x2, y2) = line
        x1, y1, x2 , y2 = int(x1), int(y1), int(x2), int(y2)
        line = (x1, y1), (x2, y2)
        if (x1, y1) in degrees: degrees[(x1, y1)].append(i)
        else: degrees[(x1, y1)] = [i]
        if (x2, y2) in degrees: degrees[(x2, y2)].append(i)
        else: degrees[(x2, y2)] = [i]
    
    used = [False] * len(group)
    st = en = None
    anchor = []
    for i in degrees.items():
        if len(i[1]) == 1:
            if st is None: st = i[0]
            elif en is None: en = i[0]
            else: return None #something bad happens
        else:
            anchor.append(i[0])
    if st is None or en is None:
        return None
    
    if lefter_point(st, en) == 2:
        st, en = en, st
    
    pt = st
    while(True):
        for i in degrees[pt]:
            if not used[i]:
                (x1, y1), (x2, y2) = group[i]
                x1, y1 = int(x1), int(y1)
                x2, y2 = int(x2), int(y2)
                pt = (x1,y1) if (x2,y2) == pt else (x2, y2)
                used[i] = True
                anchor.append(pt)
                break
        if pt == en: break
    
    anchor = anchor[:-1]
    return Line([st, en], anchor)

def combine2(segments, links):
    n = len(segments)
    uf = UnionFind(n)

    # Step 0: Calculate degrees
    degrees = {}
    slopes = []
    intercepts = []
    
    for i in range(n):
        st, en = segments[i]
        if st in degrees: degrees[st].append(i)
        else: degrees[st] = [i]
        if en in degrees: degrees[en].append(i)
        else: degrees[en] = [i]
        slope, intercept = get_slope_intercept(segments[i])
        slopes.append(slope)
        intercepts.append(intercept)
    
    # Step 1: Merge segments with common endpoints and similar slopes
    for i in range(n):
        for j in range(i + 1, n):
            common_endpoints = get_common_endpoint(segments[i], segments[j])
            if common_endpoints != (-1, -1):
                if (same_float(slopes[i], slopes[j]) or len(degrees[common_endpoints]) == 2):
                    uf.union(i, j)

    # Step 2: Upgrade groups with similar slopes and more than three segments to bus
    av = [True] * n
    bus = [0] * n
    buses = []
    for i in range(n):
        slope1 = slopes[i]
        if (slope1 != float('inf') and abs(slope1) > 0.1): continue
        if (not av[i]): continue
        possible_bus = []
        bus_connected = []
        vertical = 0
        pa = uf.find(i)
        
        points = set()
        (x1, y1), (x2, y2) = segments[i]
        points.add((x1, y1))
        for k in degrees[(x1, y1)]:
            if slope_vertical(slope1, slopes[k]):
                vertical += 1
                bus_connected.append((k, (x1, y1)))
        points.add((x2, y2))
        for k in degrees[(x2, y2)]:
            if slope_vertical(slope1, slopes[k]):
                vertical += 1
                bus_connected.append((k, (x2, y2)))
        
        for j in range(i + 1, n):
            slope2, _ = get_slope_intercept(segments[j])
            if pa == uf.find(j):
                av[j] = False
                if same_float(slope1, slope2):
                    possible_bus.append(j)
                    (x1, y1), (x2, y2) = segments[j]
                    if (x1, y1) not in points:
                        points.add((x1, y1))
                        for k in degrees[(x1, y1)]:
                            if slope_vertical(slope1, slopes[k]):
                                vertical += 1
                                bus_connected.append((uf.find(k), (x1, y1)))
                    
                    if (x2, y2) not in points:
                        points.add((x2, y2))
                        for k in degrees[(x2, y2)]:
                            if slope_vertical(slope1, slopes[k]):
                                vertical += 1
                                bus_connected.append((uf.find(k), (x2, y2)))
        
        if len(possible_bus) > 4 and vertical > 4:
            buses.append((pa, bus_connected))
            for j, _ in bus_connected:
                bus[j] = pa + 1
            bus[uf.find(i)] = -1
    
    # Step 3: Copy segments with degree 3 and similar slopes to form a new bus
    for (pt, value) in degrees.items():
        if len(value) == 3:
            u0, u1, u2 = uf.find(value[0]), uf.find(value[1]), uf.find(value[2])
            if (bus[u0]<0 or bus[u1]<0 or bus[u2]<0): continue
            if (u0 == u1 == u2): continue
            if same_float(slopes[value[0]], slopes[value[1]]):
                if slope_vertical(slopes[value[0]], slopes[value[2]]):
                    bus[u2] = -1
                    bus[u1] = u2 + 1
                    buses.append((u2, [(u0, pt)]))
            elif same_float(slopes[value[0]], slopes[value[2]]):
                if slope_vertical(slopes[value[0]], slopes[value[1]]):
                    bus[u1] = -1
                    bus[u0] = u1 + 1
                    buses.append((u1, [(u0, pt)]))
            elif same_float(slopes[value[1]], slopes[value[2]]):
                if slope_vertical(slopes[value[0]], slopes[value[1]]):
                    bus[u0] = -1
                    bus[u1] = u0 + 1
                    buses.append((u0, [(u1, pt)]))

    n = len(segments)
    groups = [[] for _ in range(n)]

    # Step 4: If line is not a bus, merge the segments to build lines
    for i in range(n):
        groups[uf.find(i)].append(segments[i])
      
    for i in range(n):
        if (len(groups[i]) > 0):
            groups[i] = combine1(groups[i])
    
    lines = []
    built = [False] * n
    for i, ks in buses:
        if (len(groups[i]) == 0):
            logging.warning("The bus group is empty, skipping...") 
            continue
        line_b = build_line(groups[i])
        if (line_b is None):
            logging.warning("Bus Line is not built successfully, skipping...") 
            continue
        built[i] = True
        line_b.line_uuid = len(lines)
        line_b.link_bus = line_b.line_uuid
        bus[i] = line_b.line_uuid
        lines.append(line_b)
        for j, ip in ks:
            nj = uf.find(j)
            if (built[nj]):
                logging.warning("Line attached to a bus is not built successfully, skipping...")  
                continue
            line = build_line(groups[nj])
            built[nj] = True
            if (line is None): continue
            line.line_uuid = len(lines)
            line.link_bus = bus[i]
            if (math.dist(ip, line.line[0]) < bus_thrs): line.st_to_bus = True
            if (math.dist(ip, line.line[1]) < bus_thrs): line.en_to_bus = True
            if (math.dist(ip, line_b.line[0]) < bus_thrs): lines[bus[i]].st_to_bus = True
            if (math.dist(ip, line_b.line[1]) < bus_thrs): lines[bus[i]].en_to_bus = True
            line.bus_pt = ip
            lines.append(line)
    
    for i in range(n):
        pa = uf.find(i)
        if not built[pa]:
            line = build_line(groups[pa])
            if (line is None):
                logging.warning("Line is not built successfully, skipping...")  
                continue
            built[pa] = True
            line.line_uuid = len(lines)
            lines.append(line)
    
    for link in links:
        line = Line((link[0], link[1]), [])
        line.line_uuid = len(lines)
        lines.append(line)

    return lines

def remove_dense(lines, col, row):
    '''
    Remove the dense lines in one block
    '''
    block_col = min(col // 5, 50)
    block_row = min(row // 5, 50)
    MAX_LINES_IN_BLOCK = 5
    valid_lines = [True] * len(lines)
    for i in range(0, col, block_col):
        for j in range(0, row, block_row):
            block_lines = []
            points_in = 0
            for idx, line in enumerate(lines):
                if line is None: continue
                if (len(line) == 4): x1, y1, x2, y2 = line
                elif (len(line) == 2): (x1, y1), (x2, y2) = line
                if (i <= x1 <= i + block_col and j <= y1 <= j + block_row and i <= x2 <= i + block_col and j <= y2 <= j + block_row):
                    block_lines.append(idx)
                    points_in += 2
                elif (intersect(line, (i, j, i + block_col, j), True) != (-1, -1) or 
                      intersect(line, (i, j + block_row, i + block_col, j + block_row), True) != (-1, -1) or 
                      intersect(line, (i, j, i, j + block_row), True) != (-1, -1) or 
                      intersect(line, (i + block_col, j, i + block_col, j + block_row), True) != (-1, -1)):
                    block_lines.append(idx)
                    points_in += 1
            if (len(block_lines) > MAX_LINES_IN_BLOCK or points_in > 1.5 * MAX_LINES_IN_BLOCK):
                for idx in block_lines:
                    valid_lines[idx] = False

    valid_line = [lines[i] for i in range(len(lines)) if valid_lines[i]]
    return valid_line

def process_line(lines, polys, links, col, row):
    global ADJUST_RATIO
    ADJUST_RATIO = max(1.0, (row**2 + col**2) ** 0.5 / 800)
    lines = combine1(lines, polys)
    lines = remove_dense(lines, col, row)
    lines = cut_lines(lines)
    lines = combine2(lines, links)
    return lines
