from tkinter import *
from turtle import onclick
from typing import Callable, Any
from config import *

class LabelButton(Label):
    
    def default_on_enter(self, e):
        self['background'] = self.activeBG
        self['foreground'] = self.activeFG

    def default_on_leave(self, e):
        self['background'] = self.defaultBG
        self['foreground'] = self.defaultFG

    def on_click(self, e):
        self['background'] = self.clickBG
        self['foreground'] = self.clickFG
        if self.clickFunc != None: self.clickFunc()
        
    def __init__(
            self, master, clickFunc: Callable = None,
            onClickFunc: Callable = None,
            activeBG=ACTIVE_BUTTON_BG_HEX,
            activeFG=COLOUR_DICT['info'],
            clickBG=CLICK_BUTTON_BG_HEX,
            clickFG=COLOUR_DICT['dark'],
            defaultBG=COLOUR_DICT['dark'],
            defaultFG=COLOUR_DICT['primary'],
            onEnterFunc=None,
            onLeaveFunc=None,
            buttonReleaseFunc=None,
            **kw
        ):
        #onClickFunc totally overrides clickFunc
        #arguments which start with "on" require an event to be passed to them
        # usually achieved with lambda e: functionName 
        Label.__init__(self,master=master,**kw)
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
        self.buttonReleaseFunc = buttonReleaseFunc
        if onClickFunc == None:
            self.onClickFunc = self.on_click
        if defaultBG == None:
            self.defaultBG = self['background']
        if defaultFG == None:
            self.defaultFG = self['foreground']
        if onEnterFunc == None:
            self.onEnterFunc = self.default_on_enter
        if onLeaveFunc == None:
            self.onLeaveFunc = self.default_on_leave
        if buttonReleaseFunc == None:
            self.buttonReleaseFunc = self.onLeaveFunc
        self['background'] = defaultBG
        self['foreground'] = defaultFG
        self.bind("<Enter>", self.onEnterFunc)
        self.bind("<Leave>", self.onLeaveFunc)
        self.bind("<Button-1>", self.onClickFunc)
        self.bind("<ButtonRelease-1>", self.buttonReleaseFunc)

