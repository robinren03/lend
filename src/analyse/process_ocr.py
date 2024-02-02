'''
Text classifier for OCR results. Perform text box connection and text classifcation.
'''
import re
import ipaddress
from analyse.box_connector import BoxesConnector
from analyse.object import ALIAS
import numpy as np
from analyse.object import *
from functools import cmp_to_key

def is_ip(s:str)->TextType:
    '''
    Check if s is a valid IPv4 or IPv6 address (with or without mask) or 
    an abbreviated address with only the host portion.
    '''
    s = s.strip()
    if s.startswith("IP"):
        s1 = re.sub(r'^\D*', '', s)
    else:
        s1 = s

    if (len(s1) == 0): return TextType.FAILED   
    if (s1[0]=="."):
        num_dots = s.count(".")
        full = "0"
        for _ in range( 3 - num_dots):
            full += ".0"
        s1 = full + s1
        return TextType.IP_HOST_ONLY
    try:
        ip = ipaddress.ip_network(s1, strict=False)
        return TextType.IP_ADDR if ip.prefixlen==32 or not s1.startswith(str(ip.network_address)) else TextType.IP_WITH_MASK
    except ValueError:
        return TextType.FAILED

def is_mac(s:str)->TextType:
    '''
    Check if s is a valid MAC address.
    '''
    s = s.strip()
    if s.startswith("MAC"):
        s1 = s[3:].strip()
        s1 = s1.strip(":")
        s1 = s1.strip()
        high_conf = True
    else:
        s1 = s
        high_conf = False
    
    s1=s1.lower()
    if (len(s1) == 0): return TextType.FAILED   
    if (high_conf): mac_address_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]{0,1}){5}([0-9A-Fa-f]{2})$')
    else: mac_address_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    mac_address_pattern_2 = re.compile(r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$')
    is_mac = bool(mac_address_pattern.match(s1) or mac_address_pattern_2.match(s1))
    if (is_mac): s=s1
    return TextType.MAC if is_mac else TextType.FAILED

def is_protocol(s:str)->TextType:
    s = re.sub(r'v\d+$', '', s)
    if 'OSPF' == s: return TextType.OSPF_PROTOCOL
    if 'BGP' == s: return TextType.BGP_PROTOCOL
    if 'RIP' == s: return TextType.RIP_PROTOCOL
    if "EIGRP" == s: return TextType.PROTOCOL
    return TextType.FAILED

def is_type_name(s:str)->TextType:
    for dt in DeviceType.__members__.keys():
        if dt == s.upper():
            return TextType.DEVICE_TYPE
    return TextType.FAILED

def is_device_name(s:str, correct:bool = True)->TextType:
    s1 = s.lower()
    if re.match(r'^\$((o|\d)+)+/\d+$', s1): s1 = s1.replace("$", "s", 1)
    if re.match(r'^(eth|s|e|fa)((o|\d)+/)+(o|\d)+$', s1): s1 = s1.replace("o", "0") 
    if re.match(r'^(eth|s|e|fa)(\d+/)+(\d)+$', s1):
        if (correct): s=s1
        return TextType.PORT_NAME
    
    s1 = s.strip().split()
    s1.reverse()
    ss = s1[0]
    for dt in DeviceType.__members__.keys():
        if dt in ss.upper():
            return TextType[dt.upper() + "_NAME"]
        
    for dt in DeviceType.__members__.keys():
        if dt in ALIAS:
            for alias in ALIAS[dt]:
                if alias.upper() in ss.upper() and (len(alias)>1 or ss[0]==alias[0] and ss[1:].isdigit()):
                        return TextType[dt.upper() + "_NAME"]
    
    for ss in s1[1:]:
        for dt in DeviceType.__members__.keys():
            if dt in ss.upper():
                return TextType.DEVICE_NAME
        if dt in ALIAS:
            for alias in ALIAS[dt]:
                if alias.upper() in ss.upper():
                    return TextType.DEVICE_NAME
    return TextType.NAME

def get_rect_points(text_boxes):
    x1 = np.min(text_boxes[:, 0])
    y1 = np.min(text_boxes[:, 1])
    x2 = np.max(text_boxes[:, 2])
    y2 = np.max(text_boxes[:, 3])
    return [x1, y1, x2, y2]

def compare_bbox(bbox1, bbox2):
    height1 = bbox1[3] - bbox1[1]
    height2 = bbox2[3] - bbox2[1]
    y0 = max(bbox1[1], bbox2[1])
    y1 = min(bbox1[3], bbox2[3])
    y_overlap = max(0, y1 - y0) / max(height1, height2)

    if y_overlap < 0.2:
        return -1 if bbox1[1] < bbox2[1] else 1
    return -1 if bbox1[0] < bbox2[0] else 1 if bbox1[0] > bbox2[0] else 0

def judge_good_name(rect_set, tr, boxes_unioned):
    ip_judge = is_ip(tr)
    mac_judge = is_mac(tr)
    protocol_judge = is_protocol(tr)
    type_judge = is_type_name(tr)

    if ip_judge != TextType.FAILED:
        boxes_unioned.append((rect_set, tr, ip_judge))
    elif mac_judge != TextType.FAILED:
        boxes_unioned.append((rect_set, tr, mac_judge))
    elif protocol_judge != TextType.FAILED:
        boxes_unioned.append((rect_set, tr, protocol_judge))
    elif type_judge != TextType.FAILED:
        boxes_unioned.append((rect_set, tr, type_judge))
    else:
        text_type = is_device_name(tr)
        if(text_type != TextType.NAME and text_type != TextType.DEVICE_NAME):
            boxes_unioned.append((rect_set, tr, text_type))
        else: return False

    return True

def get_pcbox(text_box, prefix_len, now_len, total_len):
    x1 = text_box[0] + prefix_len / total_len * (text_box[2] - text_box[0])
    y1 = text_box[1]
    x2 = x1 + now_len / total_len * (text_box[2] - text_box[0])
    y2 = text_box[3]
    return [x1, y1, x2, y2]

def union_text_boxes(text_boxes, texts):
    '''
    Union the text boxes into a single box.
    '''
    image_w = max([box[2] for box in text_boxes])
    connector = BoxesConnector(text_boxes, texts, image_w, max_dist=15, overlap_threshold=0.3)

    sub_graphs = connector.connect_boxes()
    set_element = set([y for x in sub_graphs for y in x]) 
    for idx, _ in enumerate(text_boxes):
        if idx not in set_element:
            sub_graphs.append([idx])  

    boxes_unioned = []
    text_boxes = np.array(text_boxes)
    for sub_graph in sub_graphs:
        rect_set = text_boxes[list(sub_graph)] 
        rect_set = get_rect_points(rect_set)
        a_text = ""
        sub_graph = sorted(sub_graph, key = cmp_to_key(lambda x,y: compare_bbox(text_boxes[x], text_boxes[y])))
        for idx in sub_graph:
            long_tr = texts[idx].strip()
            if judge_good_name(rect_set, long_tr, boxes_unioned):
                if (a_text != ""):
                    if len(a_text.split()) > 3 or any(not c.isalnum() and c != " " for c in a_text):
                        text_type = TextType.COMMENT
                    else:
                        text_type = is_device_name(a_text)
                    boxes_unioned.append((rect_set, a_text, text_type))
                a_text = ""
            else:
                prefix_len = 0
                total_len = len(long_tr)
                for tr in long_tr.split():
                    pc_box = get_pcbox(rect_set, prefix_len, len(tr), total_len) if a_text == "" else rect_set
                    prefix_len += len(tr) + 1
                    if(judge_good_name(pc_box, tr, boxes_unioned)):
                        a_text = a_text.strip()
                        if (a_text != ""):
                            text_type = TextType.COMMENT
                            boxes_unioned.append((pc_box, a_text, text_type))
                        a_text = ""
                    else: a_text += tr + " "
        
        a_text = a_text.strip()
        if (a_text != ""):
            if (judge_good_name(rect_set, a_text.strip(), boxes_unioned)):
                a_text = ""
            else:
                if len(a_text.split()) > 3 or any(not c.isalnum() and c != " " for c in a_text):
                    text_type = TextType.COMMENT
                else:
                    text_type = is_device_name(a_text)
                boxes_unioned.append((rect_set, a_text, text_type))
                a_text = ""

    return boxes_unioned