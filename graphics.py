
import threading
import time
import tkintools
import db
import ttkbootstrap as ttk
from pathlib import Path
from tkinter.font import BOLD, ITALIC
from tkinter import *
from typing import Callable
from aplayer import Aplayer
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from config import *


ARTISTS='artists'
ALBUMS='albums'
TRACKS='tracks'
PLAYLISTS='playlists'
PLAYLIST_SONGS='playlist_songs'
DOWNLOAD_ARTISTS='download_artists'
DOWNLOAD_TRACKS='download_tracks'
PLAY = 'play'
QUEUE = 'queue'

dbLink = db.DBLink()

class LeftPane:

    PAUSE_LABELS=[' || ', ' |> ']
    BROWSER_BUTTON_PADX = 4
    BACK_TEXT = '<--'
    NO_BACK_TEXT = '---'
    SPECIAL_HEX = COLOUR_DICT['primary']
    DEFAULT_SUBHEADER=' Your library'
    STARTING_TEXT = ' ..starting..'
    QUEUING_TEXT = ' ..queuing..'
    SUBHEADER_TEXT_MAX_WIDTH = 999 # TODO make it fit 1080p, 2k and 4k
    

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
        self.loading = False
        self.controls = None
        self.backButton = None
        self.pauseButton = None
        self.selCount = 0
        self.selWidget = None
        self.fetchedArtists = None
        self.fetchedAlbums = None
        self.fetchedTracksAndPaths = None
        self.chosenArtist = None # should never be NoneType after init
        self.chosenAlbum = None # should never be NoneType after init
        self.chosenSong = None # should never be NoneType after init
        self.chosenPlaylist = None
        self.currentPage = ARTISTS
        self.subframe = None
        self.libToolsVisible = False
        self.entryBarVisible = False
        self.selectedContent = []
        PANE_WIDTH = LEFT_PANE_WIDTH(self.root)
        EDGE_PAD = math.floor(25 * root.winfo_screenwidth() / 3840)

    def drawAll(self):
        self.drawFrame()
        self.drawAllExceptFrame()

    def drawAllExceptFrame(self):
        self.drawHeader()
        
        self.drawSubheader()
        self.drawBackbutton()
        self.genLibTools()
        self.genEntryBar()
        self.drawControls()
        self.drawBrowser()
        self.loadArtists()

    def drawFrame(self):
        self.frame = Frame(self.root, height=self.root.winfo_height(), width=PANE_WIDTH)
        self.frame.grid(column = 0, row=0, sticky='nsw', columnspan=1)
        self.frame.rowconfigure(5, weight=1) # browser is stretchy!
        self.frame.columnconfigure(0, weight=1)
        self.frame.configure(background=self.background)
        self.frame.grid_propagate(False)
    
    def drawHeader(self):
        self.header = ttk.Label(self.frame, text="serenity", bootstyle='primary')
        self.header.configure(
            font=(DEFAULT_FONT_FAMILY, 50, ITALIC),
            background=self.background)
        self.header.grid(column=0, row=0, sticky=W)
    
    def drawSubheader(self):
        self.subheader = tkintools.LabelButton(
            self.frame, text=LeftPane.DEFAULT_SUBHEADER,
            activeFG=COLOUR_DICT['info'],
            activeBG=COLOUR_DICT['dark'],
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            clickFunc=self.showHideExtras,
            buttonReleaseFunc=lambda e: self.controlRelease(e),
            background=self.background,
            font=(DEFAULT_FONT_FAMILY, 14))
        self.subheader.grid(column=0, row=1, sticky=W)

    def drawBackbutton(self):
        bbFrame = Frame(self.frame, padx=EDGE_PAD)
        bbFrame.configure(background=self.background)
        bbFrame.grid(row=1, rowspan=1, sticky=NE)
        self.backButton = tkintools.LabelButton(
            bbFrame,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            clickFunc= self.goBack,
            text=LeftPane.NO_BACK_TEXT,
            font=(DEFAULT_FONT_FAMILY,16, BOLD)
        )
        self.backButton.grid()

    def showHideExtras(self, e: Event = None):
        self.__showHideLibTools()
        self.__showHideEntryBar()

    def __showHideLibTools(self):  
        if self.libToolsVisible is False:
            self.libTools.grid(row=3, pady=5)
        else:
            self.libTools.grid_remove()
        self.libToolsVisible = not self.libToolsVisible

    def __showHideEntryBar(self):  
        if self.entryBarVisible is False:
            self.entryBar.grid(row=2, rowspan=1, pady=5)
        else:
            self.entryBar.grid_remove()
        self.entryBarVisible = not self.entryBarVisible

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
        addArtists.grid(column=0, row=2, sticky=S, padx=padx)
        addAlbums.grid(column=1, row=2, sticky=S, padx=padx)
        addSongs.grid(column=2, row=2, sticky=S, padx=padx)
    
    def genEntryBar(self):
        self.entryBar = Frame(self.frame)
        self.entryBar.configure(background=self.background)
        stream = tkintools.LabelButton(
            self.entryBar,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            text='[stream]',
            font=(DEFAULT_FONT_FAMILY, 12, BOLD)
        )
        search = tkintools.LabelButton(
            self.entryBar,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            text='[search]',
            font=(DEFAULT_FONT_FAMILY, 12, BOLD)
        )
        entry = ttk.Entry(self.entryBar)
        entry.grid(row=0,column=0)
        entry.configure(font = (DEFAULT_FONT_FAMILY,10))
        entry.focus_force()
        stream.grid(row=0,column=2, sticky=S)
        search.grid(row=0,column=1, sticky=S)

    def drawControls(self):
        self.controls = Frame(self.frame)
        self.controls.grid(row=4, pady=5, rowspan=1)
        self.controls.configure(background=self.background)
        seek_pos = self.genControlButton(
            clickFunc=lambda e, t=10: self.controlThreader(e, Aplayer.seek(seconds=t)),
            text=' ++> '   
        )
        seek_neg = self.genControlButton(
            clickFunc=lambda e, t=-10: self.controlThreader(e, Aplayer.seek(seconds=t)),
            text=' <++ '   
        )
        pause = self.genControlButton(
            clickFunc=lambda e: self.controlThreader(e, Aplayer.pauseplay),
            text=' |> '
        )
        pause.grid(column=1, row=0, sticky=S, pady=5)
        seek_pos.grid(column=2, row=0, sticky=S, pady=5)
        seek_neg.grid(column=0, row=0, sticky=S, pady=5)
        self.pauseButton = pause
        threading.Thread(target=self.monitorPlaystate, daemon=True).start()
        

    def monitorPlaystate(self):
        while True:
            try:
                self.pauseButton.configure(text=LeftPane.PAUSE_LABELS[int(Aplayer.is_paused())])
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
            font=(DEFAULT_FONT_FAMILY, 16, BOLD)
        )

    def controlThreader(self, e: Event, function):
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
    
    def genBrowser(self):
        browser = ScrolledFrame(
            self.frame, autohide=True,
            height=self.root.winfo_screenheight(),
            width=PANE_WIDTH
        )
        browser.columnconfigure(0, weight=1)
        browser.columnconfigure(1, weight=0)
        return browser

    def drawBrowser(self, browser = None):
        if browser is None:
            self.browser = self.genBrowser()
        else:
            self.browser.grid_remove()
            self.browser = browser
        self.loading = False
        self.browser.grid(row=5, sticky = NW, columnspan=1, rowspan=1)

    def flipBrowserButton(self, e):
        text_states = ['play', 'queue']
        button = e.widget
        button.configure(text=text_states[int(not e.widget.state)])
        button.state = int(not button.state)
        
    def genBrowserButton(self, row: int, text: str = PLAY, 
                        clickFunc = None, browser = None):
        if browser is None:
            browser = self.browser
        buttonFrame = Frame(browser)
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
            buttonFrame, text=text, padx=LeftPane.BROWSER_BUTTON_PADX, 
            pady=0, clickFunc=clickFunc, width=5
        )
        button.bind('<Button-3>', self.flipBrowserButton)
        button.grid()
        return buttonFrame

    def genBasicBrowserButton(self, row: int, text: str = 'open', 
                        clickFunc = None, browser = None):
        if browser is None:
            browser = self.browser
        buttonFrame = Frame(browser)
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
            buttonFrame, text=text, padx=LeftPane.BROWSER_BUTTON_PADX, 
            pady=0, clickFunc=clickFunc
        )
        button.grid()
        return buttonFrame
        


    
    def genBrowserLabel(self, row: int, text: str, label_type: str,
                        dblClickFunc = None, browser = None):
        if browser is None:
            browser = self.browser
        browserLabel = tkintools.TypedLabel(
            browser,
            label_type=label_type,
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
        
    def updateSubheader(self, new_page: str):
        self.currentPage = new_page
        if self.currentPage != ARTISTS:
            self.backButton.configure(text=LeftPane.BACK_TEXT)
        else:
            self.backButton.configure(text=LeftPane.NO_BACK_TEXT)
        if self.currentPage == ARTISTS:
            text=LeftPane.DEFAULT_SUBHEADER
        elif self.currentPage == ALBUMS:
            text=">> {}".format(self.chosenArtist)
        elif self.currentPage == TRACKS:
            text=">> {}\{}".format(self.chosenArtist, self.chosenAlbum)
        elif self.currentPage == PLAYLISTS:
            text=">> {}".format(PLAYLIST_FOLDER_NAME)
        elif self.currentPage == PLAYLIST_SONGS:
            text=">> {}\{}".format(
                PLAYLIST_FOLDER_NAME, Path(self.chosenPlaylist).stem)
        if len(text) > LeftPane.SUBHEADER_TEXT_MAX_WIDTH:
            text = text[0:LeftPane.SUBHEADER_TEXT_MAX_WIDTH-3] + '...'
        self.subheader.configure(text=text)

    def goBack(self, e: Event = None):
        if self.currentPage == TRACKS:
            self.loadAlbums()
        elif (self.currentPage == ALBUMS
                or self.currentPage == PLAYLISTS):
            self.loadArtists()
        elif self.currentPage == PLAYLIST_SONGS:
            self.__go_to_playlists()
    
    def __go_to_playlists(self, e: Event = None):
        if self.loading is True:
            return
        browser = self.genBrowser()
        self.updateSubheader(PLAYLISTS)
        i = 0
        self.loading = True
        for name in Aplayer.get_playlist_names():   
            self.genBrowserLabel(
                i, Path(name).stem, PLAYLISTS,
                lambda e, pl=name: self.__go_to_playlist_songs(e, pl),
                browser=browser)
            self.genBrowserButton(i, browser=browser)
            i += 1
        self.drawBrowser(browser)

    def __show_label_load_stats(self, e: Event, text: str, count: int, max: int):
        e.widget.configure(text="{} [{:.1f}%]".format(text, 100 * count / max))
        self.root.update()        

    def __go_to_playlist_songs(self, e: Event, chosen_playlist: str):
        if self.loading is True:
            return
        self.chosenPlaylist = chosen_playlist
        self.updateSubheader(PLAYLIST_SONGS)
        browser = self.genBrowser()
        i = 0
        chosen_playlist_files = open(chosen_playlist, 'r').readlines()
        chosen_playlist_title = self.strip_widget_text(e)
        playlist_length = len(chosen_playlist_files)
        for song in chosen_playlist_files:
            self.genBrowserLabel(
                i, Aplayer.get_title_from_file(song),
                PLAYLIST_SONGS, browser=browser)
            self.__show_label_load_stats(
                e, chosen_playlist_title, i, playlist_length)
            i += 1
        self.drawBrowser(browser)

    def __play_track(self, FQFN, queue):
        threading.Thread(target=Aplayer.loadfile, args=(FQFN, queue)).start()

    def __play_album(self, artist_album, queue):
        album, artist = artist_album.split('|')
        pull = dbLink.get_album_filenames(album, artist)
        track_list = [i[0] for i in pull]
        threading.Thread(
            target=Aplayer.loadall, args=(track_list, queue)).start()
        
    def __play_artist(self, artist, queue):
        pull = dbLink.get_artist_filenames(artist)
        artist_list = [i[0] for i in pull]
        threading.Thread(
            target=Aplayer.loadall, args=(artist_list, queue)).start()

    def play(self, e: Event, data: str, external_label=None, queue_files = False):
        button = None
        if external_label is None:
            widget = e.widget
        else:
            button = e.widget
            widget = external_label
        if queue_files == False and not button is None: 
            queue = button.state == 1
        else:
            queue = queue_files
        label_type = widget.label_type
        if label_type == TRACKS:
            self.__play_track(data, queue)
        elif label_type == ALBUMS:
            self.__play_album(data, queue)
        elif label_type == ARTISTS:
            self.__play_artist(data, queue)
        threading.Thread(target=self._temp_mark_playing, 
                        args=(widget, queue), daemon=True).start()
            
    def _temp_mark_playing(self, widget, queue):
        old_fg = widget.cget('foreground')
        if str(old_fg) == str(LeftPane.SPECIAL_HEX):
            return
        old_text = widget.cget('text')
        new_text = LeftPane.STARTING_TEXT if queue is False else LeftPane.QUEUING_TEXT
        widget.configure(foreground=LeftPane.SPECIAL_HEX)
        widget.configure(text=new_text + old_text)
        self.root.update()
        time.sleep(1.25)
        widget.configure(foreground=old_fg)
        widget.configure(text=old_text)

    def loadArtists(self):
        if self.loading is True:
            return
        self.browser.grid_remove()
        self.drawBrowser()
        self.updateSubheader(ARTISTS)
        if self.fetchedArtists == None:
            self.fetchedArtists = dbLink.get_artists()
        i = 0
        if Aplayer.get_number_of_playlists() > 0:
            l = self.genBrowserLabel(i, PLAYLISTS, ARTISTS, self.__go_to_playlists)
            l.configure(foreground=COLOUR_DICT['light'])
            self.genBasicBrowserButton(i, text="open")
            i += 1
        if dbLink.table_is_empty(db.DOWNLOADS) is False:
            # TODO: implement a download button appearing
            i += 1
        
        for tuple in self.fetchedArtists:
            name = tuple[0]     
            l = self.genBrowserLabel(i, name, ARTISTS, self.loadAlbums)
            self.genBrowserButton(
                i,
                clickFunc=lambda e, data=name, label=l: self.play(e,data,label))
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
        
    def strip_widget_text(self, e: Event):
        text = e.widget.cget('text')
        if text.startswith(LeftPane.STARTING_TEXT):
            text = text[len(LeftPane.STARTING_TEXT):]
        elif text.startswith(LeftPane.QUEUING_TEXT):
            text = text[len(LeftPane.QUEUING_TEXT):]
        return text.lstrip()

    def loadAlbums(self, e: Event = None):
        if self.loading is True:
            return
        if e != None:
            self.chosenArtist = self.strip_widget_text(e)
        self.fetchedAlbums = dbLink.get_albums(self.chosenArtist)
        self.updateSubheader(ALBUMS)
        album_count = len(self.fetchedAlbums)
        browser = self.genBrowser()
        i = 0
        text = " " + self.chosenArtist
        for album_tuple in self.fetchedAlbums:
            label = self.genBrowserLabel(
                i, album_tuple[0], ALBUMS, self.loadTracks, browser)
            label_data = album_tuple[0] + '|' + self.chosenArtist
            self.genBrowserButton(
                i, browser=browser,
                clickFunc=(
                    lambda e, data=label_data, label=label:
                        self.play(e, data, label)))
            if e != None:
                self.__show_label_load_stats(
                    e, text, i, album_count)
            i+=1
        self.browser.grid_remove()
        self.drawBrowser(browser)    
    
    def loadTracks(self, e: Event = None):
        if self.loading is True:
            return
        text = ''
        if e != None:
            text = e.widget.cget('text')
            self.chosenAlbum = self.strip_widget_text(e)
        self.fetchedTracksAndPaths = dbLink.get_all_tracks_and_paths(
                                    self.chosenAlbum, self.chosenArtist)
        self.updateSubheader(TRACKS)
        song_count = len(self.fetchedTracksAndPaths)
        browser = self.genBrowser()
        i = 0
        text = " " + self.chosenAlbum
        self.loading = True
        for tuple in self.fetchedTracksAndPaths:
            label = self.genBrowserLabel(
                i, tuple[0], TRACKS,
                lambda e, file=tuple[1]:
                    self.play(e, file), browser)
            self.genBrowserButton(
                i, browser=browser,
                clickFunc=(
                    lambda e, data=tuple[1], label=label:
                        self.play(e, data, label)))
            if e != None:
                self.__show_label_load_stats(
                    e, text, i, song_count)
            i+=1
        self.loading = False
        self.browser.grid_remove()
        self.drawBrowser(browser)

    def select(self, e: Event):
        clickedWidget = e.widget
        # IMPORTANT: for some reason the act of converting cget to a string
        # makes it work for comparisons
        if str(clickedWidget.cget('background')) == SELECTED_LABEL_BG_HEX:
            clickedWidget.configure(background = self.background)
        else:
            clickedWidget.configure(background = SELECTED_LABEL_BG_HEX)
