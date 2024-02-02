from analyse.object import TextType
from analyse.object import DeviceType
# from analyse.process_line import get_slope_intercept, same_float
from kg.kg_utils import *
from kg.km import best_match_km
from analyse.object import *
import copy

VERY_CLOSE_THRESHOLD_BASE = 5
CLOSE_THRESHOLD_BASE = 40
VERY_CLOSE_THRESHOLD = 5
CLOSE_THRESHOLD = 40
PUNISH_RATIO = 0.1

def attach_line_ends(devices:[Device], lines:[Line], ADJUST_RATIO=1.0, min_size = CLOSE_THRESHOLD_BASE * 2):
    '''
    Given each device's bbox in xyxy format and lines in xyxy format.
    Find the closest device to each end of the lines to decide which
    two devices does the line connect. The distance should base on
    the distance between the point of line end and the closest point
    on the bbox edge to it.
    '''
    ports = []
    new_idx = 0
    pending_ports = []

    for idx, line in enumerate(lines):
        start_point, end_point = line.line[0], line.line[1]
        closest_start_device = -1
        closest_start_distance = float('inf')
        closest_end_device = -1
        closest_end_distance = float('inf')

        for device in devices:
            if device.device_type == DeviceType.BLOCK:
                continue
            device_bbox:(int,int,int,int) = device.bbox
            start_distance = calculate_distance_point(device_bbox, start_point)
            end_distance = calculate_distance_point(device_bbox, end_point)

            if start_distance < closest_start_distance:
                closest_start_device = device.device_uuid
                closest_start_distance = start_distance

            if end_distance < closest_end_distance:
                closest_end_device = device.device_uuid
                closest_end_distance = end_distance
        
        if (closest_start_device != -1): 
            start_bbox = devices[closest_start_device].bbox
            w_start = start_bbox[2] - start_bbox[0]
            h_start = start_bbox[3] - start_bbox[1]
            if (closest_start_distance >= min(min(w_start, h_start) / 2, 10 * ADJUST_RATIO)): #WARNING: Very dangerous option here!
                closest_start_device = -1
        
        if (closest_end_device != -1):
            end_bbox = devices[closest_end_device].bbox
            w_end = end_bbox[2] - end_bbox[0]
            h_end = end_bbox[3] - end_bbox[1]

            if (closest_end_distance >= min(min(w_end, h_end) / 2, 10 * ADJUST_RATIO)): #WARNING: Very dangerous option here!
                closest_end_device = -1
        
        if (closest_start_device == -1):
            for device in devices:
                if device.device_type != DeviceType.BLOCK:
                    continue
                device_bbox:(int,int,int,int) = device.bbox
                start_distance = calculate_distance_point(device_bbox, start_point)

                if start_distance < closest_start_distance:
                    closest_start_device = device.device_uuid
                    closest_start_distance = start_distance

            if (closest_start_device != -1): 
                start_bbox = devices[closest_start_device].bbox
                w_start = start_bbox[2] - start_bbox[0]
                h_start = start_bbox[3] - start_bbox[1]
                if (closest_start_distance >= min(min(w_start, h_start) / 2, 5)): #WARNING: Very dangerous option here!
                    closest_start_device = -1
        
        if (closest_end_device == -1):
            for device in devices:
                if device.device_type != DeviceType.BLOCK:
                    continue
                device_bbox:(int,int,int,int) = device.bbox
                end_distance = calculate_distance_point(device_bbox, end_point)

                if end_distance < closest_end_distance:
                    closest_end_device = device.device_uuid
                    closest_end_distance = end_distance

            if (closest_end_device != -1):
                end_bbox = devices[closest_end_device].bbox
                w_end = end_bbox[2] - end_bbox[0]
                h_end = end_bbox[3] - end_bbox[1]

                if (closest_end_distance >= min(min(w_end, h_end) / 2, 5)): #WARNING: Very dangerous option here!
                    closest_end_device = -1
        
        if (closest_start_device == closest_end_device and closest_end_device != -1):
            lines[idx] = None
            continue
        
        line_len = math.sqrt((start_point[0] - end_point[0]) ** 2 + (start_point[1] - end_point[1]) ** 2)
        if (closest_start_device == closest_end_device == -1 and (line_len < min_size and line.link_bus < 0)):
            lines[idx] = None
            continue
        
        lines[idx].line_uuid = new_idx
        if (lines[idx].link_bus >= 0):
            lines[idx].link_bus = lines[line.link_bus].line_uuid if lines[line.link_bus] is not None else -1
        
        if (not line.st_to_bus):
            port_uuid = len(ports)
            ports.append(Port(start_point, closest_start_device, new_idx, port_uuid))
            if (closest_start_device >= 0): devices[closest_start_device].ports.append(port_uuid)
            else: pending_ports.append(port_uuid)
            line.st_port = port_uuid
        
        if (not line.en_to_bus):
            port_uuid = len(ports)
            ports.append(Port(end_point, closest_end_device, new_idx, port_uuid))
            if (closest_end_device >= 0): devices[closest_end_device].ports.append(port_uuid)
            else: pending_ports.append(port_uuid)
            line.en_port = port_uuid
        
        if (new_idx != idx):
            lines[new_idx] = copy.deepcopy(lines[idx])
        new_idx += 1
    
    # Combine nearby ports and consider if they can be taken as folded line
    lines = lines[:new_idx]
    for pa_idx in pending_ports:
        pa = ports[pa_idx]
        if (pa is None): continue
        for pb_idx in pending_ports:
            if (pa_idx == pb_idx): continue
            pb = ports[pb_idx]
            if (pb is None): continue
            if (math.dist(pa.coor, pb.coor) < 10):
                line_a = lines[pa.line_uuid]
                line_b = lines[pb.line_uuid]
                if line_a.st_port == pa_idx: idx_a = 0
                else: idx_a = 1
                if line_b.st_port == pb_idx: idx_b = 0
                else: idx_b = 1

                if (line_b.link_bus < 0):
                    line_a.line[idx_a] = line_b.line[1 - idx_b]
                    line_a.anchor.append(pa.coor)
                    line_a.anchor.extend(line_b.anchor if idx_b == 0 else reversed(line_b.anchor))
                    if (idx_a == 0): 
                        line_a.st_to_bus = False
                        line_a.st_port = line_b.en_port if idx_b == 0 else line_b.st_port
                        if (line_a.st_port >= 0): ports[line_a.st_port].line_uuid = pa.line_uuid
                    else: 
                        line_a.en_to_bus = False
                        line_a.en_port = line_b.en_port if idx_b == 0 else line_b.st_port
                        if (line_a.en_port >= 0): ports[line_a.en_port].line_uuid = pa.line_uuid
                    lines[pb.line_uuid] = None
                    ports[pa.port_uuid] = None
                    ports[pb.port_uuid] = None
                    break
                elif (line_a.link_bus < 0):
                    line_b.line[idx_b] = line_a.line[1 - idx_a]
                    line_b.anchor.append(pb.coor)
                    line_b.anchor.extend(line_a.anchor if idx_a == 0 else reversed(line_a.anchor))
                    if (idx_b == 0): 
                        line_b.st_to_bus = False
                        line_b.st_port = line_a.en_port if idx_a == 0 else line_a.st_port
                        if (line_b.st_port >= 0): ports[line_b.st_port].line_uuid = pb.line_uuid
                    else: 
                        line_b.en_to_bus = False
                        line_b.en_port = line_a.en_port if idx_a == 0 else line_a.st_port
                        if (line_b.en_port >= 0): ports[line_b.en_port].line_uuid = pb.line_uuid
                    lines[pa.line_uuid] = None
                    ports[pa.port_uuid] = None
                    ports[pb.port_uuid] = None
                    break

    return ports
    

def attach_comment(devices:[Device], lines:[Line], ports:[Port], text):
    closest_device = None
    closest_distance = float('inf')
    text_bbox = text[0]

    for device in devices:
        device_bbox = device.bbox
        distance = calculate_distance_box(text_bbox, device_bbox)
        if distance < closest_distance:
            closest_device = device.device_uuid
            closest_distance = distance

    for line in lines:
        if line is None:
            continue
        distance = calculate_distance_line(text_bbox, line)
        if distance < closest_distance:
            closest_device = line.line_uuid + 1000
            closest_distance = distance
    
    for port in ports:
        if port is None:
            continue
        distance = calculate_distance_point(text_bbox, port.coor)
        if distance < closest_distance:
            closest_device = port.port_uuid + 2000
            closest_distance = distance
    if (closest_device is None): return
    if (closest_device < 1000):
        devices[closest_device].device_comment += text[1] + "\n"
    elif (closest_device < 2000):
        lines[closest_device - 1000].link_comment += text[1] + "\n"
    else:
        ports[closest_device - 2000].port_comment += text[1] + "\n"



def attach_name(devices:[Device], lines:[Line], ports:[Port], text):
    '''
    Return value: a bool, if it is a device type, then a list of distances from the text to each device (line, port if applicable).
    '''
    
    text_bbox = text[0]
    text_type = text[2]
    TYPE_GAIN = 2.0

    if (text_type == TextType.DEVICE_TYPE):
        dist = [-float("inf")] * len(devices)
        device_type = DeviceType[text[1].upper()]
        
        idx = 0
        for device in devices:
            distance = calculate_distance_box(text_bbox, device.bbox)
            if distance < CLOSE_THRESHOLD:
                if distance < VERY_CLOSE_THRESHOLD:
                    dist[idx] = 1 / VERY_CLOSE_THRESHOLD + (VERY_CLOSE_THRESHOLD - distance) / CLOSE_THRESHOLD
                else: dist[idx] = 1 / distance
                if device.device_type == device_type or device.device_type is None:
                    dist[idx] += TYPE_GAIN
            idx += 1

        return True, dist

    dist = [-float("inf")] * ( len(devices) + len (lines) + len(ports) )
    idx = 0
    if (text_device_match(text_type, DeviceType.DEVICE)):
        for device in devices:
            distance = calculate_distance_box(text_bbox, device.bbox)
            if distance < CLOSE_THRESHOLD:
                if distance < VERY_CLOSE_THRESHOLD:
                    dist[idx] = 1 / VERY_CLOSE_THRESHOLD + (VERY_CLOSE_THRESHOLD - distance) / CLOSE_THRESHOLD
                else: dist[idx] = 1 / distance
                if (text_device_match(text_type, device.device_type)):
                    dist[idx] += TYPE_GAIN
            idx += 1
    else:
        idx += len(devices)

    if (text_device_match(text_type, DeviceType.LINK)):
        for line in lines:
            if line is None:
                idx += 1
                continue
            distance = calculate_distance_line(text_bbox, line)
            if distance < CLOSE_THRESHOLD:
                    if distance < VERY_CLOSE_THRESHOLD:
                        dist[idx] = 1 / VERY_CLOSE_THRESHOLD + (VERY_CLOSE_THRESHOLD - distance) / CLOSE_THRESHOLD
                    else: dist[idx] = 1 / distance
                    if (text_device_match(text_type, DeviceType.LINK)):
                        dist[idx] += TYPE_GAIN
                    if line.link_bus == line.line_uuid:
                        dist[idx] -= TYPE_GAIN / 2
            idx += 1
    else:
        idx += len(lines)
    
    if (text_device_match(text_type, DeviceType.PORT)):
        for port in ports:
            if port is None:
                idx += 1
                continue
            distance = calculate_distance_point(text_bbox, port.coor)
            if distance < CLOSE_THRESHOLD:
                    if distance < VERY_CLOSE_THRESHOLD:
                        dist[idx] = 1 / VERY_CLOSE_THRESHOLD + (VERY_CLOSE_THRESHOLD - distance) / CLOSE_THRESHOLD
                    else: dist[idx] = 1 / distance
                    if (text_device_match(text_type, DeviceType.LINK)):
                        dist[idx] += TYPE_GAIN
            idx += 1
    else:
        idx += len(ports)

    return False, dist

def attach_mac_protocol(ports:[Port], devices:[Device], text):
    '''
    Attach the ip or mac address (without masks) to the closest port.
    '''
    dist = [-float("inf")] * (len(devices) + len(ports))
    text_bbox = text[0]
    idx = 0

    for device in devices:
        distance = calculate_distance_box(text_bbox, device.bbox)
        if distance < CLOSE_THRESHOLD:
            if distance < VERY_CLOSE_THRESHOLD:
                dist[idx] = 1 / VERY_CLOSE_THRESHOLD + (VERY_CLOSE_THRESHOLD - distance) / CLOSE_THRESHOLD
            else: dist[idx] = 1 / distance
        if device.device_type == DeviceType.BLOCK:
            dist[idx] *= PUNISH_RATIO
        idx += 1
    
    PORT_GAIN = 0.5
    for port in ports:
        if port is None:
            idx += 1
            continue
        distance = calculate_distance_point(text_bbox, port.coor)
        if distance < CLOSE_THRESHOLD:
            if distance < VERY_CLOSE_THRESHOLD:
                dist[idx] = 1 / VERY_CLOSE_THRESHOLD + (VERY_CLOSE_THRESHOLD - distance) / CLOSE_THRESHOLD
            else: dist[idx] = 1 / distance
            if port.device >= 0: dist[idx] += PORT_GAIN
        idx += 1
    
    return dist

def attach_ip(devices:[Device], lines:[Line], ports:[Port], text):
    dist = [-float("inf")] * (len(devices) + len(ports) + len(lines))
    text_bbox = text[0]
    idx = 0

    if text[2] == TextType.IP_WITH_MASK:
        for device in devices:
            distance = calculate_distance_box(text_bbox, device.bbox)
            if distance < CLOSE_THRESHOLD:
                if distance < 0:
                    dist[idx] = 1 / VERY_CLOSE_THRESHOLD + (VERY_CLOSE_THRESHOLD - distance) / CLOSE_THRESHOLD
                else: dist[idx] = 1 / (CLOSE_THRESHOLD * 10)
            if device != DeviceType.BLOCK:
                dist[idx] = 0
            idx += 1
        
        LINE_GAIN = 15
        DIFF_THRESHOLD = 100
        for line in lines:
            if line is None:
                idx += 1
                continue
            distance = calculate_distance_line(text_bbox, line)
            if distance < CLOSE_THRESHOLD:
                if distance < VERY_CLOSE_THRESHOLD:
                    dist[idx] = 1 / VERY_CLOSE_THRESHOLD + (VERY_CLOSE_THRESHOLD - distance) / CLOSE_THRESHOLD
                else: dist[idx] = 1 / distance
                
                x1, y1 = min(line.line[0][0], line.line[1][0]), min(line.line[0][1], line.line[1][1])
                x2, y2 = max(line.line[0][0], line.line[1][0]), max(line.line[0][1], line.line[1][1])
                
                flag = (x1 <= text_bbox[2] and x2 >= text_bbox[0]) or (y1 <= text_bbox[3] and y2 >= text_bbox[1])
                if (x2 - x1 > 1.5*(y2 - y1) or x2 - x1 > DIFF_THRESHOLD ):
                    if text_bbox[2] < x1 or text_bbox[0] > x2:
                        flag = False 
                
                if (1.5*(x2 - x1) < y2 - y1 or y2 - y1 > DIFF_THRESHOLD):
                    if text_bbox[1] > y2 or text_bbox[3] < y1:
                        flag = False
                
                if (flag): dist[idx] += LINE_GAIN
                else: dist[idx] /= 20
            idx += 1
        
        for port in ports:
            if port is None:
                idx += 1
                continue
            distance = calculate_distance_point(text_bbox, port.coor)
            if distance < CLOSE_THRESHOLD:
                if distance < VERY_CLOSE_THRESHOLD:
                    dist[idx] = 1 / VERY_CLOSE_THRESHOLD + (VERY_CLOSE_THRESHOLD - distance) / CLOSE_THRESHOLD
                else: dist[idx] = 1 / distance
                dist[idx] /= 10
            idx += 1

    else:
        
        for device in devices:
            distance = calculate_distance_box(text_bbox, device.bbox)
            if distance < CLOSE_THRESHOLD:
                if distance < VERY_CLOSE_THRESHOLD:
                    dist[idx] = 1 / VERY_CLOSE_THRESHOLD + (VERY_CLOSE_THRESHOLD - distance) / CLOSE_THRESHOLD
                else: dist[idx] = 1 / distance
            if device.device_type == DeviceType.BLOCK:
                dist[idx] *= PUNISH_RATIO   
            idx += 1

        idx += len(lines)
        
        PORT_GAIN = 0.5
        for port in ports:
            if port is None:
                idx += 1
                continue
            distance = calculate_distance_point(text_bbox, port.coor)
            if distance < CLOSE_THRESHOLD:
                if distance < VERY_CLOSE_THRESHOLD:
                    dist[idx] = 1 / VERY_CLOSE_THRESHOLD + (VERY_CLOSE_THRESHOLD - distance) / CLOSE_THRESHOLD
                else: dist[idx] = 1 / distance
                if port.device >= 0: dist[idx] += PORT_GAIN
            idx += 1
        
    return dist

def nearest_point(bbox, point):
    bbox_points = [(bbox[0], bbox[1]), (bbox[0], bbox[3]), (bbox[2], bbox[1]), (bbox[2], bbox[3])]
    dist = [math.dist(pa, point) for pa in bbox_points]
    return bbox_points[dist.index(min(dist))]

def attach_all(texts, devices:[Device], lines:[Line], ports:[Port], ADJUST_RATIO=1.0):
    global CLOSE_THRESHOLD, VERY_CLOSE_THRESHOLD
    CLOSE_THRESHOLD = CLOSE_THRESHOLD_BASE * ADJUST_RATIO
    VERY_CLOSE_THRESHOLD = VERY_CLOSE_THRESHOLD_BASE * ADJUST_RATIO
    ip = []
    ip_text = []
    mac = []
    mac_text = []
    protocol = []
    protocol_text = []

    name = []
    name_text = []
    name_type = []
    name_type_text = []
    for idx, text in enumerate(texts):
        text_type = get_basic_type(text[2])
        if (text_type == TextType.IP):
            dist = attach_ip(devices, lines, ports, text)
            ip.append(dist)
            ip_text.append(idx)
        elif (text_type == TextType.MAC):
            dist = attach_mac_protocol(ports, devices, text)
            mac.append(dist)
            mac_text.append(idx)
        elif (text_type == TextType.PROTOCOL):
            dist = attach_mac_protocol(ports, devices, text)
            protocol.append(dist)
            protocol_text.append(idx)
        elif (text_type == TextType.COMMENT ): 
            attach_comment(devices, lines, ports, text) # one device can be attached to multiple comments
        elif (text_type == TextType.NAME): 
            is_type, dist = attach_name(devices, lines, ports, text)
            if is_type:
                name_type.append(dist)
                name_type_text.append(idx)
            else:
                name.append(dist)
                name_text.append(idx)
    
    ip_match = best_match_km(ip)
    mac_match = best_match_km(mac)
    protocol_match = best_match_km(protocol)
    name_match = best_match_km(name)
    name_type_match = best_match_km(name_type)

    for i in range(len(ip_match)):
        if ip_match[i] != -1 and ip[i][ip_match[i]] > 0:
            if ip_match[i] < len(devices):
                devices[ip_match[i]].device_ip = texts[ip_text[i]][1]
            else:
                ip_match[i] -= len(devices)
                if ip_match[i] < len(lines):
                    lines[ip_match[i]].link_ip = texts[ip_text[i]][1]
                else:
                    ip_match[i] -= len(lines)
                    ports[ip_match[i]].port_ip = texts[ip_text[i]][1]
                    device_idx = ports[ip_match[i]].device
                    if device_idx >= 0:
                        device = devices[device_idx]
                        if device is not None and any(device.device_type == d_type for d_type in [DeviceType.BLOCK, DeviceType.SUBNET]) \
                            and bbox_no_intersect(device.bbox, texts[ip_text[i]][0]):
                            ports[ip_match[i]].device = -1
                            line = lines[ports[ip_match[i]].line_uuid]
                            ports[ip_match[i]].coor = nearest_point(texts[ip_text[i]][0], ports[ip_match[i]].coor)
                            if line is not None:
                                if line.st_port == ip_match[i]:
                                    line.line[0] = ports[ip_match[i]].coor
                                else:
                                    line.line[1] = ports[ip_match[i]].coor
                            device.ports.remove(ip_match[i])
    
    for i in range(len(mac_match)):
        if mac_match[i] != -1 and mac[i][mac_match[i]] > 0:
            if mac_match[i] < len(devices):
                devices[mac_match[i]].device_mac = texts[mac_text[i]][1]
            else:
                mac_match[i] -= len(devices)
                ports[mac_match[i]].port_mac = texts[mac_text[i]][1]
    
    for i in range(len(protocol_match)):
        if protocol_match[i] != -1 and protocol[i][protocol_match[i]] > 0:
            if protocol_match[i] < len(devices):
                devices[protocol_match[i]].device_protocol = texts[protocol_text[i]][1]
            else:
                protocol_match[i] -= len(devices)
                ports[protocol_match[i]].port_protocol = texts[protocol_text[i]][1]
    
    for i in range(len(name_match)):
        if name_match[i] != -1 and name[i][name_match[i]] > 0:
            if (name_match[i] < len(devices)):
                devices[name_match[i]].device_name = texts[name_text[i]][1]
                tt = texts[name_text[i]][2]
                dt = devices[name_match[i]].device_type
                if (not text_device_match(tt, dt) and dt != DeviceType.BLOCK) or text_deep_device(tt, dt):
                    devices[name_match[i]].device_type = DeviceType[tt.name[:-5]]
            else:
                name_match[i] -= len(devices)
                if (name_match[i] < len(lines)): 
                    lines[name_match[i]].link_name = texts[name_text[i]][1]
                else:
                    name_match[i] -= len(lines)
                    ports[name_match[i]].port_name = texts[name_text[i]][1]
    
    for i in range(len(name_type_match)):
        if name_type_match[i] != -1 and name_type[i][name_type_match[i]] > 0:
            devices[name_type_match[i]].device_type = DeviceType[texts[name_type_text[i]][1].upper()]

def bbox_no_intersect(bbox1, bbox2):
    return bbox1[0] > bbox2[2] or bbox1[2] < bbox2[0] or bbox1[1] > bbox2[3] or bbox1[3] < bbox2[1]

def remove_duplicate_lines(devices:[Device], lines:[Line], ports:[Port]):
    for port in ports:
        if port is None: continue
        if port.device>=0 and devices[port.device].device_type == DeviceType.BLOCK:
            if port.port_name == "" and port.port_comment == "" and port.port_ip == "" and port.port_mac == "":
                if (lines[port.line_uuid] is not None):
                    line = lines[port.line_uuid]
                    if (port.port_uuid == line.st_port):
                        if line.en_port >= 0: 
                            if ports[line.en_port] is not None and ports[line.en_port].device >= 0:
                                if bbox_no_intersect(devices[ports[line.en_port].device].bbox, devices[port.device].bbox):
                                    continue
                                devices[ports[line.en_port].device].ports.remove(line.en_port)
                            ports[line.en_port] = None
                    elif line.st_port >= 0:
                        if ports[line.st_port] is not None and ports[line.st_port].device >= 0:
                            if bbox_no_intersect(devices[ports[line.st_port].device].bbox, devices[port.device].bbox):
                                continue
                            devices[ports[line.st_port].device].ports.remove(line.st_port)
                        ports[line.st_port] = None
                    lines[port.line_uuid] = None
                devices[port.device].ports.remove(port.port_uuid)
                ports[port.port_uuid] = None
