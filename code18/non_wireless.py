import socket

RECEIVER_IP = "192.168.0.170" # Should be receiver's IP on the local network
MY_IP = "192.168.0.193" # Should be this node's IP on the local network
UDP_PORT = 4000

# Create sockets
tx_sock = socket.socket(  socket.AF_INET, # Internet
                          socket.SOCK_DGRAM) # UDP

rx_sock = socket.socket(  socket.AF_INET, # Internet
                          socket.SOCK_DGRAM) # UDP
rx_sock.bind((MY_IP, UDP_PORT)) # Bind to local network

tx_sock.sendto( [RAW TUN data], (RECEIVER_IP, UDP_PORT)) # You can send the raw data from the TUN/TAP interface

[RAW TUN data], addr = rx_sock.recvfrom(1024) # Receive data from other end