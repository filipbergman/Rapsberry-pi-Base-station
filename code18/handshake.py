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
# Createand configurea TUN interface
tun = TunTap(nic_type="Tun", nic_name="tun0")
tun.config(ip="192.168.2.15", mask="255.255.255.0", gateway="192.168.0.1")

# Set up UDP tunnel
RECEIVER_IP = "192.168.0.170" # Should be receiver's IP on the local network
MY_IP = "192.168.0.193" # Should be this node's IP on the local network
UDP_PORT = 4001

tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rx_sock.bind((MY_IP, UDP_PORT))

def exit_handler():
    tun.close()

def transmit(self, message = None):
    start_transmit = time.monotonic()
    transmitted = []

    while True:
        #buffer = bytes("startup message nr {} from pi 17 node {} ".format(counterT, rfm9xT.node), "UTF-8")
        tx_sock.sendto( buf, (RECEIVER_IP, UDP_PORT))
        transmitted.append(len(buf))
        if time.monotonic() - start_transmit >= 1:
            total_time = time.monotonic() - start_transmit
            print("1 second has passed! Transmit Bitrate: {}", np.sum(transmitted)*8/total_time)
            start_transmit = time.monotonic()
            transmitted = []

def receive(self):
    start_receive = time.monotonic()
    received = []
    while True:
        rcvd, addr = rx_sock.recvfrom(1024)
        if rcvd is not None:
            print("Received (raw header):", [hex(x) for x in rcvd[0:4]])
            #print("Received (raw payload): {0}".format(rcvd[4:]))
            #print("Received RSSI: {0}".format(rfm9xR.last_rssi))
            received.append(len(rcvd))
            if time.monotonic() - start_receive >= 1:
                total_time_r = time.monotonic() - start_receive
                print("1 second has passed! Receive Bitrate: {}", np.sum(received)*8/total_time_r)
                start_receive = time.monotonic()
                received = []

def handshake(self, fragment, data):


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
    atexit.register(exit_handler)
    tx_process = Process(target=transmit)
    rx_process = Process(target=receive)

    rx_process.start()
    time.sleep(1)
    tx_process.start()

    ip = ipaddress.IPv4Address('192.168.2.2')
    f1 = frame(0, ip)
    frame_bits = f1.createFrame()
    transmit(frame_bits)

    tx_process.join()
    rx_process.join()
    tun.close()