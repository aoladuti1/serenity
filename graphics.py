from tkinter.font import ITALIC
from tkinter import *
from turtle import width
import ttkbootstrap as ttk
import tkintools
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from config import *

class LeftPane:
    def __init__(self, root: ttk.Window, background=COLOUR_DICT['dark']):
        self.root = root
        self.background = background
        self.width = 700
        self.frame = None
        self.browser = None
        self.header = None
        self.subheader = None
        self.controls = None
        self.selCount = 0
        self.selWidget = None

    def drawAll(self):
        self.drawFrame()
        self.drawAllExceptFrame()

    def drawAllExceptFrame(self):
        self.drawHeader()
        self.drawSubheader()
        self.drawControls()
        self.drawBrowser()
        self.populateBrowser()

    def drawFrame(self):
        self.frame = Frame(self.root, height=self.root.winfo_height(), width=self.width)
        self.frame.grid(column = 0, row=0, sticky='nsw', columnspan=1)
        self.frame.rowconfigure(3, weight=1) #browser is stretchy!
        self.frame.configure(background=self.background)
    
    def drawHeader(self):
        self.header = ttk.Label(self.frame, text="serenity", bootstyle='primary')
        self.header.configure(
            font=(DEFAULT_FONT_FAMILY,50, ITALIC),
            background=self.background
        )
        self.header.grid(column=0, row=0, sticky=W)
    
    def drawSubheader(self):
        self.subheader = ttk.Label(self.frame, text="Your library")
        self.subheader.configure(background=self.background)
        self.subheader.grid(column=0, row=1, sticky=W)

    def drawControls(self):
        self.controls = ttk.Label(self.frame, text='--->')
        self.controls.configure(background=self.background)
        self.controls.grid(column=0, row=2)
    
    def drawBrowser(self):
        self.browser = ScrolledFrame(
            self.frame, autohide=True,
            height=self.root.winfo_screenheight(),
            width=self.width
        )
        self.browser.columnconfigure(0, weight=1)
        self.browser.columnconfigure(1, weight=0)
        self.browser.grid(row=3, sticky = NW)

    def populateBrowser(self):
        for x in range(150):
            songLabel = ttk.Label(
                self.browser,
                text="bryson tiller - intro (difference)",
                bootstyle='info',
                width=self.width #makes the highlight bar go fully across
            )
            songLabel.grid(
                column=0, row=x, rowspan=1, sticky=NW
            )
            songLabel.configure(background = self.background)
            songLabel.bind('<Button-1>', self.select)
            buttonFrame = Frame(self.browser)
            buttonFrame.configure(
                highlightcolor=COLOUR_DICT['primary'],
                highlightbackground = COLOUR_DICT['primary'],
                highlightthickness = 1
            )            
            buttonFrame.grid(
                column=1, row=x, rowspan=1, ipady=0, 
                padx=(20,20), pady=(0,9), sticky=E
            )
            button = tkintools.LabelButton(
                buttonFrame, 
                activeBG=ACTIVE_BUTTON_BG_HEX,
                activeFG=COLOUR_DICT['info'],
                clickBG=CLICK_BUTTON_BG_HEX,
                clickFG=COLOUR_DICT['dark'],
                defaultBG=COLOUR_DICT['dark'],
                defaultFG=COLOUR_DICT['primary'],
                text='play', padx=3, pady=0
            )
            button.grid()

    def select(self, e: Event):
        clickedWidget = e.widget
        # IMPORTANT: for some reason the act of converting cget to a string
        # makes it work for comparisons
        if str(clickedWidget.cget('background')) == SELECTED_LABEL_BG_HEX:
            clickedWidget.configure(background = self.background)
        else:
            clickedWidget.configure(background = SELECTED_LABEL_BG_HEX)
