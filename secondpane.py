import threading
from tkinter import messagebox
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
        self.queue_frame.columnconfigure(0, weight = 0)
        self.entry_bar = self.__gen_entry_bar()
        self.queue_box = self.__gen_queue_box()
        self.saving = False

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
        entry_bar.add_button('save', self.save_playlist)
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
        

    def __dotdraw_side_label(self, text):
        old_text = self.entry_bar.get_side_label_text()
        new_text = text
        for i in range(3):
            new_text += '.'
            self.entry_bar.show_side_label(new_text)
            time.sleep(0.5)
        while self.saving is True:
            time.sleep(1)
        self.entry_bar.hide_side_label(old_text)
    
    def save_playlist(self, e: Event = None):
        if self.saving is True:
            return
        dest_title = Aplayer._validate_title(self.entry_bar.get())
        temp_text = '{} {}'.format('saving to', dest_title)
        self.saving = True
        threading.Thread(
            target=self.__dotdraw_side_label, args=(temp_text,)).start()
        rejects = Aplayer.savelist(dest_title)
        if rejects:
            msg = """
            The following titles could not be added to '{}'
            (titles may be wrong) likely because streams are not permitted
            in saved playlists:
            """.format(dest_title)
            for i, filename in rejects:
                msg += '\n{} [{}]'.format(self.queue_box.get(i,i)[0], filename)
            messagebox.showinfo(
                'Files unable to be added to {}'.format(dest_title), msg)
        Aplayer._mpv_wait()
        self.saving = False

        