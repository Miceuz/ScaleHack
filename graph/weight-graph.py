#!/usr/bin/env python3

import sys
import tkinter as tk
import tkplot
import threading
from queue import Queue, Empty
import serial
import struct
from collections import namedtuple
import time
import csv
import math

def execute_delayed(root, generator):
    """For each yielded value wait the given amount of time (in seconds)
    without pausing the Tkinter main loop.

    See 'slowmotion' in http://effbot.org/zone/tkinter-generator-polyline.htm
    """
    try:
        root.after(int(next(generator) * 1000), execute_delayed, root, generator)
    except StopIteration:
        pass


class Status(namedtuple('Status', ['local_time', 'weight_reading'])):
    @property
    def temp(self):
        return self.weight_reading


START_TIME = time.time()

def local_time():
    return time.time() - START_TIME


class Arduino:
    def __init__(self, port, filename):
        self.filename = filename
        self.port = port
        self.status = Queue()
        self.command = Queue()
        self.thread = threading.Thread(target=self.interact, daemon=True)
        self.started = threading.Event()
        self.last_status = None
        self._power = None

    def line_status(self, line):
        weight_reading = float(line.strip())
        return Status(local_time(), weight_reading)

    def interact(self):
        with open(self.filename, 'wb') as f:
            self.serial = serial.Serial(self.port, 9600)
            try:
                self.started.set()
                while True:
                    try:
                        while True:
                            None
                            self.serial.write(self.command.get_nowait())
                    except Empty:
                        pass

                    line = self.serial.readline()
                    try:
                        status = self.line_status(line)
                    except ValueError:
                        continue
                    f.write(line)
                    f.flush()
                    self.status.put_nowait(status)
                    self.last_status = status
            finally:
                self.started.clear()

    def iter_status(self):
        assert(self.started.is_set())
        try:
            while True:
                status = self.status.get_nowait()
                yield status
        except Empty:
            pass

    def __str__(self):
        return "<{} {}>".format(self.__class__.__name__, self.last_status if self.started.is_set() else '(stopped)')


    @property
    def calibrationWeight(self):
        assert(self.started.is_set())
        return self._power

    @calibrationWeight.setter
    def calibrationWeight(self, calibrationWeight):
        assert(self.started.is_set())
        assert(0 <= calibrationWeight <= 2**24)
        command = struct.pack('4sc', str.encode(str(int(calibrationWeight))), b'\n')        
        self.command.put(command)

    def start(self):
        self.thread.start()
        self.started.wait()


class HeatPlot(tkplot.TkPlot):
    def __init__(self, root):
        tkplot.TkPlot.__init__(self, root, (9, 6))

        self.plot = self.figure.add_subplot(111)
        self.plot.set_xlabel("Time (s)")
        self.plot.set_ylabel("Weight (g)")
        self.plot.set_xlim(0, 1)
        self.plot.set_ylim(0, 110)
        self.weight_reading_line, = self.plot.plot([], [], label="Weight, g")
        self.plot.legend(handles=[self.weight_reading_line], bbox_to_anchor=(0.3, 1))
        self.figure.tight_layout()

    def update(self, status):
        time = [s.local_time for s in status]
        weight_reading = [s.weight_reading for s in status]

        if time:
            self.plot.set_xlim(min(time), max(time))
            self.plot.set_ylim(0, max(110, round(max(weight_reading) / 50.0 + 0.5) * 50 + 10))
            self.weight_reading_line.set_xdata(time)
            self.weight_reading_line.set_ydata(weight_reading)
            self.figure.canvas.draw()


class Krosnis:
    def __init__(self, root, port, experiment):
        self.root = root
        self.root.title("Scales - {}".format(experiment))
        self.experiment = experiment

        self.update_period = 1.0

        self.plot = HeatPlot(self.root)
        self.plot.pack(fill=tk.BOTH, expand=1)

        self.toolbar = tk.Frame(self.root)
        self.toolbar.pack(fill=tk.X)
        self.label = tk.Label(self.toolbar)
        self.label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

        self.power_val = tk.StringVar()
        self.power_val.set('0')
        self.power = tk.Entry(self.toolbar, textvariable=self.power_val)
        self.power.bind('<Return>', self.set_calibrationWeight)
        self.power.pack(side=tk.LEFT)
        self.power.focus_set()
        self.set_power = tk.Button(self.toolbar, text='Set weight', command=self.set_calibrationWeight)
        self.set_power.pack(side=tk.LEFT)

#        self.setpoint_val = tk.StringVar()
#        self.setpoint_val.set('0.0')
#        self.setpoint = tk.Entry(self.toolbar, textvariable=self.setpoint_val)
#        self.setpoint.bind('<Return>', self.set_setpoint)
#        self.setpoint.pack(side=tk.LEFT)
#        self.setpoint.focus_set()
#        self.set_setpoint = tk.Button(self.toolbar, text='Set temperature', command=self.set_setpoint)
#        self.set_setpoint.pack(side=tk.LEFT)

        self.arduino = Arduino(port, "experiments/{}_raw.csv".format(experiment))
        self.every_status = []
        self.th0 = 0

    def set_status(self, status):
        self.label.config(text=status)

    def set_calibrationWeight(self, event=None):
        self.arduino.calibrationWeight = float(self.power_val.get())

    # def set_setpoint(self, event=None):
    #     self.arduino.setpoint = float(self.setpoint_val.get())

    def start(self):
        _self = self
        def shell():
            self = _self
        threading.Thread(target=shell, daemon=True).start()
        execute_delayed(self.root, self.sample())

    def time_deviation(self):
        if self.every_status:
            t0 = self.every_status[0].time
            t0_local = self.every_status[0].local_time
            t_sum = 0
            for s in self.every_status:
                t_sum += (s.time - t0) - (s.local_time - t0_local)
            return t_sum / len(self.every_status)
        else:
            return 0

    def control(self):
        pass

    def sample(self):
        self.arduino.start()
        with open("experiments/{}.csv".format(self.experiment), 'w') as f:
            csvf = csv.writer(f)
            csvf.writerow(Status._fields)
            while True:
                try:
                    for s in self.arduino.iter_status():
                        if self.th0 is None:
                            self.th0 = s.temp
                        csvf.writerow(s)
                        self.set_status(str(s))
                        self.every_status.append(s)
                    f.flush()
                    self.plot.update(self.every_status)
                    self.control()
                    yield self.update_period
                except Exception as e:
                    print(e)


def run(port, experiment):
    root = tk.Tk()
    root.geometry("1000x700")
    win = Krosnis(root, port, experiment)
    win.start()
    tk.mainloop()

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
