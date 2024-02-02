import json
import os

def convert_json(json_path):
    with open(json_path, "r") as json_path:
        entities = json.load(json_path)
    devices = entities["devices"]
    id2dvc = {}
    for idx, device in enumerate(devices):
        id2dvc[device["device_uuid"]] = idx
    lines = entities["lines"]
    id2line = {}
    for idx, line in enumerate(lines):
        id2line[line["line_uuid"]] = idx
    ports = entities["ports"]
    id2port = {}
    for idx, port in enumerate(ports):
        id2port[port["port_uuid"]] = idx

    all_descp = []
    for device in devices:
        if "device_name" in device:
            device_desp = device["device_name"] + " is a " + device["device_type"].lower()
        
        if "device_ip" in device:
            device_desp += ", with IP " + device["device_ip"]
        
        if "device_mac" in device:
            device_desp += ", with MAC " + device["device_mac"]

        if "device_comment" in device:
            device_desp += ", " + device["device_comment"]
        
        if ("ports" in device and len(device["ports"])>0):
            device_desp += ",\n with ports: "
            for port_idx in device["ports"]:
                if port_idx not in id2port:
                    continue
                port = ports[id2port[port_idx]]
                if "port_name" in port:
                    device_desp += port["port_name"] + " "

                if "port_ip" in port:
                    device_desp += "with IP " + port["port_ip"] + " "
                if "port_mac" in port:
                    device_desp += "with MAC " + port["port_mac"] + " "
                if "port_comment" in port:
                    device_desp += "," + port["port_comment"] + " "

                if (port["line_uuid"] not in id2line):
                    continue

                line = lines[id2line[port["line_uuid"]]]
                if "link_name" in line:
                    device_desp += "connected to " + line["link_name"] + " "

                if "link_ip" in line:
                    device_desp += "with IP range of " + line["link_ip"] + " "
                if "link_comment" in line:
                    device_desp += line["link_comment"] + " "

                st_port = line["st_port"] if "st_port" in line else -1
                en_port = line["en_port"] if "en_port" in line else -1
                other_end = None
                if (st_port == port_idx and en_port >= 0):
                    if (en_port not in id2port):
                        continue
                    other_end = ports[id2port[en_port]]
                elif (en_port == port_idx and st_port >= 0):
                    if (st_port not in id2port):
                        continue
                    other_end = ports[id2port[st_port]]
                
                if (other_end is not None and "device" in other_end):
                    device_desp += "all the way to "
                    other_device = devices[id2dvc[other_end["device"]]]
                    if "device_name" in other_device:
                        device_desp += other_device["device_name"] + " "
                        
                if "real_line" not in line or not line["real_line"]:
                    device_desp += "logically (not real)"
                device_desp += "\n "
        
        all_descp.append(device_desp)
    
    return '\n'.join(all_descp)
