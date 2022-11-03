import threading
from tkinter import messagebox
from tkinter.font import BOLD
import ttkbootstrap as ttk
import supertk as stk
import time
from aplayer import Aplayer
from audiodl import AudioDL
from mastertools import Shield
from tkinter import *
from lang import rellipsis
from config import light_wait, COLOUR_DICT, DEFAULT_FONT_FAMILY

ENTRY_BG = '#17012e'


class SecondPane:

    def __init__(self):
        self.frame = Frame(Shield.root, width=Shield.max_pane())
        self.queue_frame = ttk.Frame(
            self.frame, padding='{0} 0 {0} 0'.format(Shield.edge_pad()))
        self.queue_frame.columnconfigure(0, weight=0)
        self.entry_bar = self.__gen_entry_bar()
        self.queue_box = self.__gen_queue_box()
        self.queue_tools = self.__gen_queue_tools()
        self.subheader = self.__gen_sub_header()
        self.saving = False

    def drawAll(self):
        self.frame.grid(column=0, row=1, sticky='nsw', columnspan=1)
        self.__draw_queue_frame()
        self.entry_bar.focus_entry()

    def undrawAll(self):
        self.frame.grid_remove()

    def __gen_queue_box(self):
        queue_box = stk.QueueListbox(self.queue_frame)
        queue_box.configure(background=COLOUR_DICT['dark'])
        queue_box.grid(column=0, row=4)
        return queue_box

    def __gen_entry_bar(self):
        text = 'search'
        entry_bar = stk.EntryBar(
            self.queue_frame, self.search_hit,
            [text], entry_placeholder=rellipsis(text),
            pady=Shield.edge_pad())
        entry_bar.set_entry_bg(ENTRY_BG)
        entry_bar.add_button('save', self.save_playlist)
        entry_bar.grid(column=0, row=3, sticky=W)
        return entry_bar

    def __gen_queue_tools(self):
        queue_tools = Frame(self.queue_frame)
        clear_playlist_button = stk.DarkLabelButton(
            queue_tools, self.queue_box.playlist_clear,
            text='[clear queue]')
        clear_selection_button = stk.DarkLabelButton(
            queue_tools, self.queue_box.unselect_all,
            text='[clear selection]')
        remove_selection_button = stk.DarkLabelButton(
            queue_tools, self.queue_box.playlist_remove_selection,
            text='[remove selection]')
        clear_playlist_button.grid(column=0, row=0)
        clear_selection_button.grid(column=1, row=0)
        remove_selection_button.grid(column=2, row=0)
        queue_tools.grid(row=1, sticky=W)
        return queue_tools

    def __gen_sub_header(self):
        subheader = ttk.Label(
            self.queue_frame, font=(DEFAULT_FONT_FAMILY, 19, BOLD))
        subheader.grid(column=0, row=0)
        Aplayer.observe_playlist_title(self.update_subheader)
        return subheader

    def update_subheader(self, _, _2):
        self.subheader.configure(
            text='Currently playing: {}'.format(Aplayer.playlist_title()))

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
        for _ in range(3):
            new_text += '.'
            self.entry_bar.show_side_label(new_text)
            time.sleep(0.5)
        while self.saving is True:
            time.sleep(1)
        self.entry_bar.hide_side_label(old_text)

    def save_playlist(self, e: Event = None):
        if self.saving is True:
            return
        dest_title = AudioDL.validate_title(self.entry_bar.get())
        if dest_title is None:
            return
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
                msg += '\n{} [{}]'.format(
                    self.queue_box.get(i, i)[0], filename)
            messagebox.showinfo(
                'Files unable to be added to {}'.format(dest_title), msg)
        light_wait()
        self.saving = False
