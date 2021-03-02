from multiprocessing import Process
import time
import board
import busio
import digitalio
import adafruit_rfm9x
import numpy as np

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

def transmit(counterT):
    start_transmit = time.monotonic()
    transmitted = []

    while True:
        # send a broadcast message from my_node with ID = counter
        
        buffer = bytes("startup message nr {} from pi 17 node {} ".format(counterT, rfm9xT.node), "UTF-8")
        sent = rfm9xT.send(buffer)
        transmitted.append(len(buffer))
        counterT = counterT + 1
        if time.monotonic() - start_transmit >= 1:
            total_time = time.monotonic() - start_transmit
            print("1 second has passed! Transmit Bitrate: {}", np.sum(transmitted)*8/total_time)
            start_transmit = time.monotonic()
            transmitted = []

def receive():
    start_receive = time.monotonic()
    received = []
    while True:
        packet = rfm9xR.receive(with_header=True, timeout=5)
        if packet is not None:
            print("Received packet:", packet)
            print("Received (raw payload): {0}".format(packet[4:]))
            print("Received RSSI: {0}".format(rfm9xR.last_rssi))
            received.append(len(packet))
            if time.monotonic() - start_receive >= 1:
                total_time_r = time.monotonic() - start_receive
                print("1 second has passed! Receive Bitrate: {}", np.sum(received)*8/total_time_r)
                start_receive = time.monotonic()
                received = []
           
if __name__ == "__main__":
    tx_process = Process(target=transmit, kwargs={'counterT': counterT})
    rx_process = Process(target=receive)

    rx_process.start()
    time.sleep(1)
    tx_process.start()

    tx_process.join()
    rx_process.join()