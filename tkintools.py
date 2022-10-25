from math import ceil
import threading
import time
from tkinter import *
from tkinter.font import BOLD
import ttkbootstrap as ttk
from aplayer import Aplayer
from typing import Callable, Any
from config import *


class TypedLabel(ttk.Label):
    def __init__(self, master, label_type: str, data: str, **kw):
        self.label_type = label_type
        self.data = data
        ttk.Label.__init__(self, master, **kw)


class LabelButton(Label):

    def default_on_enter(self, e):
        self['background'] = self.activeBG
        self['foreground'] = self.activeFG

    def default_on_leave(self, e):
        self['background'] = self.defaultBG
        self['foreground'] = self.defaultFG

    def on_click(self, e: Event = None):
        self['background'] = self.clickBG
        self['foreground'] = self.clickFG
        if e is None:
            if self.clickFunc is not None:
                self.clickFunc()
        else:
            if self.clickFunc is not None:
                self.clickFunc(e)

    def __init__(
        self, master, clickFunc: Callable = None,
        onClickFunc: Callable = None,
        activeBG=ACTIVE_BUTTON_BG_HEX,
        activeFG=COLOUR_DICT['info'],
        clickBG=CLICK_BUTTON_BG_HEX,
        clickFG=COLOUR_DICT['bg'],
        defaultBG=COLOUR_DICT['bg'],
        defaultFG=COLOUR_DICT['primary'],
        onEnterFunc=None,
        onLeaveFunc=None,
        unclickFunc=None,
        **kw
    ):
        # onClickFunc totally overrides clickFunc
        # arguments which start with "on" require an event to be passed to them
        # usually achieved with lambda e: functionName
        Label.__init__(self, master=master, **kw)
        self.onClickFunc = onClickFunc
        self.clickFunc = clickFunc
        self.defaultBG = defaultBG
        self.defaultFG = defaultFG
        self.activeBG = activeBG
        self.activeFG = activeFG
        self.clickBG = clickBG
        self.clickFG = clickFG
        self.onEnterFunc = onEnterFunc
        self.onLeaveFunc = onLeaveFunc
        self.unclickFunc = unclickFunc
        self.state = 0
        self.configure(cursor='hand2')
        if onClickFunc is None:
            self.onClickFunc = self.on_click
        if defaultBG is None:
            self.defaultBG = self['background']
        if defaultFG is None:
            self.defaultFG = self['foreground']
        if onEnterFunc is None:
            self.onEnterFunc = self.default_on_enter
        if onLeaveFunc is None:
            self.onLeaveFunc = self.default_on_leave
        if unclickFunc is None:
            self.unclickFunc = self.onLeaveFunc
        self['background'] = defaultBG
        self['foreground'] = defaultFG
        self.bind("<Enter>", self.onEnterFunc)
        self.bind("<Leave>", self.onLeaveFunc)
        self.bind("<Button-1>", self.onClickFunc)
        self.bind("<ButtonRelease-1>", self.unclickFunc)


class StatusBar(Frame):
    def __init__(self, master, **kw):
        from mastertools import Shield
        Frame.__init__(self, master, **kw)
        self.configure(width=Shield.base_pane_width())
        self.columnconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)
        self.label = ttk.Label(
            self, font=(DEFAULT_FONT_FAMILY, 12), padding='4 4 0 4',
            background=COLOUR_DICT['dark'])
        self.time = ttk.Label(
            self, font=(DEFAULT_FONT_FAMILY, 12), padding='0 4 4 4',
            background=COLOUR_DICT['dark'])


class SeekBar(Frame):
    def __init__(self, master, **kw):
        from mastertools import Shield
        Frame.__init__(self, master, **kw)
        self.columnconfigure((1, 2, 3, 4, 5, 6, 7, 8, 9, 10), weight=1)
        self.sliding = False
        self.pos = ttk.Label(
            self, font=(DEFAULT_FONT_FAMILY, 12), padding='0 0 10 0')
        self.pos.pack(side=LEFT)
        self.new_position = DoubleVar()
        self.slider = ttk.Scale(
            self, from_=0, to_=100, orient=HORIZONTAL,
            variable=self.new_position,
            command=self.seek_percent,
            length=int(Shield.base_pane_width() * 6/10))
        self.slider.bind('<Button-1>', self.set_value)
        self.slider.pack(side=LEFT, expand=True, fill=X, anchor=CENTER)
        self.duration = ttk.Label(
            self, font=(DEFAULT_FONT_FAMILY, 12), padding='10 0 0 0')
        self.duration.pack(side=LEFT)

    def unset_sliding(self, secs):
        time.sleep(secs)
        self.sliding = False

    def set_value(self, e: Event):
        self.slider.event_generate('<Button-3>', x=e.x, y=e.y)
        return 'break'

    def seek_percent(self, p: float):
        if self.sliding is True:
            return
        self.sliding = True
        percent = ceil(float(p))
        Aplayer.seek_percent(percent)
        secs = 0.15
        if percent == 100:
            secs = 1
        threading.Thread(
            target=self.unset_sliding, args=(secs,)).start()


class DarkLabelButton(LabelButton):
    def __init__(self, master, clickFunc=None,
                defaultFG = COLOUR_DICT['primary'], **kw):
        LabelButton.__init__(
            self, master=master,
            unclickFunc=clickFunc,
            defaultFG=defaultFG,
            activeFG=COLOUR_DICT['info'],
            activeBG=COLOUR_DICT['bg'],
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['bg'], **kw)


class QueueListbox(Listbox):
    """ A tk listbox with drag'n'drop reordering of entries. """

    def __init__(self, master, root, set_fg = COLOUR_DICT['light'], 
                 current_song_fg = COLOUR_DICT['primary'], **kw):
        from mastertools import Shield
        Listbox.__init__(self, master, **kw)
        kw['selectmode'] = MULTIPLE
        kw['foreground'] = set_fg
        self.config(selectforeground=COLOUR_DICT['info'])
        self.root = root
        self.cur_index = None
        self.cur_state = None
        self.current_song_fg = current_song_fg
        self.__last_playing_pos = -1
        self.config(foreground=set_fg)
        self.bind('<Button-1>', self.get_state, add='+')
        self.bind('<Button-1>', self.set_current, add='+')
        self.bind('<B1-Motion>', self.shift_selection)
        self.bind('<ButtonRelease-1>', self.moved_item)
        self.bind('<Double-Button-1>',
                  lambda e: Aplayer.player.playlist_play_index(self.cur_index))
        self.config(width=50, height=int(Shield.drawn_height / 55),
                    background=COLOUR_DICT['bg'])
        Aplayer.observe_playlist_changes(self.refresh_queue)
        Aplayer.observe_playlist_pos(self.update)

    def moved_item(self, e: Event = None):
        if self.cur_index != self.last_cur_index:
            Aplayer.playlist_move(self.last_cur_index, self.cur_index, True)

    def set_current(self, event):
        ''' gets the current index of the clicked item in the listbox '''
        self.cur_index = self.nearest(event.y)
        self.last_cur_index = self.cur_index

    def get_state(self, event):
        ''' checks if the clicked item in listbox is selected '''
        self.cur_state = 1

    def shift_selection(self, event):
        ''' shifts item up or down in listbox '''
        i = self.nearest(event.y)
        if self.cur_state == 1:
            self.selection_set(self.cur_index)
        else:
            self.selection_clear(self.cur_index)
        if i < self.cur_index:
            # Moves up
            x = self.get(i)
            selected = self.selection_includes(i)
            self.delete(i)
            self.insert(i+1, x)
            if selected:
                self.selection_set(i+1)
            self.cur_index = i
        elif i > self.cur_index:
            # Moves down
            x = self.get(i)
            selected = self.selection_includes(i)
            self.delete(i)
            self.insert(i-1, x)
            if selected:
                self.selection_set(i-1)
            self.cur_index = i

    def update(self, _, playlist_pos):
        Aplayer._mpv_wait()
        pos = Aplayer.get_playlist_pos()
        size = self.size()
        if ((pos is None or pos < 0
            or pos > size - 1
            or self.__last_playing_pos > size - 1)):
                return
        valid_pos = pos if pos < size else size - 1
        if self.__last_playing_pos != -1:
            self.itemconfig(self.__last_playing_pos, {'fg': self['foreground']})
        else:
            self.itemconfig(self.size() - 1, {'fg': self['foreground']})
        self.itemconfig(valid_pos, {'fg': COLOUR_DICT['primary']})
        self.__last_playing_pos = valid_pos

    def refresh_queue(self, _, count):
        if count == 1:
            self.update(None, 0)
        self.delete(0, END)
        if count > 0:
            for path in Aplayer.playlist_filenames():
                self.insert(END, Aplayer.get_title_from_file(path))
        self.update(None, self.__last_playing_pos)
        self.root.update()

class EntryBar(Frame):

    def __init__(self, master, root, main_func, states: list[str],
                 main_alterable=True, entry_placeholder='', smartxpad=6, **kw):
        Frame.__init__(self, master, **kw)
        self.root = root
        self.state = 0
        self.states = states
        self.__padx = smartxpad
        self.button_frames = []
        main_button_widgets = self.add_button(
            self.states[0], main_func, alterable=main_alterable)
        self.main_button_frame = main_button_widgets[0]
        self.main_button = main_button_widgets[1]
        self.side_label = ttk.Label(self, font=(DEFAULT_FONT_FAMILY, 12))
        self.entry = Entry(self, width=27)
        self.entry.grid(row=0, column=0, padx=(0,smartxpad))
        self.entry.configure(
            font=(DEFAULT_FONT_FAMILY, 13),
            background=COLOUR_DICT['dark'],
            selectbackground=COLOUR_DICT['selectbg'])
        self.entry.bind('<Return>', self.click_sim)
        self.entry.insert(0, entry_placeholder)

    def __grid_new_button(self, button_frame):
        i = len(self.button_frames)
        if i == 0:
            button_frame.grid(row=0, column=i, sticky=S)
        else:
            button_frame.grid(row=0, column=i, sticky=S, padx=self.__padx)

    def add_button(self, text, clickFunc=None, alterable=False):
        button_frame = Frame(self)
        button_frame.configure(
            highlightcolor=COLOUR_DICT['light'],
            highlightbackground=COLOUR_DICT['light'],
            highlightthickness=1)
        button = LabelButton(
            button_frame, text=text,
            clickFunc=clickFunc,
            font=(DEFAULT_FONT_FAMILY, 13, BOLD))
        if alterable:
            button.bind('<Button-3>', self.alter_button)
        button.grid()
        self.button_frames.append(button_frame)
        self.__grid_new_button(button_frame)
        return [button_frame, button]

    def click_sim(self, e: Event = None):
        self.main_button.event_generate('<Button-1>')
        self.root.update()
        time.sleep(0.08)
        self.main_button.event_generate('<ButtonRelease-1>')
        self.root.update()

    def alter_button(self, e: Event):
        self.state = next_valid_index(self.state, self.states)
        e.widget.configure(text=self.states[self.state])

    def focus_entry(self):
        self.entry.focus_force()
        self.entry.select_range(0, 'end')
        self.entry.icursor('end')

    def set_entry_bg(self, colour):
        self.entry['background'] = colour

    def show_side_label(self, text):
        self.side_label.configure(text=text)
        self.side_label.grid(row=0, column=len(self.button_frames) + 1, sticky=E)

    def hide_side_label(self, text = ''):
        self.side_label.grid_remove()
        if text != '':
            self.side_label.configure(text=text)

    def set_side_label_text(self, text):
        self.side_label.configure(text=text)

    def get_side_label_text(self):
        return self.side_label.cget('text')

    def get(self):
        return self.entry.get()
