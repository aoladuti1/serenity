from concurrent.futures import thread
import copy
import threading
import time
from tkinter.font import ITALIC
from tkinter import *
import ttkbootstrap as ttk
from aplayer import Aplayer
import tkintools
import db
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from config import *

class LeftPane:
    def __init__(self, root: ttk.Window, background=COLOUR_DICT['dark']):
        self.root = root
        self.background = background
        self.frame = None
        self.browser = None
        self.header = None
        self.subheader = None
        self.controls = None
        self.selCount = 0
        self.selWidget = None
        self.fetchedArtists = None
        self.fetchedAlbums = None
        self.fetchedSongs = None
        self.chosenArtist = None
        self.chosenAlbum = None
        self.chosenSong = None
        

    def drawAll(self):
        self.drawFrame()
        self.drawAllExceptFrame()

    def drawAllExceptFrame(self):
        self.drawHeader()
        self.drawSubheader()
        self.drawControls()
        self.drawBrowser()
        self.loadArtists()

    def drawFrame(self):
        self.frame = Frame(self.root, height=self.root.winfo_height(), width=LEFT_PANE_WIDTH)
        self.frame.grid(column = 0, row=0, sticky='nsw', columnspan=1)
        self.frame.rowconfigure(3, weight=1) # browser is stretchy!
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
        self.controls = Frame(self.frame)
        self.controls.grid()
        self.controls.configure(background=self.background)
        skip = tkintools.LabelButton(
            self.controls, 
            onEnterFunc=self.wrapSquares,
            onLeaveFunc=self.unwrapSquares, 
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            clickFunc=lambda t=10, type="+": self.controlThreader(Aplayer.seek(seconds=t,type=type)),
            buttonReleaseFunc=lambda e: self.controlRelease(e),
            text='++>'
        )
        skip.grid()

    def controlThreader(self, function):
        threading.Thread(
                target=self.controlHandler, 
                args=(function,)
                ).start()

    def controlHandler(self, function):
        time.sleep(0.07)
        if (function != None):
            function()

    def controlRelease(self, e: Event):
        e.widget.configure(foreground=COLOUR_DICT['primary'])
        self.unwrapSquares(e)
    
    def drawBrowser(self):
        self.browser = ScrolledFrame(
            self.frame, autohide=True,
            height=self.root.winfo_screenheight(),
            width=LEFT_PANE_WIDTH
        )
        self.browser.columnconfigure(0, weight=1)
        self.browser.columnconfigure(1, weight=0)
        self.browser.grid(row=3, sticky = NW)

    def getDur(self):
        return self.songDur

    def genBrowserButton(self, row: int, text: str = 'play', clickFunc = None):
        buttonFrame = Frame(self.browser)
        buttonFrame.configure(
            highlightcolor=COLOUR_DICT['primary'],
            highlightbackground = COLOUR_DICT['primary'],
            highlightthickness = 1
        )            
        buttonFrame.grid(
            column=1, row=row, rowspan=1, ipady=0, 
            padx=(20,20), pady=(0,9), sticky=E
        )
        button = tkintools.LabelButton(
            buttonFrame, text=text, padx=3, pady=0, clickFunc=clickFunc
        )
        button.grid()
        return buttonFrame
    
    def genBrowserLabel(self, row: int, text: str, dblClickFunc = None):
        browserLabel = ttk.Label(
            self.browser,
            text=text,
            bootstyle='info',
            width=LEFT_PANE_WIDTH #makes the highlight bar go fully across
        )
        browserLabel.grid(
            column=0, row=row, rowspan=1, sticky=NW
        )
        browserLabel.configure(background = self.background)
        browserLabel.bind('<Button-1>', lambda e: self.select(e))
        browserLabel.bind('<Double-Button-1>', dblClickFunc)
        return browserLabel    

    def wrapSquares(self, e: Event):
        text = e.widget.cget('text')
        e.widget.configure(text= '[' + text + ']')
    
    def unwrapSquares(self, e: Event):
        text = e.widget.cget('text')
        if text.startswith('['):
            e.widget.configure(text=text[1:-1])        
    

    def __killAndLoadAlbums(self, e: Event):
        for widget in self.browser.winfo_children():
            if widget == e.widget:
                self.chosenArtist = e.widget.cget('text')
        self.browser.grid_remove()
        self.drawBrowser()
        self.loadAlbums()

    def __killAndLoadSongs(self, e: Event):
        for widget in self.browser.winfo_children():
            if widget == e.widget:
                self.chosenAlbum = e.widget.cget('text')
        self.browser.grid_remove()
        self.drawBrowser()
        self.loadSongs()

    def loadArtists(self):
        if self.fetchedArtists == None:
            self.fetchedArtists = db.getArtists()
        i = 0
        for tuple in self.fetchedArtists:
            name = tuple[0]     
            self.genBrowserLabel(i, name, self.__killAndLoadAlbums)
            self.genBrowserButton(i)
            i += 1
    
    def loadAlbums(self):
        self.fetchedAlbums = db.getAlbumsByArtist(self.chosenArtist)
        i = 0
        for tuple in self.fetchedAlbums:
            name = tuple[0]     
            browserLabel = self.genBrowserLabel(i, name, self.__killAndLoadSongs)
            buttonFrame = self.genBrowserButton(i)
            i += 1        
    
    def loadSongs(self):
        if self.fetchedSongs == None:
            self.fetchedSongs = db.getSongsByAlbum(self.chosenAlbum, self.chosenArtist)
        i = 0
        for song in self.fetchedSongs:
            name = song['track']  
            self.genBrowserLabel(i, name)
            self.genBrowserButton(i, clickFunc= lambda skipOnLoad=False, song=song: self.controlThreader(Aplayer.play(song, skipOnLoad)))
            i += 1

    def select(self, e: Event):
        clickedWidget = e.widget
        # IMPORTANT: for some reason the act of converting cget to a string
        # makes it work for comparisons
        if str(clickedWidget.cget('background')) == SELECTED_LABEL_BG_HEX:
            clickedWidget.configure(background = self.background)
        else:
            clickedWidget.configure(background = SELECTED_LABEL_BG_HEX)
