import asyncio
import threading
import time
import tkintools
import db
import ttkbootstrap as ttk
import records
from pathlib import Path
from tkinter.font import BOLD, ITALIC
from tkinter import *
from typing import Callable
from aplayer import Aplayer
from tkinter import filedialog
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from config import *
from youtubesearchpython.__future__ import VideosSearch


ARTISTS='artists'
ALBUMS='albums'
TRACKS='tracks'
PLAYLISTS='playlists'
PLAYLIST_SONGS='playlist_songs'
PLAY = 'play'
QUEUE = 'queue'
SEARCH_RESULTS = 'search_results'
SEARCH_MODE = 0
STREAM_MODE = 1
STREAM_DOWNLOAD_MODE = 2
DOWNLOAD_MODE = 3

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
        self.entryBar = None
        self.entry_label = None
        self.entry = None
        self.entry_mode = SEARCH_MODE
        self.libToolsVisible = False
        self.entryBarVisible = False
        self.updating_entry_label = False
        self.selectedContent = []
        self.current_file = ''
        self.current_duration = ''
        self.playing_text = 'Now playing:'
        self.status = None
        self.adding_music_label = None
        self.downloading = False
        self.__overriding_status = False
        Aplayer.player.observe_property('path', self.observe_title)
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
        self.drawStatus()
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

    def drawStatus(self):
        self.status = Frame(self.root, width=PANE_WIDTH)
        self.status.columnconfigure(1, weight=0)
        self.status.columnconfigure(0, weight=1)
        self.status_text = ttk.Label(self.status, 
            font=(DEFAULT_FONT_FAMILY, 12), padding='4 4 0 4',
            background=COLOUR_DICT['bg'])
        self.status_time = ttk.Label(self.status, 
            font=(DEFAULT_FONT_FAMILY, 12), padding='0 4 4 4')

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
            self.entry.focus_force()
        else:
            self.entryBar.grid_remove()
            self.root.focus_force()
        self.entryBarVisible = not self.entryBarVisible

    def finish_adding_music(self):
        self.adding_music_label.configure(
            text='done!', background=COLOUR_DICT['dark'])
        self.root.update()
        time.sleep(1)
        self.adding_music_label.grid_remove()

    def add_folders(self, e: Event, AAT_structure: bool):
        directory = filedialog.askdirectory()
        if not directory == '':
            self.adding_music_label.configure(text='adding...')
            self.adding_music_label.grid(row=2, column=2)
            self.root.update()
            records.addFolder(directory, AAT_structure)
            threading.Thread(target=self.finish_adding_music).start()

    def genLibTools(self):
        self.libTools = Frame(self.frame)
        self.libTools.configure(background=self.background)
        add_library = tkintools.LabelButton(
            self.libTools,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            clickFunc=lambda e, AAT=True: self.add_folders(e, AAT),
            text='[add library]',
            font=(DEFAULT_FONT_FAMILY, 12, BOLD)
        )
        add_songs = tkintools.LabelButton(
            self.libTools,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            clickFunc=lambda e, AAT=False: self.add_folders(e, AAT),
            text='[add songs]',
            font=(DEFAULT_FONT_FAMILY, 12, BOLD)
        )
        self.adding_music_label = ttk.Label(self.libTools,
            font=(DEFAULT_FONT_FAMILY, 12))
        padx = 7
        add_library.grid(column=0, row=2, sticky=S, padx=padx)
        add_songs.grid(column=1, row=2, sticky=S, padx=padx)

    def genSearchButton(self):
        buttonFrame = Frame(self.entryBar)
        buttonFrame.configure(
            highlightcolor=COLOUR_DICT['light'],
            highlightbackground = COLOUR_DICT['light'],
            highlightthickness = 1
        )
        button = tkintools.LabelButton(
            buttonFrame, text='search',
            pady=0, clickFunc=self.search_hit,
            font=(DEFAULT_FONT_FAMILY,13, BOLD)
        )
        button.bind('<Button-3>', self.__alter_search_button)
        button.grid()
        return buttonFrame

    def genEntryBar(self):
        self.entryBar = Frame(self.frame)
        self.entryBar.configure(background=self.background)
        queue_button = tkintools.LabelButton(
            self.entryBar,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['dark'],
            clickFunc=lambda e, queue=True: self.search_hit(e, queue),
            text='[queue]',
            font=(DEFAULT_FONT_FAMILY, 12, BOLD)
        )
        search_button = self.genSearchButton()
        self.entry_label = ttk.Label(
            self.entryBar, background=self.background,
            font = (DEFAULT_FONT_FAMILY, 12))
        self.entry = Entry(self.entryBar)
        self.entry.grid(row=0,column=0, padx=7)
        self.entry.configure(
            font = (DEFAULT_FONT_FAMILY,13),
            background=COLOUR_DICT['bg'])
        self.entry.bind(
            '<Return>', lambda e: self.search_hit(e))
        self.entry.insert(0, '1. type 2. hit Enter')
        search_button.grid(row=0,column=1, sticky=S)
        queue_button.grid(row=0,column=2, sticky=S)

    def __alter_search_button(self, e: Event):
        if self.entry_mode == SEARCH_MODE:
            self.entry_mode = STREAM_MODE
            e.widget.configure(text='stream')
        elif self.entry_mode == STREAM_MODE:
            self.entry_mode = STREAM_DOWNLOAD_MODE
            e.widget.configure(text='stream + download')
        elif self.entry_mode == STREAM_DOWNLOAD_MODE:
            self.entry_mode = DOWNLOAD_MODE
            e.widget.configure(text='download')
        else:
            self.entry_mode = SEARCH_MODE
            e.widget.configure(text='search')

    async def __search_yt_from_entry(self):
        videosSearch = VideosSearch(self.entry.get(), limit = 1)
        videosResult = await videosSearch.next()
        return [videosResult['result'][0]['link'],
                videosResult['result'][0]['title']]

    def __stream(self, queue: bool = False, download = False):
        try:
            entry_text = self.entry.get()
            if entry_text.startswith('https://'):
                threading.Thread(target=Aplayer.loadfile, 
                    args=(self.entry.get(), queue, '', download)).start()
                return Aplayer.scrape_title(entry_text)
            else:
                loop = asyncio.new_event_loop()
                link, title = loop.run_until_complete(self.__search_yt_from_entry())
                threading.Thread(target=Aplayer.loadfile,
                    args=(link, queue, title, download)).start()
                return title
        except Exception:
            pass
    
    def __link_downloaded(self, data):
        artist, track, _, _ = data
        dl_path = DOWNLOAD_PATH + os.sep + artist + os.sep + track
        full_path = "{}.{}".format(dl_path, DOWNLOADS_CODEC)
        return path_exists(full_path)

    def __download_and_display(self):
        link = self.entry.get()
        if link.startswith('https://'):
            title = Aplayer.get_title_from_file(link, '', True)
        else:
            loop = asyncio.new_event_loop()
            link, title_rough = loop.run_until_complete(self.__search_yt_from_entry())
            title = Aplayer._validate_title(title_rough)
        data = Aplayer.get_artist_track_trackNum(title)
        if not self.__link_downloaded(data):
            threading.Thread(target=self.put_dl_percent).start()
            Aplayer.download(link, data)
        else:
            # TODO: add new label to row saying that the file exists
            pass
        
    def put_dl_percent(self):
        if self.downloading is True:
            time.sleep(2)
            if self.downloading is True:
                return
        self.downloading = True
        self.entry_label.config(text='...')
        self.entry_label.grid(row=0, column=3, sticky=E)
        self.root.update()
        while len(Aplayer._download_queue_titles) == 0:
            time.sleep(0.01)
            if Aplayer.downloading_audio is True and len(Aplayer._download_queue_titles) > 0:
                break
        while len(Aplayer._download_queue_titles) > 0:
            self.entry_label.config(text='downloading...' + str(Aplayer._current_download_percent) + '%')
            self.root.update()
            time.sleep(0.001)
            if Aplayer._current_download_percent == 100:
                time.sleep(1)
                if (Aplayer._current_download_percent == 0
                        or Aplayer._current_download_percent == 100):
                    break
        self.downloading = False
        self.entry_label.grid_remove()
        self.root.update()            
    
    def search_hit(self, e: Event = None, queue = False):
        if self.entry_mode == SEARCH_MODE:
            self.search_library()
        elif self.entry_mode == STREAM_MODE:
            title = self.__stream(queue)
            if self.status_text.cget('text') == '':
                text = 'queuing... \"' + title + '\"' if queue else 'loading...'
                self.status_text.configure(text=text)
            else:
                if queue is True:
                    threading.Thread(
                        target=self.__override_status,
                        args=('queuing... \"' + title + '\"',)).start()
        elif self.entry_mode == STREAM_DOWNLOAD_MODE:
            threading.Thread(target=self.__stream, args=(queue, True)).start()
            threading.Thread(target=self.__download_and_display).start()
            if self.status_text.cget('text') == '':
                self.status_text.configure(text='loading and downloading...')
        elif self.entry_mode == DOWNLOAD_MODE:
            threading.Thread(target=self.__download_and_display).start()

        self.root.update()
            

    def draw_browser_subtitle(self, text, row, browser):
        ttk.Label(
            browser, text=text, background=self.background, 
            padding='0 0 0 10',
            font=(DEFAULT_FONT_FAMILY,14,UNDERLINE)).grid(sticky=W,row=row)

    def __search_playlists(self, insert_row, query, browser):
        pl_filenames = Aplayer.get_playlist_names()
        playlist_results = [
            name for name in pl_filenames
            if query.casefold() in map(str.casefold, Path(name).stem)
        ]
        i = insert_row
        if len(playlist_results) > 0:
            self.draw_browser_subtitle(PLAYLISTS, i, browser)
            i +=1
        self.loading = True
        for name in playlist_results:   
            self.genBrowserLabel(
                i, Path(name).stem, PLAYLISTS,
                lambda e, pl=name: self.__go_to_playlist_songs(e, pl),
                browser=browser)
            self.genBrowserButton(i, browser=browser)
            i += 1
        return i

    def __search_artists(self, insert_row, query, browser):
        artist_results = dbLink.search_artists(query)
        i = insert_row
        if len(artist_results) > 0:
            self.draw_browser_subtitle(ARTISTS, i, browser)
            i +=1
        for artist_tuple in artist_results:
            label = self.genBrowserLabel(
                i, artist_tuple[0], ARTISTS,self.loadAlbums, browser)
            label_data = artist_tuple[0]
            self.genBrowserButton(
                i, browser=browser,
                clickFunc=(
                    lambda e, data=label_data, label=label:
                        self.play(e, data, label)))
            i+=1
        return i

    def __search_albums(self, insert_row, query, browser):
        album_results = dbLink.search_albums(query)
        i = insert_row
        if len(album_results) > 0:
            self.draw_browser_subtitle(ALBUMS, i, browser)
            i +=1
        for album_tuple in album_results:
            album = album_tuple[0]
            artist = album_tuple[1]
            label = self.genBrowserLabel(
                i, album + ' | ' + artist, ALBUMS, 
                lambda e, artist=artist: self.loadTracks(e, artist), browser)
            label_data = album + '|' + artist
            self.genBrowserButton(
                i, browser=browser,
                clickFunc=(
                    lambda e, data=label_data, label=label:
                        self.play(e, data, label)))
            i += 1
        return i

    def __search_tracks(self, insert_row, query, browser):
        track_results = dbLink.search_tracks(query)
        i = insert_row
        if len(track_results) > 0:
            self.draw_browser_subtitle(TRACKS, i, browser)
            i +=1
        for tuple in track_results:
            label = self.genBrowserLabel(
                i, tuple[0], TRACKS,
                lambda e, file=tuple[1]:
                    self.play(e, file), browser)
            self.genBrowserButton(
                i, browser=browser,
                clickFunc=(
                    lambda e, data=tuple[1], label=label:
                        self.play(e, data, label)))
            i+=1
        return i       



    def search_library(self):
        query = self.entry.get()
        if self.loading is True:
            return         
        self.updateSubheader(SEARCH_RESULTS, ' Search results for: ' + query)
        browser = self.genBrowser()
        i = 0
        i = self.__search_playlists(i, query, browser)
        i = self.__search_artists(i, query, browser)
        i = self.__search_albums(i, query, browser)
        i = self.__search_tracks(i, query, browser)
        self.browser.grid_remove()
        self.drawBrowser(browser)
        
    def __override_status(self, text):
        """
        Temporarily override the status bar text.
        Usage: threading.Thread(target=self.__override_status).start()
        Then update self.status_text.
        """
        self.status_text.configure(text=text)
        time.sleep(1)
        self.status_text.configure(text=self.current_file)

    def seek(self, e, seconds):
        threading.Thread(target=Aplayer.seek, args=(seconds,)).start()
        Aplayer._mpv_wait()
        self.__update_status_time()
    
    def drawControls(self):
        self.controls = Frame(self.frame)
        self.controls.grid(row=4, pady=5, rowspan=1)
        self.controls.configure(background=self.background)
        seek_pos = self.genControlButton(
            clickFunc=lambda e, t=10: self.seek(e, t),
            text=' ++> '   
        )
        seek_neg = self.genControlButton(
            clickFunc=lambda e, t=-10: self.seek(e, t),
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

    def observe_title(self, path, v):
        if self.status is None:
            return
        if v is None:
            self.current_file = ''
            self.current_duration = ''
            self.status.grid_remove()
        else:
            self.status.grid(row=6)
            self.status_text.grid(column=0, row=0)
            self.status_time.grid(column=1, row=0)
            self.status.configure(background=COLOUR_DICT['bg'])
            if Aplayer.online_queue is True:
                self.current_file = Aplayer.get_title_from_file(v)
                self.playing_text = 'Now streaming:'
            else:
                self.current_file = Path(v).name
                self.playing_text = 'Now playing:'

            threading.Thread(target=self.monitor_pos, daemon=True).start()

    def get_time_pos(self):
        secs = Aplayer.get_time_pos()
        if secs < 0 or secs is None:
            return '00:00:00'
        else:
            return time.strftime("%H:%M:%S", time.gmtime(secs))

    def __update_status_time(self):
        if Aplayer.get_duration() >= 0:
            self.current_duration = time.strftime(
                        "%H:%M:%S", time.gmtime(Aplayer.get_duration()))
        self.status_time.configure(text=' | [{}/{}]'.format(
                            self.get_time_pos(), self.current_duration))

    def monitor_pos(self):
        self.status_text.configure(
            text='{} {}'.format(self.playing_text, self.current_file))
        self.status_time.configure(text=' | [{}/{}]'.format('00:00:00', '...?'))
        while not self.current_file == '':
            time.sleep(1)
            if self.__overriding_status is False:
                self.__update_status_time()
            self.root.update()

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
        
    def updateSubheader(self, new_page: str, subheader: str = ''):
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
        elif self.currentPage == SEARCH_RESULTS:
            text=subheader
        if len(text) > LeftPane.SUBHEADER_TEXT_MAX_WIDTH:
            text = text[0:LeftPane.SUBHEADER_TEXT_MAX_WIDTH-3] + '...'
        self.subheader.configure(text=text)

    def goBack(self, e: Event = None):
        if self.currentPage == TRACKS:
            self.loadAlbums()
        elif (self.currentPage == ALBUMS
                or self.currentPage == PLAYLISTS
                or self.currentPage == SEARCH_RESULTS):
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
        if text == '':
            self.strip_widget_text(e)
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
        for tuple in self.fetchedArtists:
            name = tuple[0]     
            l = self.genBrowserLabel(i, name, ARTISTS, self.loadAlbums)
            self.genBrowserButton(
                i,
                clickFunc=lambda e, data=name, label=l: self.play(e,data,label))
            i += 1
        if i == 0:
            txt = ttk.Text(self.browser, font=(DEFAULT_FONT_FAMILY, 15))
            txt.insert(INSERT, GUIDE_TEXT)
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
    
    def loadTracks(self, e: Event = None, artist: str = ''):
        """Will load tracks into the browser.

        Args:
            e (Event, optional): The event that of the calling widget.
                Defaults to None.
            artist (str, optional): If specified, will set the
                chosenArtist of this LeftPane and 
                set the chosenAlbum as if it was returned from a search
                result, taking the first element of a split on the 
                album LabelButton text ' |'. Defaults to ''.
        """
        if self.loading is True:
            return
        text = ''
        if e != None:
            text = e.widget.cget('text')
            album = self.strip_widget_text(e)
        if artist != '':
            self.chosenArtist = artist
            album = album.split(' | ')[0]
        self.chosenAlbum = album
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
