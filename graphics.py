import threading
import time
from tkinter.font import BOLD, ITALIC
from tkinter import *
from typing import Callable
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
PLAYLISTS='playlists'
PLAYLIST_TRACKS='playlist_tracks'
DOWNLOAD_ARTISTS='download_artists'
DOWNLOAD_TRACKS='download_tracks'

DEFAULT_SUBHEADER=' Your library'
SUBHEADER_TEXT_MAX_WIDTH = 999 # TODO make it fit 1080p, 2k and 4k
PAUSE_LABELS=[' |> ', ' || ']



dbLink = db.DBLink()

class LeftPane:
    def __init__(self, root: ttk.Window, background=COLOUR_DICT['dark']):
        global PANE_WIDTH
        global EDGE_PAD
        self.root = root
        self.background = background
        self.frame = None
        self.browser = None
        self.header = None
        self.subheader = None
        self.libTools = None
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
        self.libToolsVisible = False
        PANE_WIDTH = LEFT_PANE_WIDTH(self.root)
        EDGE_PAD = 20 * math.floor(root.winfo_screenwidth() / 3840)

    def drawAll(self):
        self.drawFrame()
        self.drawAllExceptFrame()

    def drawAllExceptFrame(self):
        self.drawHeader()
        self.drawSubheader()
        self.genLibTools()
        self.drawControls()
        self.drawBrowser()
        self.loadArtists()

    def drawFrame(self):
        self.frame = Frame(self.root, height=self.root.winfo_height(), width=PANE_WIDTH)
        self.frame.grid(column = 0, row=0, sticky='nsw', columnspan=1)
        self.frame.rowconfigure(4, weight=1) # browser is stretchy!
        self.frame.columnconfigure(0, weight=1)
        self.frame.configure(background=self.background)
        self.frame.grid_propagate(False)
    
    def drawHeader(self):
        self.header = ttk.Label(self.frame, text="serenity", bootstyle='primary')
        self.header.configure(
            font=(DEFAULT_FONT_FAMILY, 50, ITALIC),
            background=self.background
        )
        self.header.grid(column=0, row=0, sticky=W)
    
    def drawSubheader(self):
        self.subheader = tkintools.LabelButton(
            self.frame,text=DEFAULT_SUBHEADER,
            activeFG=COLOUR_DICT['info'],
            activeBG=COLOUR_DICT['dark'],
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            clickFunc=self.showHideLibTools,
            buttonReleaseFunc=lambda e: self.controlRelease(e),
            background=self.background,
            font=(DEFAULT_FONT_FAMILY,12),
        )

        bbFrame = Frame(self.frame, padx=EDGE_PAD)
        bbFrame.configure(background=self.background)
        bbFrame.grid(row=1, column=0, columnspan=2, sticky=E)
        
        self.backButton = tkintools.LabelButton(
            bbFrame,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            clickFunc= self.goBack,
            text='---',
            font=(DEFAULT_FONT_FAMILY,12, BOLD)
        )
        self.backButton.grid()
        self.subheader.grid(column=0, columnspan=1, row=1, sticky=W)
        
    def showHideLibTools(self, e: Event = None):  
        if self.libToolsVisible is False:
            self.libTools.grid(row=2, pady=5)
        else:
            self.libTools.grid_remove()
        self.libToolsVisible = not self.libToolsVisible

    def genLibTools(self):
        self.libTools = Frame(self.frame)
        self.libTools.configure(background=self.background)
        addArtists = tkintools.LabelButton(
            self.libTools,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            text='[add artists]',
            font=(DEFAULT_FONT_FAMILY, 12, BOLD)
        )
        addAlbums = tkintools.LabelButton(
            self.libTools,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            text='[add albums]',
            font=(DEFAULT_FONT_FAMILY, 12, BOLD)
        )
        addSongs = tkintools.LabelButton(
            self.libTools,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            text='[add songs]',
            font=(DEFAULT_FONT_FAMILY, 12, BOLD)
        )
        padx = 7
        addArtists.grid(column=0, row=0, sticky=S, padx=padx)
        addAlbums.grid(column=1, row=0, sticky=S, padx=padx)
        addSongs.grid(column=2, row=0, sticky=S, padx=padx)

    def drawControls(self):
        self.controls = Frame(self.frame)
        self.controls.grid(row=3, pady=5)
        self.controls.configure(background=self.background)
        seek = self.genControlButton(
            clickFunc=lambda t=10: self.controlThreader(Aplayer.seek(seconds=t)),
            text=' ++> '   
        )

        pause = self.genControlButton(
            clickFunc=lambda: self.controlThreader(Aplayer.pauseplay),
            text=' |> '
        )
        padx = 13
        pause.grid(column=0, row=0, sticky=S, padx=padx)
        seek.grid(column=1, row=0, sticky=S, padx=padx)
        self.pauseButton = pause
        threading.Thread(target=self.monitorPlaystate, daemon=True).start()
        

    def monitorPlaystate(self):
        while True:
            try:
                self.pauseButton.configure(text=PAUSE_LABELS[int(Aplayer.is_paused())])
            except: pass #tkinter complains about the threading but i don't care
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
            font=(DEFAULT_FONT_FAMILY,18, BOLD)
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
            width=PANE_WIDTH
        )
        self.browser.columnconfigure(0, weight=1)
        self.browser.columnconfigure(1, weight=0)
        self.browser.grid(row=4, sticky = NW, columnspan=1)

    def genBrowserButton(self, row: int, text: str = 'play', clickFunc = None):
        buttonFrame = Frame(self.browser)
        buttonFrame.configure(
            highlightcolor=COLOUR_DICT['primary'],
            highlightbackground = COLOUR_DICT['primary'],
            highlightthickness = 1
        )            
        buttonFrame.grid(
            column=1, row=row, rowspan=1, ipady=0, 
            padx=(EDGE_PAD,EDGE_PAD), pady=(0,9), sticky=E
        )
        button = tkintools.LabelButton(
            buttonFrame, text=text, padx=3, pady=0, clickFunc=clickFunc
        )
        button.grid()
        return buttonFrame
    
    def genBrowserLabel(self, row: int, text: str, dblClickFunc = None):
        browserLabel = ttk.Label(
            self.browser,
            text=" " + text,
            bootstyle='info',
            width=PANE_WIDTH #makes the highlight bar go fully across
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
                    self.chosenArtist = e.widget.cget('text').lstrip()
        self.browser.grid_remove()
        self.drawBrowser()
        self.loadAlbums()

    def __killAndloadTracks(self, e: Event = None):
        if e != None:
            for widget in self.browser.winfo_children():
                if widget == e.widget:
                    self.chosenAlbum = e.widget.cget('text').lstrip()
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
            self.fetchedArtists = dbLink.get_artists()
        i = 0
        for tuple in self.fetchedArtists:
            name = tuple[0]     
            self.genBrowserLabel(i, name, self.__killAndLoadAlbums)
            self.genBrowserButton(i)
            i += 1
        if i == 0:
            txt = ttk.Text(self.browser, font=(DEFAULT_FONT_FAMILY, 15))
            txt.insert(INSERT,
                (
                "Click 'Your Library' to add some music!\n"
              + "When you choose a directory all music files "
              + "in its subdirectories will be "
              + "added to the database.\n\n"
              + "Click [add artists] if each song is in an album folder, and "
              + "each album folder is inside an artist folder\n"
              + "(e.g. music/Bryson Tiller/T R A P S O U L/05 - Dont.mp3).\n\n"
              + "Click [add albums] if each "
              + "song is in an album folder, and the song filename "
              + "or album folder name has the artist's name in it\n"
              + "(e.g. music/True to Self/Bryson Tiller - Self Made.mp3).\n\n"
              + "Otherwise, click [add songs] and we'll try our best to get "
              + "all your music added and organised nicely :-)\n\n"
              + "Don't worry too much about the EXACT file / folder names, "
              + "Serenity is flexible!\n"
              + "[Note: Serenity does not use metadata at all. "
              + "Things like track number can be signalled by being "
              + "present in the filename like .../01 - Intro.mp3.]"
            ))
            txt.configure(
                background=self.background, highlightbackground=self.background,
                wrap=WORD)
            txt.grid(columnspan=2)
        
    
    def loadAlbums(self):
        self.backButton.configure(text="<--")
        self.currentPage = ALBUMS
        self.fetchedAlbums = dbLink.get_albums(self.chosenArtist)
        self.updateSubheader()
        i = 0
        for tuple in self.fetchedAlbums:
            name = tuple[0]     
            browserLabel = self.genBrowserLabel(i, name, self.__killAndloadTracks)
            buttonFrame = self.genBrowserButton(i)
            i += 1        
    
    def loadTracks(self):
        self.currentPage = TRACKS
        self.fetchedSongs = dbLink.get_songs_by_album(self.chosenAlbum, self.chosenArtist)
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
            lambda song=song, queue=True: 
                Aplayer.play(song, queue)
        )


    def select(self, e: Event):
        clickedWidget = e.widget
        # IMPORTANT: for some reason the act of converting cget to a string
        # makes it work for comparisons
        if str(clickedWidget.cget('background')) == SELECTED_LABEL_BG_HEX:
            clickedWidget.configure(background = self.background)
        else:
            clickedWidget.configure(background = SELECTED_LABEL_BG_HEX)
