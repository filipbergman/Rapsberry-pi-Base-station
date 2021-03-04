from multiprocessing import Process
from tuntap import TunTap
import socket
import time
import board
import busio
import digitalio
import adafruit_rfm9x
import numpy as np
import atexit
import ipaddress

import sys
# sys.path is a list of absolute path strings
sys.path.append('/var/www/mypython-test')

import index

RADIO_FREQ_MHZR = 868.0  # Frequency of the radio in Mhz. Must match your
RADIO_FREQ_MHZT = 869.0

CSR = digitalio.DigitalInOut(board.CE1)
RESETR = digitalio.DigitalInOut(board.D25)

CST = digitalio.DigitalInOut(board.D17)
RESETT = digitalio.DigitalInOut(board.D4)

spiR = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
spiT = busio.SPI(board.D21, MOSI=board.D20, MISO=board.D19)

rfm9xR = adafruit_rfm9x.RFM9x(spiR, CSR, RESETR, RADIO_FREQ_MHZR)
rfm9xT = adafruit_rfm9x.RFM9x(spiT, CST, RESETT, RADIO_FREQ_MHZT)

# Radio 1: Receiver
# enable CRC checking
#rfm9xR.enable_crc = True
rfm9xR.node = 3
rfm9xR.destination = 4
rfm9xR.spreading_factor = 10
#rfm9xR.signal_bandwidth = 125000
counterR = 0

# Radio 2: Transmitter NOT WORKING
# enable CRC checking
#rfm9xT.enable_crc = True
rfm9xT.node = 1
rfm9xT.destination = 2
rfm9xT.tx_power = 5
rfm9xT.spreading_factor = 10
rfm9xT.ack_retries = 1
#rfm9xT.signal_bandwidth = 125000
counterT = 0

import MySQLdb
conn = MySQLdb.connect('localhost', 'pi', 'pi', 'dbtest')

iface= 'tun0'
tun = TunTap(nic_type="Tun", nic_name="tun0")
tun.config(ip="192.168.2.15", mask="255.255.255.0", gateway="192.168.0.1")

this_ip = ipaddress.IPv4Address('192.168.2.15')
base1 = ipaddress.IPv4Address('192.168.2.16')
test1 = ipaddress.IPv4Address('192.168.2.2')

ipList = []
ipList.append(this_ip)
ipList.append(base1)
ipList.append(test1)

# Set up UDP tunnel
RECEIVER_IP = "192.168.0.170" # Should be receiver's IP on the local network
MY_IP = "192.168.0.193" # Should be this node's IP on the local network
UDP_PORT = 4003

tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rx_sock.bind((MY_IP, UDP_PORT))

def exit_handler():
    tun.close()

def transmit_message(message):
    tx_sock.sendto(message, (RECEIVER_IP, UDP_PORT))

def transmit():
    while True:
        buf= tun.read(1024)
        #print("TUN BUFFER: ", buf)
        tx_sock.sendto( buf, (RECEIVER_IP, UDP_PORT))

def receive():
    while True:
        rcvd, addr = rx_sock.recvfrom(1024)
        if rcvd is not None:
            
            rcvd_hex = rcvd.hex()
            print("hex: ", rcvd_hex[:2])
            if rcvd_hex[:2] == "45": # If ipv4 packet header, write to tun interface:
                print("WRITE TO TUN", rcvd)
                tun.write(rcvd)
            elif rcvd_hex[:2] == "31":
                # if control packet:
                rcvd = rcvd.decode()
                print("Handshake")
                control_packet(rcvd[0], rcvd[1:])
            elif rcvd_hex[:2] == "30":
                # if data packet:
                rcvd = rcvd.decode()
                print("Data packet")
                control_packet(rcvd[0], rcvd[1:])
                

def control_packet(frame_type, data):
    print("RECEIVED")
    print("FRAME TYPE: ", frame_type)
    print("data: ", data)

    if frame_type == "0":
        print("\nData plane\n")
        index.commit_line(data)
        
    elif frame_type == "1":
        print("\nControl plane\n")
        tun_ip = ""
        for i in range(0, 4):
            tun_ip += str(int(data[i*8:(i*8)+8], 2)) # Translates each octet from bits to decimal
            if i != 3:
                tun_ip += "."
        tun_ip = ipaddress.IPv4Address(tun_ip)
        print("RECEIVED IP: ", tun_ip)

        if tun_ip not in ipList:
            print("UNIQUE IP")
            f = frame(int(frame_type), tun_ip)
            f2 = f.createControlFrame()
            transmit_message(f2)
        elif tun_ip in ipList:
            print("IP ALREADY EXISTS")
            for i in range(10,254):
                test_ip = "192.168.2." + str(i)
                ipv4 = ipaddress.IPv4Address(test_ip)
                if ipv4 not in ipList:
                    print("FOUND UNIQUE IP")
                    f = frame(int(frame_type), ipv4)
                    f2 = f.createControlFrame()
                    transmit_message(f2)
                    break
        
class frame:
    frame_type = 0
    data = 0
    frame = 0

    def __init__(self, frame_type, data):
        self.frame_type = frame_type
        self.data = data

    def createFrame(self): 
        frame = format(self.frame_type, "b")
        data_int = int(self.data)
        data_bit = format(data_int, "032b")
        print("DATA_BIT: ", data_bit)
        frame += data_bit
        return frame.encode()

    def frame_from_bits(self):
        frame = self.frame_type
        frame += self.data
        return frame.encode()

    def createControlFrame(self): 
        frame = format(self.frame_type, "b")
        data_int = int(self.data)
        data_bit = format(data_int, "032b")
        print("DATA_BIT: ", data_bit)
        frame += data_bit
        return frame.encode()
           
if __name__ == "__main__":
    atexit.register(exit_handler)
    tx_process = Process(target=transmit)
    rx_process = Process(target=receive)

    rx_process.start()
    time.sleep(1)
    tx_process.start()

    tx_process.join()
    rx_process.join()