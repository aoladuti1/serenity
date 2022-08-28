from tkinter import *


class LabelButton(Label):
    def __init__(
                self, master,
                activeBG, activeFG, 
                clickBG, clickFG, clickFunc = None,
                defaultBG = None, defaultFG = None,
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
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_enter)

    def on_enter(self, e):
        self['background'] = self.activeBG
        self['foreground'] = self.activeFG

    def on_leave(self, e):
        self['background'] = self.defaultBG
        self['foreground'] = self.defaultFG

    def on_click(self, e):
        self['background'] = self.clickBG
        if self.clickFunc != None: self.clickFunc()