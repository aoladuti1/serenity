from math import ceil
import threading
import time
from tkinter import *
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
        self.sliding = False
        self.pos = ttk.Label(
            self, font=(DEFAULT_FONT_FAMILY, 12), padding='0 0 10 0')
        self.pos.pack(side=LEFT)
        self.new_position = DoubleVar()
        self.slider = ttk.Scale(
            self, from_=0, to_=100, orient=HORIZONTAL,
            variable=self.new_position,
            command=self.seek_percent,
            length=int(Shield.base_pane_width() * 4/9))
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
    def __init__(self, master, clickFunc=None, **kw):
        LabelButton.__init__(
            self, master=master,
            unclickFunc=clickFunc,
            activeFG=COLOUR_DICT['info'],
            activeBG=COLOUR_DICT['bg'],
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['bg'], **kw)