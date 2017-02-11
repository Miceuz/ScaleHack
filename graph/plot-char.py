from bluepy.btle import *
from binascii import *

import matplotlib.pyplot as plt
import numpy as np

DEVICE_UUID = '00:0B:57:0B:F6:F6'

x = np.arange(100)
y = np.ones(100) * 560

plt.ion()
fig = plt.figure()
ax = fig.add_subplot(111)
h1, = ax.plot(x, y, 'r-')

def updateLine(h1, newData):
	global y
	print newData
#	h1.set_xdata(numpy.append(h1.get_xdata(), newData))
	y = np.append(y, newData)
	y = y[1:]
	h1.set_ydata(y)
	#ax.relim()
	# ax.set_ylim(500, 1000)

	ax.set_ylim(600, 3300)
#	ax.set_ylim(y.mean() - np.std(y) * 5, y.mean() + np.std(y) * 5)
#	ax.set_ylim(y.mean() - y.mean()/2, y.mean() + y.mean()/2)
	ax.autoscale_view()
	fig.canvas.draw()
	fig.canvas.flush_events()
	#plt.draw()

p = Peripheral(DEVICE_UUID)
chars = p.getCharacteristics()

while(True):
	val = chars[5].read()
	ival = int(hexlify(val[1]+val[0]), 16)
	updateLine(h1, ival)

p.disconnect()

#x = np.linspace(0, 6*np.pi, 100)
#y = np.sin(x)
#
## You probably won't need this if you're embedding things in a tkinter plot...
#plt.ion()
#
#fig = plt.figure()
#ax = fig.add_subplot(111)
#line1, = ax.plot(x, y, 'r-') # Returns a tuple of line objects, thus the comma
#
#for phase in np.linspace(0, 10*np.pi, 500):
#    line1.set_ydata(np.sin(x + phase))
#    fig.canvas.draw()#
