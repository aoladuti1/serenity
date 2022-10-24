import threading
import ttkbootstrap as ttk
import tkintools
import time
from aplayer import Aplayer
from mastertools import Shield
from tkinter import *
from config import rellipsis, COLOUR_DICT

ENTRY_BG = '#17012e'

class SecondPane:

    def __init__(self, root: ttk.Window):
        self.root = root
        self.frame = Frame(self.root, width=Shield.max_pane()) 
        self.queue_frame = ttk.Frame(
            self.frame, padding='{0} 0 {0} 0'.format(Shield.edge_pad()))
        self.entry_bar = self.__gen_entry_bar()
        self.queue_box = self.__gen_queue_box()
        

    def drawAll(self):
        self.frame.grid(column=0, row=1, sticky='nsw', columnspan=1)
        self.__draw_queue_frame()
        self.entry_bar.focus_entry()

    def __gen_queue_box(self):  
        queue_box = tkintools.QueueListbox(self.queue_frame, self.root)
        queue_box.configure(background=COLOUR_DICT['dark'])
        queue_box.grid(column=0, row=4)
        return queue_box

    def __gen_entry_bar(self):
        text = 'search'
        entry_bar = tkintools.EntryBar(
            self.queue_frame, self.root, self.search_hit,
            [text], entry_placeholder=rellipsis(text),
            pady=Shield.edge_pad())
        entry_bar.set_entry_bg(ENTRY_BG)
        entry_bar.grid(column=0, row=3, sticky=W)
        return entry_bar

    def __draw_queue_frame(self):
        self.queue_frame.grid(column=0)
    
    def search_hit(self, e: Event = None):
        query = self.entry_bar.get()
        items = self.queue_box.get(0, END)
        index = -1
        for i, song in enumerate(items):
            if query.casefold() in song.casefold():
                index = i
                break
        if index != -1:
            self.queue_box.see(index)
            threading.Thread(
                target=self.__highlight_short, args=(index,)).start()

    def undrawAll(self):
        self.frame.grid_remove()
        
    def __highlight_short(self, index):
        self.queue_box.itemconfig(index, {'fg': '#FFD700'})
        time.sleep(2)
        if not Aplayer.get_playlist_pos() == index:
            revert_colour = self.queue_box['foreground']
        else:
            revert_colour = self.queue_box.current_song_fg
        self.queue_box.itemconfig(index, {'fg': revert_colour})
        