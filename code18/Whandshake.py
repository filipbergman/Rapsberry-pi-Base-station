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

iface= 'tun0'
tun = TunTap(nic_type="Tun", nic_name="tun0")
tun.config(ip="192.168.2.15", mask="255.255.255.0", gateway="192.168.0.1")


this_ip = ipaddress.IPv4Address('192.168.2.15')
this_ip_bits = format(int(this_ip), "032b")

base1 = ipaddress.IPv4Address('192.168.2.16')
base1_bits = format(int(base1), "032b")

test1 = ipaddress.IPv4Address('192.168.2.2')
test1_bits = format(int(test1), "032b")

ipList = []
ipList.append(this_ip_bits)
ipList.append(base1_bits)
ipList.append(test1_bits)


def exit_handler():
    tun.close()

def transmit_message(message):
    #tx_sock.sendto(message, (RECEIVER_IP, UDP_PORT))
    rfm9xT.send(message)

def transmit():
    while True:
        buf= tun.read(1024)
        print("TUN BUFFER: ", buf)
        #buffer = bytes("startup message nr {} from pi 17 node {} ".format(counterT, rfm9xT.node), "UTF-8")
        #tx_sock.sendto( buf, (RECEIVER_IP, UDP_PORT))
        rfm9xT.send(buf)

def receive():
    while True:
        #rcvd, addr = rx_sock.recvfrom(1024)
        packet = rfm9xR.receive(with_header=True, timeout=5)
        print("Received: ", packet)

        if packet is not None:
            # If ipv4 packet, write to tun interface:
            
            packet_hex = packet.hex()
            print("hex: ", packet_hex)
            if packet_hex[:2] != "03": 
                print("WRITE TO TUN")
                tun.write(packet)
            elif packet_hex[:2] == "03":
                # if not ip packet, decode:
                packet = packet.decode()
                handshake(packet[4], packet[5:])
                

def handshake(frame_type, data):
    print("FRAME TYPE: ", frame_type)
    print("data: ", data)

    if frame_type == "0":
        print("\nData plane\n")
    elif frame_type == "1":
        print("\nControl plane\n")
        if data not in ipList:
            print("UNIQUE IP")
            f = frame(frame_type, data)
            f2 = f.frame_from_bits()
            transmit_message(f2)
        elif data in ipList:
            print("IP ALREADY EXISTS")



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
        frame += data_bit
        return frame.encode()

    def frame_from_bits(self):
        frame = self.frame_type
        frame += self.data
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