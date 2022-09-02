from concurrent.futures import thread
import copy
import threading
import time
from tkinter.font import BOLD, ITALIC
from tkinter import *
from turtle import back, width
from typing import Callable, Optional
import ttkbootstrap as ttk
from aplayer import Aplayer
import tkintools
import db
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from config import *


ARTISTS='artists'
ALBUMS='albums'
TRACKS='tracks'
DEFAULT_SUBHEADER='Your library'
SUBHEADER_TEXT_MAX_WIDTH = 42
PAUSE_LABELS=['|>','||']


class LeftPane:
    def __init__(self, root: ttk.Window, background=COLOUR_DICT['dark']):
        self.root = root
        self.background = background
        self.frame = None
        self.browser = None
        self.header = None
        self.subbar = None
        self.subheader = None
        self.controls = None
        self.backButton = None
        self.pauseButton = None
        self.selCount = 0
        self.selWidget = None
        self.fetchedArtists = None
        self.fetchedAlbums = None
        self.fetchedSongs = None
        self.chosenArtist = None # should never be NoneType after init
        self.chosenAlbum = None # should never be NoneType after init
        self.chosenSong = None # should never be NoneType after init
        self.currentPage = ARTISTS

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
        self.frame.grid_propagate(False)
    
    def drawHeader(self):
        self.header = ttk.Label(self.frame, text="serenity", bootstyle='primary')
        self.header.configure(
            font=(DEFAULT_FONT_FAMILY,50, ITALIC),
            background=self.background
        )
        self.header.grid(column=0, row=0, sticky=W)
    
    def drawSubheader(self):
        self.subbar = Frame(self.frame, width=LEFT_PANE_WIDTH)
        self.subheader = ttk.Label(
            self.subbar,text=DEFAULT_SUBHEADER, 
            width=SUBHEADER_TEXT_MAX_WIDTH, background=self.background,
            font=(DEFAULT_FONT_FAMILY,    12)
        )
        self.backButton = tkintools.LabelButton(
            self.subbar,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            clickFunc= self.goBack,
            text='---',
            font=(DEFAULT_FONT_FAMILY,12, BOLD)
        )
        self.subbar.configure(background=self.background)
        self.subbar.columnconfigure(1, weight=0)        
        self.subbar.grid(row=1, sticky=W)
        self.subheader.grid(column=0, row=0, sticky=W)
        self.backButton.grid(row=0, column=1, padx=20, sticky=E)

    def drawControls(self):
        self.controls = Frame(self.frame)
        self.controls.grid(row=2, pady=5)
        self.controls.configure(background=self.background)
        seek = self.genControlButton(
            clickFunc=lambda t=10, type="+": self.controlThreader(Aplayer.seek(seconds=t,type=type)),
            text='++>'   
        )
        pause = self.genControlButton(
            clickFunc=lambda: self.controlThreader(Aplayer.pauseplay),
            text='|>'
        )
        padx = 7
        pause.grid(column=0, row=0, sticky=S, padx=padx)
        seek.grid(column=1, row=0, sticky=S, padx=padx)
        threading.Thread(target=self.monitorPlaystate, daemon=True).start()
        self.pauseButton = pause

    def monitorPlaystate(self):
        while True:
            self.pauseButton.configure(text=PAUSE_LABELS[int(Aplayer.playing)])
            time.sleep(1)

    def genControlButton(self, text: str, clickFunc: Callable):
        return tkintools.LabelButton(
            self.controls,
            onEnterFunc=self.wrapSquares,
            onLeaveFunc=self.unwrapSquares, 
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            clickFunc=clickFunc,
            buttonReleaseFunc=lambda e: self.controlRelease(e),
            text=text,
            font=(DEFAULT_FONT_FAMILY,12, BOLD)
        )

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
        self.browser.grid(row=3, sticky = NW, columnspan=1)

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
        
    def updateSubheader(self):
        if self.currentPage == ARTISTS:
            text=DEFAULT_SUBHEADER
        elif self.currentPage == ALBUMS:
            text=">> {}".format(self.chosenArtist)
        elif self.currentPage == TRACKS:
            text=">> {}\{}".format(self.chosenArtist, self.chosenAlbum)
        if len(text) > SUBHEADER_TEXT_MAX_WIDTH:
            text = text[0:SUBHEADER_TEXT_MAX_WIDTH-3] + '...'
        self.subheader.configure(text=text)


    def goBack(self):
        if self.currentPage == TRACKS:
            self.__killAndLoadAlbums() 
        elif self.currentPage == ALBUMS:
            self.__killAndLoadArtists()   
    

    def __killAndLoadAlbums(self, e: Event = None):
        if e != None:
            for widget in self.browser.winfo_children():
                if widget == e.widget:
                    self.chosenArtist = e.widget.cget('text')
        self.browser.grid_remove()
        self.drawBrowser()
        self.loadAlbums()

    def __killAndloadTracks(self, e: Event = None):
        if e != None:
            for widget in self.browser.winfo_children():
                if widget == e.widget:
                    self.chosenAlbum = e.widget.cget('text')
        self.browser.grid_remove()
        self.drawBrowser()
        self.loadTracks()
    
    def __killAndLoadArtists(self, e: Event = None):
        self.browser.grid_remove()
        self.drawBrowser()
        self.loadArtists()


    def loadArtists(self):
        self.backButton.configure(text="---")
        self.currentPage = ARTISTS
        self.updateSubheader()
        if self.fetchedArtists == None:
            self.fetchedArtists = db.getArtists()
        i = 0
        for tuple in self.fetchedArtists:
            name = tuple[0]     
            self.genBrowserLabel(i, name, self.__killAndLoadAlbums)
            self.genBrowserButton(i)
            i += 1
    
    def loadAlbums(self):
        self.backButton.configure(text="<--")
        self.currentPage = ALBUMS
        self.fetchedAlbums = db.getAlbumsByArtist(self.chosenArtist)
        self.updateSubheader()
        i = 0
        for tuple in self.fetchedAlbums:
            name = tuple[0]     
            browserLabel = self.genBrowserLabel(i, name, self.__killAndloadTracks)
            buttonFrame = self.genBrowserButton(i)
            i += 1        
    
    def loadTracks(self):
        self.currentPage = TRACKS
        self.fetchedSongs = db.getSongsByAlbum(self.chosenAlbum, self.chosenArtist)
        self.updateSubheader()
        i = 0
        for song in self.fetchedSongs:
            name = song['track']  
            self.genBrowserLabel(i, name)
            self.genBrowserButton(i, clickFunc=lambda song=song: self.playTrack(song=song))
            i += 1
    
    def playTrack(self, song):
        self.chosenSong = song
        self.controlThreader(
            lambda song=song, skipOnLoad=True: 
                Aplayer.play(song, skipOnLoad)
        )


    def select(self, e: Event):
        clickedWidget = e.widget
        # IMPORTANT: for some reason the act of converting cget to a string
        # makes it work for comparisons
        if str(clickedWidget.cget('background')) == SELECTED_LABEL_BG_HEX:
            clickedWidget.configure(background = self.background)
        else:
            clickedWidget.configure(background = SELECTED_LABEL_BG_HEX)
