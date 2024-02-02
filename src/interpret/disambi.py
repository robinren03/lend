from analyse.object import Device, Port, Line, DeviceType,  TextType
from analyse.process_ocr import is_ip, is_device_name
from kg.attach import bbox_no_intersect
import copy

def convert_port_to_devices(devices:[Device], ports:[Port]):
    for port in ports:
        if port is None: continue
        if port.device >= 0: continue
        if port.port_name == "" and port.port_comment == "" and port.port_ip == "" and port.port_mac == "": continue
        if port.port_name == "" or port.port_comment == "" or is_device_name(port.port_name) != TextType.PORT_NAME:
            if (port.port_ip != "" and is_ip(port.port_ip) == TextType.IP_WITH_MASK):
                new_device = Device((port.coor[0]-5, port.coor[1]-5, port.coor[0]+5, port.coor[1]+5), len(devices), DeviceType.SUBNET, ports=[port.port_uuid], device_name=port.port_name, device_comment=port.port_comment, device_ip=port.port_ip, device_mac=port.port_mac)
                port.device = new_device.device_uuid
                port.port_name = ""
                port.port_ip = ""
                port.port_mac = ""
                devices.append(new_device)
            else:
                new_device = Device((port.coor[0]-5, port.coor[1]-5, port.coor[0]+5, port.coor[1]+5), len(devices), DeviceType.DEVICE, ports=[port.port_uuid], device_name=port.port_name, device_comment=port.port_comment, device_ip=port.port_ip, device_mac=port.port_mac)
                port.device = new_device.device_uuid
                port.port_name = ""
                port.port_ip = ""
                port.port_mac = ""
                devices.append(new_device)


def convert_line_to_devices(lines:[Line], devices:[Device], ports:[Port]):
    to_bus = []
    for line in lines:
        if line is None: continue
        if (line.st_port >= 0 and ports[line.st_port] is not None and ports[line.st_port].device >= 0) or \
            (line.en_port >= 0 and ports[line.en_port] is not None and ports[line.en_port].device >= 0) : continue
        if (line.link_ip != "" or line.link_name != "") and line.link_bus >= 0 and line.link_bus != line.line_uuid:
            x1, y1 = min(line.line[0][0], line.line[1][0]), min(line.line[0][1], line.line[1][1])
            x2, y2 = max(line.line[0][0], line.line[1][0]), max(line.line[0][1], line.line[1][1])
            new_device = Device((x1-5, y1-5, x2+5, y2+5), len(devices), DeviceType.SUBNET, line.link_name, line.link_comment, device_ip=line.link_ip)
            devices.append(new_device) 
            to_bus.append((line.link_bus, new_device.device_uuid, line.bus_pt))
        if (line.st_port >= 0): ports[line.st_port] = None
        if (line.en_port >= 0): ports[line.en_port] = None
        lines[line.line_uuid] = None

    return to_bus

def convert_block_to_devices(devices:[Device]):
    for device in devices:
        if device is None: continue
        if device.device_type != DeviceType.BLOCK: continue

        device.contain = []
        for dvc in devices:
            if dvc is None: continue
            if device.device_uuid != dvc.device_uuid:
                if dvc.device_type == DeviceType.BLOCK:
                    if device.bbox[0] <= dvc.bbox[0] and dvc.bbox[2] <= device.bbox[2] and device.bbox[1] <= dvc.bbox[1] and dvc.bbox[3] <= device.bbox[3]:
                        device.contain.append(dvc.device_uuid) 
                elif not bbox_no_intersect(dvc.bbox, device.bbox):
                    device.contain.append(dvc.device_uuid)
        
        if len(device.contain) > 0 or (device.device_ip != "" and is_ip(device.device_ip) == TextType.IP_WITH_MASK): 
            device.device_type = DeviceType.SUBNET
        elif len(device.ports) > 0:
            device.device_type = DeviceType.DEVICE       

def convert_bus_to_devices(devices:[Device], lines:[Line], ports:[Port], to_bus):
    bus_device = {}   
    for line in lines:
        if line is None: continue
        if line.link_bus == line.line_uuid:
            bus_uuid = len(devices)
            bus_device[line.line_uuid] = bus_uuid
            bus = Device((min(line.line[0][0],line.line[1][0])-5, min(line.line[0][1],line.line[1][1])-5, max(line.line[0][0],line.line[1][0])+5, max(line.line[0][1],line.line[1][1])+5), len(devices), DeviceType.BUS, line.link_name, line.link_comment, line.link_ip)
            if (line.st_port >= 0):
                old_port = ports[line.st_port]
                if old_port is not None and old_port.device >= 0:
                    new_port_uuid = len(ports)
                    new_line_uuid = len(lines)
                    lines.append(Line([line.line[0], line.line[0]], [], line_uuid = new_line_uuid, st_port = line.st_port, en_port = new_port_uuid, real_line=False))
                    old_port.line_uuid = new_line_uuid
                    ports.append(Port(line.line[0], bus_uuid, new_line_uuid, new_port_uuid))
                    bus.ports.append(new_port_uuid)
                    bus.st_dvc_port = new_port_uuid
                
            if (line.en_port >= 0):
                old_port = ports[line.en_port]
                if old_port is not None and old_port.device >= 0:
                    new_port_uuid = len(ports)
                    new_line_uuid = len(lines)
                    lines.append(Line([line.line[1], line.line[1]], [], line_uuid = new_line_uuid, st_port = line.en_port, en_port = new_port_uuid, real_line=False))
                    old_port.line_uuid = new_line_uuid
                    ports.append(Port(line.line[1], bus_uuid, new_line_uuid, new_port_uuid))
                    bus.ports.append(new_port_uuid)
                    bus.en_dvc_port = new_port_uuid
            
            lines[line.line_uuid] = None
            devices.append(bus)

        elif line.link_bus >= 0:
            if not line.link_bus in bus_device:
                line.link_bus = -1
                line.st_to_bus = False
                line.en_to_bus = False
                continue
            if (line.st_to_bus):
                new_port_uuid = len(ports)
                ports.append(Port(line.line[0], bus_device[line.link_bus], line.line_uuid, new_port_uuid))
                line.st_port = new_port_uuid
                devices[bus_device[line.link_bus]].ports.append(new_port_uuid)
            elif (line.en_to_bus):
                new_port_uuid = len(ports)
                ports.append(Port(line.line[1], bus_device[line.link_bus], line.line_uuid, new_port_uuid))
                line.en_port = new_port_uuid
                devices[bus_device[line.link_bus]].ports.append(new_port_uuid)
            else:
                if (line.st_port >= 0):
                    old_port = ports[line.st_port]
                    if old_port is not None and old_port.device >= 0:
                        bus_port_uuid = len(ports)
                        dvc_port_uuid = bus_port_uuid + 1

                        new_line_uuid = len(lines)
                        lines.append(Line([line.line[0], line.bus_pt], [], line_uuid = new_line_uuid, st_port = bus_port_uuid, en_port = dvc_port_uuid, real_line=False))
                        ports.append(Port(line.bus_pt, bus_device[line.link_bus], new_line_uuid, bus_port_uuid))
                        dvc_port = copy.copy(old_port)
                        dvc_port.port_uuid = dvc_port_uuid
                        dvc_port.line_uuid = new_line_uuid
                        ports.append(dvc_port)

                        devices[bus_device[line.link_bus]].ports.append(bus_port_uuid)
                        devices[old_port.device].ports.append(dvc_port_uuid)
                
                if (line.en_port >= 0):
                    old_port = ports[line.en_port]
                    if old_port is not None and old_port.device >= 0:
                        bus_port_uuid = len(ports)
                        dvc_port_uuid = bus_port_uuid + 1

                        new_line_uuid = len(lines)
                        lines.append(Line([line.line[1], line.bus_pt], [], line_uuid = new_line_uuid, st_port = bus_port_uuid, en_port = dvc_port_uuid, real_line=False))
                        
                        ports.append(Port(line.bus_pt, bus_device[line.link_bus], new_line_uuid, bus_port_uuid))
                        dvc_port = copy.copy(old_port)
                        dvc_port.port_uuid = dvc_port_uuid
                        dvc_port.line_uuid = new_line_uuid
                        ports.append(dvc_port)
                        
                        devices[bus_device[line.link_bus]].ports.append(bus_port_uuid)
                        devices[old_port.device].ports.append(dvc_port_uuid)
    
    for bus_id, device_id, pt in to_bus:
        if (ports[bus_id] is None): continue
        new_port_uuid = len(ports)
        ports.append(Port(pt, device_id, ports[bus_id].line_uuid, new_port_uuid))
        devices[device_id].ports.append(new_port_uuid)
        ports[bus_id] = None

def remove_features(devices:[Device], lines:[Line], ports:[Port]):
    for device in devices:
        if device.device_name == "":
            device.device_name = "Device" + str(device.bbox)
        device.bbox = None
    
    for line in lines:
        if line is None: continue
        if line.link_name == "":
            line.link_name = "Line"+str(line.line)
        line.bus_pt = None
        line.anchor = None
        line.line = None
        line.link_bus, line.st_to_bus, line.en_to_bus = None, None, None
    
    for port in ports:
        if port is None: continue
        if port.port_name == "":
            port.port_name = "Port" + str(port.coor)
        port.coor = None
    
def optimize_json(devices, lines, ports):
    convert_port_to_devices(devices, ports)
    to_bus = convert_line_to_devices(lines, devices, ports)
    convert_block_to_devices(devices)
    convert_bus_to_devices(devices, lines, ports, to_bus)
    remove_features(devices, lines, ports)