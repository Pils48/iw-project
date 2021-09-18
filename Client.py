import numpy as np
import socket
import time

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

bytes_counter = 0
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(bytes("ADD_PLOT TEMPERATURE\n", 'utf-8'))
    initial_timestamp = time.time()
    for i in range(1, 10000):
        time.sleep(1e-5)
        s.sendall(bytes(f"DATA TEMPERATURE {np.random.normal(0, 1)} {(time.time() - initial_timestamp) * 1e3}\n", 'utf-8'))
