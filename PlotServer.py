from matplotlib import pyplot as plt
import numpy as np
import sys, time
import socket

HOST = '0.0.0.0'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)
BUFFER_SIZE = 4096
GRAPHS_WIDTH = 30

windows = {}
ADD_PLOT_CMD = "ADD_PLOT"
DATA_CMD = "DATA"


def update_plot(name, data, timestamp):
    """Add received data to plot"""
    timestamp = float(timestamp)
    data = float(data)
    current_axes = windows[name].get_axes()[0]
    current_line = current_axes.get_lines()[0]
    x_data, y_data = current_line.get_xdata(), current_line.get_ydata()
    x_data = np.append(x_data, timestamp)
    y_data = np.append(y_data, data)
    current_axes.plot(x_data, y_data, 'b')
    current_line.set_xdata(x_data)
    current_line.set_ydata(y_data)
    current_axes.relim()
    current_axes.autoscale_view()

    points_count = len(x_data)
    if points_count > GRAPHS_WIDTH:
        x_data = np.delete(x_data, 0)
        y_data = np.delete(y_data, 0)
        for line in current_axes.get_lines():
            line.remove()
        current_axes.plot(x_data, y_data, 'b')
    plt.pause(1e-6)


def process_msg(conn):
    """This function receive and parse data"""
    data = str(conn.recv(BUFFER_SIZE))[2:-1]
    msgs = data.split("\\n")[:-1]
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


def add_new_plot(name):
    """Add a subplot to figure for visualization"""
    fig = plt.figure()
    fig.suptitle(name, fontsize=16)
    ax = plt.axes()
    fig.add_axes(ax)
    ax.grid(color='k', linestyle='-', linewidth=0.2)
    ax.set_alpha(1)
    ax.set_xlabel("time (s)")
    windows[name] = fig
    ax.set_autoscale_on(True)
    ax.plot([], 'b')


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
    start_server(HOST, PORT)


