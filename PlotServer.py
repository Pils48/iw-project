from matplotlib import pyplot as plt
import numpy as np
import datetime
import sys, time
import socket

HOST = '0.0.0.0'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to liste00n on (non-privileged ports are > 1023)
BUFFER_SIZE = 4096
GRAPHS_WIDTH = 300

axes = {}
ADD_PLOT_CMD = "ADD_PLOT"
DATA_CMD = "DATA"

# dump_file = open(f"{datetime.datetime.now()}_data.txt", 'w')
dump_file = open(f"logs/{datetime.datetime.today().strftime('%Y-%m-%d-%H_%M_%S')}_data.txt", 'a')

fig = plt.figure("Control system monitor")
plot_count = 0


def update_plot(name, data, timestamp):
    """Add received data to plot"""
    global fig
    timestamp = float(timestamp)
    data = float(data)
    current_axes = axes[name]
    x_data, y_data = [], []
    if len(current_axes.get_lines()) != 0:
        current_line = current_axes.get_lines()[0]
        x_data, y_data = current_line.get_xdata(), current_line.get_ydata()
        x_data = np.append(x_data, timestamp)
        y_data = np.append(y_data, data)
    # current_axes.plot(x_data, y_data, 'b')
        current_line.set_xdata(x_data)
        current_line.set_ydata(y_data)
    else:
        x_data = np.append(x_data, timestamp)
        y_data = np.append(y_data, data)
        current_axes.plot(x_data, y_data, 'b')
    current_axes.relim()
    # current_axes.autoscale_view()

    # points_count = len(x_data)
    # if points_count > GRAPHS_WIDTH:
    #     x_data = np.delete(x_data, 0)
    #     y_data = np.delete(y_data, 0)
    #     for line in current_axes.get_lines():
    #         line.remove()
    #     current_line.set_xdata(x_data)
    #     current_line.set_ydata(y_data)
    #     current_axes.add_line(current_line)
        # current_axes.set_xlim(x_data[0] - 1, x_data[len(x_data) - 1] + 1)
    plt.pause(1e-12)


def process_msg(conn):
    """This function receive and parse data"""
    data = str(conn.recv(BUFFER_SIZE))[2:-1]
    msgs = data.split("\\n")[:-1]
    for msg in msgs:
        commands = msg.split()
        if commands[0] == ADD_PLOT_CMD:
            add_new_plot(commands[1], commands[2], commands[3], commands[4])
        elif commands[0] == DATA_CMD:
            # dump_file.write(msg + "\n")
            # dump_file.flush()
            update_plot(commands[1], commands[2], commands[3])


def start_diagrams(conn):
    """This function start diagrams"""
    while True:
        process_msg(conn)


def add_new_plot(name, lower_bound, upper_bound, xticks_number):
    """Add a subplot to figure for visualization"""
    global plot_count, fig
    lower_bound = int(lower_bound)
    upper_bound = int(upper_bound)
    plot_count += 1
    fig.add_subplot(2, 2, plot_count)
    ax = fig.axes[plot_count - 1]
    ax.set_alpha(1)
    ax.set_xlabel("time (s)")
    ax.set_xlim(0, GRAPHS_WIDTH)
    ax.set_yticks(np.linspace(lower_bound, upper_bound, int(xticks_number)))
    ax.grid(color='k', linestyle='-', linewidth=0.2)
    ax.set_ylim(lower_bound, upper_bound)
    ax.set_ylabel(name)
    # windows[name] = fig
    # ax.set_autoscale_on(False)
    # ax.plot([], 'b')
    axes[name] = ax


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
    try:
        start_server(HOST, PORT)
    except KeyboardInterrupt:
        print('Interrupted')
        dump_file.close()

