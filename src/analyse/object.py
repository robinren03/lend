import enum
from dataclasses import dataclass, field


ALIAS = {"WORKSTATION":["computer", "pc", "desktop", "laptop", "console", "client"], "SWITCH":["sw"], "ROUTER":["R"], "LINK":["dash line", "lightning line", "line", "expressway"], "AP":["Access Point"]}

class DeviceType(enum.Enum):
    '''
    The type of device.
    '''
    FAILED = 0
    DEVICE = 1 # A more general device
    FORWARDING_DEVICE = 10
    SWITCH = 101
    ROUTER = 102
    AP = 11
    SITE = 12
    END_DEVICE = 13
    WORKSTATION = 131
    USER = 132
    SERVER = 133
    FIREWALL = 14
    BLOCK = 15
    SUBNET = 151
    DEVICE_BLOCK = 152
    TELEPHONE = 16
    BUS=17
    SERVICE=18
    LINK = 2
    PORT = 3

    def __str__(self):
        return self.name

class TextType(enum.Enum):
    '''
    The type of text.
    '''
    FAILED = 0
    NAME = 1
    IP = 2
    MAC = 3
    PROTOCOL = 4
    COMMENT = 5

    TYPE_NAME = 10
    DEVICE_TYPE = 101 
    LINK_TYPE = 102
    DEVICE_NAME = 11
    FORWARDING_DEVICE_NAME = 110
    SWITCH_NAME = 1101
    ROUTER_NAME = 1102
    AP_NAME = 111
    SITE_NAME = 112
    END_DEVICE_NAME = 113
    WORKSTATION_NAME = 1131
    USER_NAME = 1132
    SERVER_NAME = 1133
    FIREWALL_NAME = 114
    BLOCK_NAME = 115
    SUBNET_NAME = 1151
    TELEPHONE_NAME = 116
    BUS_NAME = 117
    SERVICE_NAME = 118
    LINK_NAME = 12
    PORT_NAME = 13

    IP_ADDR = 20
    IP_WITH_MASK = 21
    IP_HOST_ONLY = 22

    ROUTING_PROTOCOL = 40
    OTHER_PROTOCOL = 41
    BGP_PROTOCOL = 401
    OSPF_PROTOCOL = 402
    RIP_PROTOCOL = 403
    OTHER_ROUTING = 404

    def __str__(self):
        return self.name

@dataclass
class Port:
    '''
    A port of a device. 
    '''
    coor : (int, int)
    device : int
    line_uuid : int
    port_uuid : int
    port_mac : str = ""
    port_ip : str = ""
    port_name : str = ""
    port_comment: str = ""

@dataclass
class Device:
    '''
    A device in the network.
    '''
    bbox : (int, int, int, int)
    device_uuid : int
    device_type : DeviceType
    device_name : str = ""
    device_comment : str = ""
    device_ip: str = ""
    device_mac: str = ""
    ports : [int] = field(default_factory=list) # each int is a port index in the ports list   

@dataclass
class Line:
    '''
    A line in the network.
    '''
    line : [(int, int), (int, int)]
    anchor: [(int, int)] = field(default_factory=list)
    line_uuid : int = 0
    link_comment : str = ""
    link_name : str = ""
    link_bus : int = -1
    st_to_bus : bool = False
    en_to_bus : bool = False
    bus_pt: (int, int) = (-1, -1)
    real_line : bool = True
    st_port : int = -1
    en_port : int = -1
    link_ip: str = ""

def get_lines_by_uuid(lines:[Line], uuid:int):
    if (uuid < 0): return None
    for line in lines:
        if line.line_uuid == uuid: return line
    return None

def get_devices_by_uuid(devices:[Device], uuid:int):
    if (uuid < 0): return None
    for device in devices:
        if device.device_uuid == uuid: return device
    return None

def get_port_by_uuid(ports:[Port], uuid:int):
    if (uuid < 0): return None
    for port in ports:
        if port.port_uuid == uuid: return port
    return None