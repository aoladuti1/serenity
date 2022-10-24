30
import ttkbootstrap as ttk
import tkintools
from aplayer import Aplayer
from mastertools import Shield
from tkinter import *

class SecondPane:

    def __init__(self, root: ttk.Window):
        self.root = root
        self.frame = Frame(self.root, width=Shield.max_pane()) 
        self.queue_frame = self.gen_queue_frame()

    def drawAll(self):
        self.frame.grid(column=0, row=1, sticky='nsw', columnspan=1)
        self.draw_queue_frame()

    def gen_queue_frame(self):
        queue_frame = ttk.Frame(self.frame) 
        queue_frame.configure(padding='{} 0 0 0'.format(Shield.edge_pad()))
        queue_box = tkintools.QueueListbox(queue_frame, self.root)
        queue_box.grid(column=0, row=4)
        return queue_frame

    def draw_queue_frame(self):
        self.queue_frame.grid(column=1)

    def undrawAll(self):
        self.frame.grid_remove()
    