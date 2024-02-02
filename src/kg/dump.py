import json
from analyse.object import Device, Line, Port, DeviceType
from PIL import Image, ImageDraw

def filter_dict(dict, filter):
    if (not filter): return dict
    return {key: value for key, value in dict.items() if value is not None and value != "" and (not isinstance(value, int) or value >= 0) and (not isinstance(value, list) or len(value) > 0)}

def first_step_dump(devices:[Device], lines:[Line], output_path:str, imageWidth:int, imageHeight:int, Hefilter = False):
    data = {
        'devices': [filter_dict(device.__dict__, filter) for device in devices if device is not None],
        'lines': [filter_dict(line.__dict__, filter) for line in lines if line is not None],
        'imageWidth': imageWidth,
        'imageHeight': imageHeight,
    }
    with open(output_path, 'w') as file:
        json.dump(data, file, default=str, indent=4)

def dump(devices:[Device], lines:[Line], ports:[Port], output_path:str, filter = True):
    '''
    Dump the devices, lines and ports to a json file.
    '''
    data = {
        'devices': [filter_dict(device.__dict__, filter) for device in devices if device is not None],
        'lines': [filter_dict(line.__dict__, filter) for line in lines if line is not None],
        'ports': [filter_dict(port.__dict__, filter) for port in ports if port is not None]
    }

    with open(output_path, 'w') as file:
        json.dump(data, file, default=str, indent=4)
    

def visualize(devices:[Device], lines:[Line], ports:[Port], output_path:str, col:int, row:int):
    if not (output_path.endswith(".jpg") or output_path.endswith(".png") or output_path.endswith("jpeg")):
        raise Exception("output_path must be a jpg or png file.")
    
    canvas = Image.new('RGB', (col, row), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    
    for device in devices:
        if device.device_type == DeviceType.BLOCK or device.device_type == DeviceType.SUBNET:
            x1, y1, x2, y2 = device.bbox
            draw.rectangle([(x1, y1), (x2, y2)], fill=(0, 255, 0))

    for device in devices:
        if device.device_type == DeviceType.BLOCK or device.device_type == DeviceType.SUBNET: continue
        x1, y1, x2, y2 = device.bbox
        draw.rectangle([(x1, y1), (x2, y2)], fill=(255, 0, 0))
        if device.device_name is None: device.device_name = ""
        draw.text((x1, y1), str(device.device_type) + device.device_name, fill=(0, 0, 0))
        
    for line in lines:
        if line is None: continue
        prev_point = line.line[0]
        for point in line.anchor:
            draw.line([prev_point, point], fill=(0, 0, 0), width=2)
            prev_point = point
        last_point = line.line[1]
        draw.line([prev_point, last_point], fill=(0, 0, 0), width=2)
    
    for port in ports:
         if port is None: continue
         point_x, point_y = port.coor
         draw.ellipse((point_x - 3, point_y - 3, point_x + 3, point_y + 3), fill="blue")
    
    canvas.save(output_path)
    