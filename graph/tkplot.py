import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import tkinter as tk


try:
    from matplotlib.pyplot import style
    style.use('ggplot')
except ImportError:
    pass


class TkPlot(tk.Frame):
    def __init__(self, master, figsize=(9, 6)):
        tk.Frame.__init__(self, master)
        self.figure = Figure(figsize=figsize)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        self.toolbar.update()
