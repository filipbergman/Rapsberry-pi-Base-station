from tuntap import TunTap
import socket
import time
import busio
import digitalio
import ipaddress
import numpy as np

import ipaddress

class frame:
    frame_type = 0
    #fragment_id = 0 no need since I use small packets
    s_ip = 0
    d_ip = 0
    data = 0
    frame = 0

    def __init__(self, frame_type, data):
        self.frame_type = frame_type
        self.data = data

    def createFrame(self): 
        frame = format(self.frame_type, "#b")
        bit_data = bin(int(self.data))[2:]
        frame += format(bit_data)
        return frame

    def readFrame(self, new_frame):
        bytes_frame = 0

        return bytes_frame

if __name__ == "__main__":
    ip = ipaddress.IPv4Address('192.168.2.2')

    f1 = frame(0, ip)
    frame_bits = f1.createFrame()
    print("DATA: ", f1.data)
    print("BITS: ", frame_bits)