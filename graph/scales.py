import serial
import matplotlib.pyplot as plt
import numpy as np
import sys, select

ser = serial.Serial('/dev/rfcomm0', 9600)

x = np.arange(100)
y = np.ones(100)*0

plt.ion()
fig = plt.figure()
ax = fig.add_subplot(111)
h1, = ax.plot(x, y, 'r-')


def updateLine(h1, newData):
	global y
	print(newData)
#	h1.set_xdata(numpy.append(h1.get_xdata(), newData))
	y = np.append(y, newData)
	y = y[1:]
	h1.set_ydata(y)
	#ax.relim()
	ax.set_ylim(np.amin(y), np.amax(y))

	#~ ax.set_ylim(-10, 10000)
#	ax.set_ylim(y.mean() - np.std(y) * 5, y.mean() + np.std(y) * 5)
#	ax.set_ylim(y.mean() - y.mean()/2, y.mean() + y.mean()/2)
	ax.autoscale_view()
	fig.canvas.draw()
	fig.canvas.flush_events()
	plt.draw()
	
def GetChar(Block=True):
  if Block or select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
    return sys.stdin.read(1)
  #~ raise error('NoChar')
	
while(True):
	val = ser.readline()
	ival =  np.float(val.decode("utf-8").strip()) 
	#~ print(ival)
	updateLine(h1, ival)
	if "n" == GetChar(False):
		break

#~ print(type(y[0]))		
#~ print(np.amax(y))

ser.close()
