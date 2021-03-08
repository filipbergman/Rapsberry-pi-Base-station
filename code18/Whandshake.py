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
import threading

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

# Radio 2: Transmitter
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

lock = threading.Lock()

def exit_handler():
    tun.close()

def transmit_message(message):
    print("SENDING: ", message.hex())
    rfm9xT.send(message)

def bits_to_bytes(bits: str):
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))

def transmit():
    while True:
        buf= tun.read(252)
        #print("TUN BUFFER: ", buf)
        rfm9xT.send(buf)

def receive():
    global lock

    while True:
        packet = rfm9xR.receive(with_header=True, timeout=5)
        lock.acquire()
        if packet is not None:
            packet_hex = packet.hex()
            print("PACKET: ", packet_hex)

            if packet_hex[8:10] == "45": 
                print("WRITE TO TUN")
                tun.write(bytes(packet[4:]))
            elif packet_hex[:2] == "03":
                # if not ip packet, decode:
                payload = ""
                for i in range(0, 252):
                    if packet_hex[i*2:] == "":
                        break
                    if int(packet_hex[i*2:], 16) == 0:
                        break
                    payload += str(format(int(packet_hex[i*2:(i*2)+2], 16), "08b"))
                    
                #print(payload[39], " - ", payload[40:])
                control_packet(payload[39], payload[40:])
        lock.release()

def control_packet(frame_type, data):
    if frame_type == "0":
        print("\nData plane\n")

        print("WRITE: ", bits_to_bytes(data))
        #print("WRITE TO DATABASE: ", bits_to_bytes(data).decode())
        index.commit_line(bits_to_bytes(data).decode())

        # Send back same message to ack:
        print("SENDING BACK: ", bits_to_bytes(data).decode())
        f = frame(1, bits_to_bytes(data).decode())
        f2 = f.createDataFrame()
        transmit_message(f2)
        
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

def control_packet2(frame_type, data):
    if frame_type == "0":
        print("\nData plane")
        print("WRITE TO DATABASE: ", bits_to_bytes(data).decode())
        index.commit_line(bits_to_bytes(data).decode())
        
    elif frame_type == "1":
        print("\nControl plane")
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

    def createControlFrame(self):
        frame = format(self.frame_type, "08b") # frane_type is on index 7 
        data_int = int(self.data)
        data_bit = format(data_int, "032b")
        print("DATA_BIT: ", data_bit)
        frame += data_bit
        return bits_to_bytes(frame)
    
    def createDataFrame(self): 
        frame = format(self.frame_type, "08b")
        data_bits = ''.join(format(ord(i), '08b') for i in self.data)

        for i in range(512 - len(data_bits)): #512
            data_bits += "0"

        frame += data_bits
        return bits_to_bytes(frame)
           
if __name__ == "__main__":
    atexit.register(exit_handler)
    tx_process = Process(target=transmit)
    rx_process = Process(target=receive)

    rx_process.start()
    time.sleep(1)
    tx_process.start()

    tx_process.join()
    rx_process.join()