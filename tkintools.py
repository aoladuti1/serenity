from tkinter import *
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
        if self.clickFunc != None: self.clickFunc(e)


    def __init__(
                self, master, clickFunc = None,
                activeBG=ACTIVE_BUTTON_BG_HEX,
                activeFG=COLOUR_DICT['info'],
                clickBG=CLICK_BUTTON_BG_HEX,
                clickFG=COLOUR_DICT['dark'],
                defaultBG=COLOUR_DICT['dark'],
                defaultFG=COLOUR_DICT['primary'],
                onEnterFunc=None,
                onLeaveFunc=None,
                **kw
                ):
        Label.__init__(self,master=master,**kw)   
        self.clickFunc = clickFunc
        self.defaultBG = self["background"]
        self.defaultFG = self["foreground"]
        if defaultBG != None:
            self.defaultBG = defaultBG
        if defaultFG != None:
            self.defaultFG = defaultFG
        self.activeBG = activeBG
        self.activeFG = activeFG
        self.clickBG = clickBG
        self.clickFG = clickFG
        self['background'] = defaultBG
        self.onEnterFunc = onEnterFunc
        self.onLeaveFunc = onLeaveFunc
        if onEnterFunc == None:
            self.onEnterFunc = self.default_on_enter
        if onLeaveFunc == None:
            self.onLeaveFunc = self.default_on_leave

        self.bind("<Enter>", self.onEnterFunc)
        self.bind("<Leave>", self.onLeaveFunc)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.onLeaveFunc)

