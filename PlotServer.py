from matplotlib import pyplot as plt
import numpy as np
import sys
import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)
BUFFER_SIZE = 1024
GRAPHS_WIDTH = 100

windows = {}
ADD_PLOT_CMD = "ADD_PLOT"
DATA_CMD = "DATA"


def update_plot(name, data, timestamp):
    current_line = windows[name].get_axes()[0].get_lines()[0]
    x_data, y_data = current_line.get_xdata(), current_line.get_ydata()
    x_data = np.append(x_data, float(timestamp))
    y_data = np.append(y_data, float(data))
    current_line.set_xdata(x_data)
    current_line.set_ydata(y_data)

    points_count = len(x_data)
    if points_count > GRAPHS_WIDTH:
        x_data = np.delete(x_data, 0)
        y_data = np.delete(y_data, 0)
        # windows[0].get_axes()[0].clear()
        current_line.set_xdata(x_data)
        current_line.set_ydata(y_data)
        # windows[0].get_axes()[0].plot(x_data, y_data, 'b')
        # points_count -= 1
    windows[0].get_axes()[0].plot(x_data, y_data, 'b')
    plt.pause(0.001)


def process_msg(conn):
    """This function receive and parse data"""
    data = str(conn.recv(BUFFER_SIZE))[2:-1]
    msgs = data.split("\\n")[:-1]
    # print = msgs
    for msg in msgs:
        commands = msg.split()
        if commands[0] == ADD_PLOT_CMD:
            add_new_plot(commands[1])
        elif commands[0] == DATA_CMD:
            update_plot(commands[1], commands[2], commands[3])


def start_diagrams(conn):
    """This function start diagrams"""
    while True:
        process_msg(conn)
        # points = np.append(points, float(1))
        # windows[0].get_axes()[0].plot(points, 'b')
        # points_count += 1


def add_new_plot(name):
    """Add a subplot to figure for visualization"""
    fig, ax = plt.subplots()
    windows[name] = fig
    windows[name].get_axes()[0].plot([], 'b')


def start_server(ip, port):
    """Function creating socket and starting to listen"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip, port))
    s.listen()
    print(f"Start listening: {ip}:{port}")
    conn, addr = s.accept()
    print('Connected by', addr)
    start_diagrams(conn)


if __name__ == "__main__":
    # start_server(sys.argv[1], int(sys.argv[2]))
    start_server(HOST, PORT)


