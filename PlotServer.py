from matplotlib import pyplot as plt
import numpy as np
import math
import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)


def get_data(conn):
    """This function receive and parse data"""
    return conn.recv(1024)


def start_diagrams(conn):
    """This function start diagrams"""
    points = np.array([])
    points_count = 0
    fig, ax = plt.subplots()
    while True:
        # data = get_data(conn)
        points = np.append(points, math.sin(0.1) + np.random.normal(0, 1))
        ax.plot(points)
        if points_count > 100:
            points = np.delete(points, 1)
            ax.clear()
            ax.plot(points)
            points_count -= 1
        plt.pause(0.001)
        points_count += 1


def add_new_plot(name):
    """Add a subplot to figure for visualization"""
    pass


def start_server(ip, port):
    """Function creating socket and starting to listen"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip, port))
    print(f"Start listening: {ip}:{port}")
    s.listen()
    conn, addr = s.accept()
    print('Connected by', addr)
    start_diagrams(conn)


if __name__ == "__main__":
    start_server(HOST, PORT)


