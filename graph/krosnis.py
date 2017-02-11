#!/usr/bin/env python3

import sys
import tkinter as tk
from skardas import tkplot
from skardas.skardas import execute_delayed
import threading
from queue import Queue, Empty
import serial
import struct
from collections import namedtuple
import time
import csv
import math


class Status(namedtuple('Status', ['time', 'local_time', 'power', 'setpoint', 'temp_outside', 'temp_inside'])):
    @property
    def temp(self):
        return self.temp_inside - self.temp_outside


START_TIME = time.time()

def local_time():
    return time.time() - START_TIME


class Arduino:
    def __init__(self, filename):
        self.filename = filename
        self.status = Queue()
        self.command = Queue()
        self.thread = threading.Thread(target=self.interact, daemon=True)
        self.started = threading.Event()
        self.last_status = None
        self._power = None
        self._setpoint = None

    def line_status(self, line):
        t_ms, pwm, setpoint, temp_outside, temp_inside = line.strip().split(b',')
        t = float(t_ms) / 1000.0
        p = float(pwm) / 255.0
        temp_outside = float(temp_outside)
        temp_inside = float(temp_inside)
        return Status(t, local_time(), p, setpoint, temp_outside, temp_inside)

    def interact(self):
        with open(self.filename, 'wb') as f:
            self.serial = serial.Serial('/dev/rfcomm0', 115200)
            try:
                self.started.set()
                while True:
                    try:
                        while True:
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
                    self._power = status.power
                    self._setpoint = status.setpoint
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
    def power(self):
        assert(self.started.is_set())
        return self._power

    @power.setter
    def power(self, power):
        assert(self.started.is_set())
        assert(0 <= power <= 1)
        pwm = int(power * 255)
        command = struct.pack('cB', b'P', pwm)
        self.command.put(command)

    @property
    def setpoint(self):
        assert(self.started.is_set())
        return self._setpoint

    @setpoint.setter
    def setpoint(self, setpoint):
        assert(self.started.is_set())
        assert(0 <= setpoint <= 255)
        x = int(setpoint)
        command = struct.pack('cB', b'S', x)
        self.command.put(command)
    def start(self):
        self.thread.start()
        self.started.wait()


class HeatPlot(tkplot.TkPlot):
    def __init__(self, root):
        tkplot.TkPlot.__init__(self, root, (9, 6))

        self.plot = self.figure.add_subplot(111)
        self.plot.set_xlabel("Time (s)")
        self.plot.set_ylabel("Temperature (°C) / heater power (%)")
        self.plot.set_xlim(0, 1)
        self.plot.set_ylim(0, 110)
        self.temp_inside_line, = self.plot.plot([], [], label="Inside temperature")
        self.temp_outside_line, = self.plot.plot([], [], label="Outside temperature")
        self.power_line, = self.plot.plot([], [], label="Power")
        self.setpoint_line, = self.plot.plot([], [], label="Setpoint")
        self.plot.legend(handles=[self.temp_inside_line,
                                  self.temp_outside_line,
                                  self.power_line,
                                  self.setpoint_line], bbox_to_anchor=(0.3, 1))
        self.figure.tight_layout()

    def update(self, status):
        time = [s.local_time for s in status]
        temp_inside = [s.temp_inside for s in status]
        temp_outside = [s.temp_outside for s in status]
        power = [s.power * 100 for s in status]
        setpoint = [s.setpoint for s in status]

        if time:
            self.plot.set_xlim(min(time), max(time))
            self.plot.set_ylim(0, max(110, round(max(temp_inside) / 50.0 + 0.5) * 50 + 10))
            self.temp_inside_line.set_xdata(time)
            self.temp_inside_line.set_ydata(temp_inside)
            self.temp_outside_line.set_xdata(time)
            self.temp_outside_line.set_ydata(temp_outside)
            self.power_line.set_xdata(time)
            self.power_line.set_ydata(power)
            self.setpoint_line.set_xdata(time)
            self.setpoint_line.set_ydata(setpoint)
            self.figure.canvas.draw()


class Krosnis:
    def __init__(self, root, experiment):
        self.root = root
        self.root.title("krosnis - {}".format(experiment))
        self.experiment = experiment

        self.update_period = 1.0

        self.plot = HeatPlot(self.root)
        self.plot.pack(fill=tk.BOTH, expand=1)

        self.toolbar = tk.Frame(self.root)
        self.toolbar.pack(fill=tk.X)
        self.label = tk.Label(self.toolbar)
        self.label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

        self.power_val = tk.StringVar()
        self.power_val.set('0.0')
        self.power = tk.Entry(self.toolbar, textvariable=self.power_val)
        self.power.bind('<Return>', self.set_power)
        self.power.pack(side=tk.LEFT)
        self.power.focus_set()
        self.set_power = tk.Button(self.toolbar, text='Set power', command=self.set_power)
        self.set_power.pack(side=tk.LEFT)

        self.setpoint_val = tk.StringVar()
        self.setpoint_val.set('0.0')
        self.setpoint = tk.Entry(self.toolbar, textvariable=self.setpoint_val)
        self.setpoint.bind('<Return>', self.set_setpoint)
        self.setpoint.pack(side=tk.LEFT)
        self.setpoint.focus_set()
        self.set_setpoint = tk.Button(self.toolbar, text='Set temperature', command=self.set_setpoint)
        self.set_setpoint.pack(side=tk.LEFT)

        self.arduino = Arduino("experiments/{}_raw.csv".format(experiment))
        self.every_status = []
        self.th0 = 0

    def set_status(self, status):
        self.label.config(text=status)

    def set_power(self, event=None):
        self.arduino.power = float(self.power_val.get())

    def set_setpoint(self, event=None):
        self.arduino.setpoint = float(self.setpoint_val.get())

    def start(self):
        _self = self
        def shell():
            self = _self
            import IPython
            IPython.embed()
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
        #def predict(th_max, rc, th0, th_target):
        #    t1 = -rc * math.log((th_target - th_max) / (th0 - th_max))
        #    p_support = th_target / th_max
        #    return t1, p_support

        #th_max = 204
        #rc = 600

        #t1, p_support = predict(th_max, rc, self.th0, 100)

        #if local_time() < t1:
        #    self.arduino.power = 1.0
        #else:
        #    self.arduino.power = p_support
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


def run(experiment):
    root = tk.Tk()
    root.geometry("1000x700")
    win = Krosnis(root, experiment)
    win.start()
    tk.mainloop()

if __name__ == "__main__":
    run(sys.argv[1])
