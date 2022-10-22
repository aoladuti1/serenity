import asyncio
from concurrent.futures import thread
import math
import threading
import time
import tkintools
import db
import ttkbootstrap as ttk
import records
import screenery
from mastertools import Shield
from pathlib import Path
from tkinter.font import BOLD
from tkinter import *
from typing import Callable
from aplayer import Aplayer
from tkinter import filedialog
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from config import *
from youtubesearchpython.__future__ import VideosSearch


ARTISTS = 'artists'
ALBUMS = 'albums'
TRACKS = 'tracks'
PLAYLISTS = 'playlists'
PLAYLIST_SONGS = 'playlist_songs'
PLAYLISTS_TEXT = 'playlists'
PLAY = 'play'
QUEUE = 'queue'
SEARCH_RESULTS = 'search_results'
SEARCH_MODE = 0
STREAM_MODE = 1
STREAM_DOWNLOAD_MODE = 2
DOWNLOAD_MODE = 3

dbLink = db.DBLink()


class LeftPane:

    PAUSE_LABELS = ['||', '|>']
    BROWSER_BUTTON_PADX = 4
    BACK_TEXT = '<--'
    NO_BACK_TEXT = '---'
    SPECIAL_HEX = COLOUR_DICT['primary']
    DEFAULT_SUBHEADER = ' More...'
    STARTING_TEXT = ' ..starting..'
    QUEUING_TEXT = ' ..queuing..'
    ADDING_TEXT = ' ..adding..'
    SUBHEADER_TEXT_MAX_WIDTH = 999  # TODO make it fit 1080p, 2k and 4k

    def __init__(self, root: ttk.Window, status: tkintools.StatusBar):
        global _edge_pad
        self.root = root
        self.frame = None
        self.browser = None
        self.header = None
        self.subheader = None
        self.libTools = None
        self.loading = False
        self.controls = None
        self.control_buttons = None
        self.backButton = None
        self.pauseButton = None
        self.selCount = 0
        self.selWidget = None
        self.fetchedArtists = None
        self.fetchedAlbums = None
        self.fetchedTracksAndPaths = None
        self.chosenArtist = None  # should never be NoneType after init
        self.chosenAlbum = None  # should never be NoneType after init
        self.chosenPlaylist = None
        self.currentPage = ARTISTS
        self.subframe = None
        self.entryBar = None
        self.entry_label = None
        self.entry = None
        self.entry_mode = SEARCH_MODE
        self.popup_menu = None
        self.playlist_menu = None
        self.libToolsVisible = False
        self.entryBarVisible = False
        self.updating_entry_label = False
        self.selectedContent = {}
        self.current_file = ''
        self.duration_str = ''
        self.playing_text = 'Now playing:'
        self.status = status
        self.adding_music_label = None
        self.seekBar = None
        self.downloading = False
        self.monitoring_time = False
        self.__overriding_status = False
        Aplayer.player.observe_property('path', self.observe_title)
        _edge_pad = Shield.edge_pad()

    def drawAll(self):
        self.drawFrame()
        self.drawAllExceptFrame()

    def drawAllExceptFrame(self):
        self.drawSubheader()
        self.drawBackbutton()
        self.genLibTools()
        self.genEntryBar()
        self.genPlaylistMenu()
        self.genPopupMenu()
        self.drawControls()
        self.drawBrowser()
        self.loadArtists()

    def drawFrame(self):
        self.frame = Frame(
            self.root,
            width=Shield.max_pane())
        self.frame.grid(column=0, row=1, sticky='nsw', columnspan=1)
        self.frame.rowconfigure(5, weight=1)  # browser is stretchy!
        self.frame.columnconfigure(0, weight=1)


    def drawSubheader(self):
        self.subheader = tkintools.LabelButton(
            self.frame, text=LeftPane.DEFAULT_SUBHEADER,
            activeFG=COLOUR_DICT['info'],
            activeBG=COLOUR_DICT['bg'],
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['bg'],
            clickFunc=self.showHideExtras,
            unclickFunc=lambda e: self.controlRelease(e),
            font=(DEFAULT_FONT_FAMILY, 14))
        self.subheader.grid(column=0, row=0, sticky=W)

    def drawBackbutton(self):
        bbFrame = Frame(self.frame, padx=_edge_pad)
        bbFrame.grid(row=0, rowspan=1, sticky=NE)
        self.backButton = tkintools.LabelButton(
            bbFrame,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['bg'],
            clickFunc=self.goBack,
            text=LeftPane.NO_BACK_TEXT,
            font=(DEFAULT_FONT_FAMILY, 16, BOLD)
        )
        self.backButton.grid()

    def showHideExtras(self, e: Event = None):
        self.__showHideLibTools()
        self.__showHideEntryBar()

    def __showHideLibTools(self):
        if self.libToolsVisible is False:
            self.libTools.grid(row=2, pady=5)
        else:
            self.libTools.grid_remove()
        self.libToolsVisible = not self.libToolsVisible

    def __showHideEntryBar(self):
        if self.entryBarVisible is False:
            self.entryBar.grid(row=1, rowspan=1, pady=5)
            self.entry.focus_force()
        else:
            self.entryBar.grid_remove()
            self.root.focus_force()
        self.entryBarVisible = not self.entryBarVisible

    def finish_adding_music(self):
        self.adding_music_label.configure(text='done!')
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

    def entry_button_command(self, e: Event = None, queue: bool = False):
        threading.Thread(target=self.search_hit, args=(e, queue)).start()

    def genLibTools(self):
        self.libTools = Frame(self.frame)
        add_library = tkintools.LabelButton(
            self.libTools,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['bg'],
            clickFunc=lambda e, AAT=True: self.add_folders(e, AAT),
            text='[add library]',
            font=(DEFAULT_FONT_FAMILY, 12, BOLD)
        )
        add_songs = tkintools.LabelButton(
            self.libTools,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['bg'],
            clickFunc=lambda e, AAT=False: self.add_folders(e, AAT),
            text='[add songs]',
            font=(DEFAULT_FONT_FAMILY, 12, BOLD)
        )
        self.adding_music_label = ttk.Label(self.libTools,
                                            font=(DEFAULT_FONT_FAMILY, 12))
        padx = 7
        add_library.grid(column=0, row=2, sticky=S, padx=padx)
        add_songs.grid(column=1, row=2, sticky=S, padx=padx)

    def genEntryButton(self, text, queue=False):
        buttonFrame = Frame(self.entryBar)
        buttonFrame.configure(
            highlightcolor=COLOUR_DICT['light'],
            highlightbackground=COLOUR_DICT['light'],
            highlightthickness=1)
        button = tkintools.LabelButton(
            buttonFrame, text=text,
            pady=0,
            clickFunc=lambda e, q=queue: self.entry_button_command(e, q),
            font=(DEFAULT_FONT_FAMILY, 13, BOLD))
        if not queue:
            button.bind('<Button-3>', self.__alter_search_button)
        button.grid()
        return buttonFrame

    def genEntryBar(self):
        self.entryBar = Frame(self.frame)
        search_button = self.genEntryButton('search')
        queue_button = self.genEntryButton('queue', True)
        self.entry_label = ttk.Label(
            self.entryBar,
            font=(DEFAULT_FONT_FAMILY, 12))
        self.entry = Entry(self.entryBar)
        self.entry.grid(row=0, column=0, padx=7)
        self.entry.configure(
            font=(DEFAULT_FONT_FAMILY, 13),
            background=COLOUR_DICT['bg'])
        self.entry.bind(
            '<Return>', lambda e: self.search_hit(e))
        self.entry.insert(0, '1. type 2. hit Enter')
        search_button.grid(row=0, column=1, sticky=S)
        queue_button.grid(row=0, column=2, sticky=S, padx=6)

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
        try:
            videosSearch = VideosSearch(self.entry.get(), limit=1)
            videosResult = await videosSearch.next()
            return [videosResult['result'][0]['link'],
                    videosResult['result'][0]['title']]
        except Exception:
            return [None, None]

    def __stream(self, queue: bool = False, download=False):
        entry_text = self.entry.get()
        if entry_text.startswith('https://'):
            try:
                threading.Thread(
                    target=Aplayer.loadfile,
                    args=(self.entry.get(), queue, '', download)).start()
                return Aplayer.scrape_title(entry_text)
            except Exception:
                return None  # TODO: ERROR MSG
        else:
            loop = asyncio.new_event_loop()
            link, title = loop.run_until_complete(
                self.__search_yt_from_entry())
            if link is None:
                return  # TODO: ERROR MSG
            threading.Thread(target=Aplayer.loadfile,
                             args=(link, queue, title, download)).start()
            return title

    def __link_downloaded(self, data):
        artist, track, _, _ = data
        dl_path = DOWNLOAD_PATH + os.sep + artist + os.sep + track
        full_path = "{}.{}".format(dl_path, DOWNLOADS_CODEC)
        return path_exists(full_path)

    def __download_and_display(self):
        link = self.entry.get()
        if link.startswith('https://'):
            title = Aplayer.get_title_from_file(link, '', True)
            if title is None:
                return  # TODO: ERROR MSG
        else:
            loop = asyncio.new_event_loop()
            link, title_rough = loop.run_until_complete(
                self.__search_yt_from_entry())
            title = Aplayer._validate_title(title_rough)
            if title is None:
                return  # TODO: ERROR MSG
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
            if (Aplayer.downloading_audio is True
                    and len(Aplayer._download_queue_titles) > 0):
                break
        while len(Aplayer._download_queue_titles) > 0:
            self.entry_label.config(
                text='downloading...' + str(Aplayer._current_download_percent) + '%')
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

    def search_hit(self, e: Event = None, queue=False):
        if self.entry_mode == SEARCH_MODE:
            self.search_library()
        elif self.entry_mode == STREAM_MODE:
            title = self.__stream(queue)
            if self.status.label.cget('text') == '':
                text = 'queuing... \"' + title + '\"' if queue else 'loading...'
                self.status.label.configure(text=text)
            else:
                if queue is True:
                    threading.Thread(
                        target=self.__override_status,
                        args=('queuing... \"' + title + '\"',)).start()
        elif self.entry_mode == STREAM_DOWNLOAD_MODE:
            threading.Thread(target=self.__stream, args=(queue, True)).start()
            threading.Thread(target=self.__download_and_display).start()
            if self.status.label.cget('text') == '':
                self.status.label.configure(text='loading and downloading...')
        elif self.entry_mode == DOWNLOAD_MODE:
            threading.Thread(target=self.__download_and_display).start()

        self.root.update()

    def draw_browser_subtitle(self, text, row, browser):
        ttk.Label(
            browser, text=text,
            padding='0 0 0 10',
            font=(DEFAULT_FONT_FAMILY, 14, UNDERLINE)).grid(sticky=W, row=row)

    def __search_playlists(self, insert_row, query, browser):
        pl_titles = Aplayer.get_playlist_titles()
        playlist_results = [
            title for title in pl_titles
            if query.casefold() in map(str.casefold, title)]
        i = insert_row
        if len(playlist_results) > 0:
            self.draw_browser_subtitle(PLAYLISTS, i, browser)
            i += 1
        self.loading = True
        for title in playlist_results:
            label = self.genBrowserLabel(
                i, title, PLAYLISTS, title,
                self.__go_to_playlist_songs,
                browser=browser)
            self.genBrowserButton(
                i, browser=browser,
                clickFunc=(lambda e, d=title, l=label:
                           self.play(e, d, l)))
            i += 1
        return i

    def __search_artists(self, insert_row, query, browser):
        artist_results = db.DBLink().search_artists(query)
        i = insert_row
        if len(artist_results) > 0:
            self.draw_browser_subtitle(ARTISTS, i, browser)
            i += 1
        for artist_tuple in artist_results:
            name = artist_tuple[0]
            label = self.genBrowserLabel(
                i, name, ARTISTS, name, self.loadAlbums, browser)
            label_data = artist_tuple[0]
            self.genBrowserButton(
                i, browser=browser,
                clickFunc=(
                    lambda e, data=label_data, label=label:
                        self.play(e, data, label)))
            i += 1
        return i

    def __search_albums(self, insert_row, query, browser):
        album_results = db.DBLink().search_albums(query)
        i = insert_row
        if len(album_results) > 0:
            self.draw_browser_subtitle(ALBUMS, i, browser)
            i += 1
        for album_tuple in album_results:
            album = album_tuple[0]
            artist = album_tuple[1]
            data = album + '|' + artist
            label = self.genBrowserLabel(
                i, album + ' | ' + artist, ALBUMS, data,
                lambda e, artist=artist: self.loadTracks(e, artist), browser)
            self.genBrowserButton(
                i, browser=browser,
                clickFunc=(
                    lambda e, data=data, label=label:
                        self.play(e, data, label)))
            i += 1
        return i

    def __search_tracks(self, insert_row, query, browser):
        track_results = db.DBLink().search_tracks(query)
        i = insert_row
        if len(track_results) > 0:
            self.draw_browser_subtitle(TRACKS, i, browser)
            i += 1
        for tuple in track_results:
            label = self.genBrowserLabel(
                i, tuple[0], TRACKS, tuple[1],
                self.play, browser)
            self.genBrowserButton(
                i, browser=browser,
                clickFunc=(
                    lambda e, data=tuple[1], label=label:
                        self.play(e, data, label)))
            i += 1
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
        Then update self.status.label.
        """
        self.status.label.configure(text=text)
        time.sleep(1)
        self.status.label.configure(text=self.current_file)
        self.root.update()

    def seek(self, e, seconds):
        threading.Thread(target=Aplayer.seek, args=(seconds,)).start()
        Aplayer._mpv_wait()
        self.__update_status_time()


    def drawControls(self):
        self.controls = Frame(self.frame)
        self.controls.grid(row=3, pady=5, rowspan=1)
        self.control_buttons = Frame(self.controls)
        self.control_buttons.grid(row=0)
        shuffle = self.genControlButton(
            clickFunc=lambda e: Aplayer.shuffle(), text='¿?',
            unclickFunc=self.toggle_highlight)
        repeat = self.genControlButton(
            clickFunc=lambda e: Aplayer.change_loop(), text='{0}',
            unclickFunc=self.highlight_replay)
        seek_pos = self.genControlButton(
            clickFunc=lambda e, t=10: self.seek(e, t), text='++>')
        seek_neg = self.genControlButton(
            clickFunc=lambda e, t=-10: self.seek(e, t), text='<++')
        pause = self.genControlButton(
            clickFunc=lambda e: self.controlThreader(e, Aplayer.pauseplay),
            text='|>')
        count = self.cgrid([shuffle, seek_neg, pause, seek_pos, repeat])
        self.seekBar = tkintools.SeekBar(self.controls)
        self.pauseButton = pause
        self.seekBar.grid(row=1)
        self.seekBar.bind('<Button-1>', lambda e: self.__update_status_time)
        threading.Thread(target=self.monitorPlaystate, daemon=True).start()
       

    def cgrid(self, controls: list):
        i = 0
        for control in controls:
            control.grid(
                column=i, row=0, sticky=S, pady=5, rowspan=1, columnspan=1)
            self.control_buttons.columnconfigure(i, weight=1)
            i += 1
        return i


    def monitorPlaystate(self):
        while True:
            try:
                self.pauseButton.configure(
                    text=LeftPane.PAUSE_LABELS[int(Aplayer.is_paused())])
            except Exception:
                pass  # tkinter complains about the threading but i don't care
            time.sleep(1)

    def observe_title(self, path, file):
        if file is None:
            self.current_file = ''
            self.duration_str = ''
            self.status.grid_remove()
        else:

            if Aplayer.online_queue is True:
                self.current_file = Aplayer.get_title_from_file(file)
                self.playing_text = 'Now streaming:'
            else:
                self.current_file = Path(file).name
                self.playing_text = 'Now playing:'
            self.status.grid(row=5)
            self.status.label.grid(column=0, row=0)
            self.status.time.grid(column=1, row=0)
            self.status.configure(background=COLOUR_DICT['bg'])
            self.status.label.configure(
                text='{} {}'.format(self.playing_text, self.current_file))
            if not self.monitoring_time:
                self.monitoring_time = True
                threading.Thread(target=self.monitor_pos, daemon=True).start()
            

    def toggle_highlight(self, e: Event):
        states = [COLOUR_DICT['primary'], COLOUR_DICT['info']]
        e.widget.state = 1 - e.widget.state
        self.controlRelease(e)
        e.widget.configure(foreground=states[e.widget.state])

    def highlight_replay(self, e: Event):
        states = [
            COLOUR_DICT['primary'], COLOUR_DICT['light'], COLOUR_DICT['info']]
        self.controlRelease(e)
        e.widget.state += 1
        state = e.widget.state
        if state > len(states) - 1:
            e.widget.state = 0
            state = 0
        if state == 1:
            e.widget.configure(text='{1}')
        elif state == 2:
            e.widget.configure(text='{+}')
        else:
            e.widget.configure(text='{0}')
        e.widget.configure(foreground=states[state])

    def str_pos(self, secs: float):
        if secs < 0 or secs is None:
            return '00:00:00'
        else:
            return time.strftime("%H:%M:%S", time.gmtime(secs))

    def __update_status_time(self):
        duration = math.floor(Aplayer.get_duration())
        secs = Aplayer.get_time_pos()
        if duration < 0:
            prcnt = 0
        else:
            prcnt = math.ceil(100 * secs / duration)
        str_pos = self.str_pos(secs)
        if duration >= 0:
            self.duration_str = time.strftime(
                "%H:%M:%S", time.gmtime(duration))
        self.status.time.configure(text=' | [{}/{}]'.format(
            str_pos, self.duration_str))
        self.seekBar.pos.configure(text = str_pos)
        if self.duration_str != '':
            self.seekBar.duration.configure(text = self.duration_str)
        else:
            self.seekBar.duration.configure(text='--:--:--')
        self.seekBar.new_position.set(prcnt)
        self.root.update()

    def monitor_pos(self):
        self.status.time.configure(
            text=' | [{}/{}]'.format('00:00:00', '...?'))
        self.seekBar.pos.configure(text='00:00:00')
        self.seekBar.duration.configure(text='--:--:--')
        self.root.update()
        while not self.current_file == '':
            time.sleep(0.4)
            if self.__overriding_status is False:
                self.__update_status_time()
            self.monitoring_time = False
        self.root.update()

    def genControlButton(self, text: str, clickFunc: Callable,
                         unclickFunc: Callable = None):
        if unclickFunc is None:
            func = self.controlRelease
        else:
            func = unclickFunc
        return tkintools.LabelButton(
            self.control_buttons,
            onEnterFunc=self.wrapSquares,
            onLeaveFunc=self.unwrapSquares,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['bg'],
            clickFunc=clickFunc,
            unclickFunc=func,
            text=text,
            padx=30,
            font=(DEFAULT_FONT_FAMILY, 16, BOLD)
        )

    def controlThreader(self, e: Event, function):
        threading.Thread(
            target=self.controlHandler,
            args=(function,)
        ).start()

    def controlHandler(self, function):
        if (function is not None):
            function()

    def controlRelease(self, e: Event):
        e.widget.configure(foreground=COLOUR_DICT['primary'])
        self.unwrapSquares(e)

    def genBrowser(self):
        global _edge_pad
        _edge_pad = Shield.edge_pad()
        if not Shield.expanded:
            height = int(0.7 * Shield.drawn_height)
        else:
            height = int(0.8 * Shield.drawn_height)
        if Shield.small_screen is True:
                height *=  1.4 * screenery.primary_geometry()[1] / 2160
                if Shield.expanded is True:
                    height *= 1.2
        browser = ScrolledFrame(
            self.frame, autohide=True,
            width=Shield.max_pane(),
            height=height
        )
        browser.columnconfigure(0, weight=1)
        browser.columnconfigure(1, weight=0)
        return browser

    def drawBrowser(self, browser=None):
        if browser is None:
            self.browser = self.genBrowser()
        else:
            self.browser.grid_remove()
            self.browser = browser
        self.loading = False
        self.browser.grid(row=4, sticky=NW, columnspan=1, rowspan=1)
        self.root.update()

    def flipBrowserButton(self, e):
        text_states = ['play', 'queue']
        button = e.widget
        button.configure(text=text_states[int(not e.widget.state)])
        button.state = int(not button.state)

    def genBrowserButton(self, row: int, text: str = PLAY,
                         clickFunc=None, browser=None):
        if browser is None:
            browser = self.browser
        buttonFrame = Frame(browser)
        buttonFrame.configure(
            highlightcolor=COLOUR_DICT['primary'],
            highlightbackground=COLOUR_DICT['primary'],
            highlightthickness=1
        )
        buttonFrame.grid(
            column=1, row=row, rowspan=1, ipady=0,
            padx=(_edge_pad, _edge_pad), pady=(0, 9), sticky=E
        )
        button = tkintools.LabelButton(
            buttonFrame, text=text, padx=LeftPane.BROWSER_BUTTON_PADX,
            pady=0, clickFunc=clickFunc, width=5
        )
        button.bind('<Button-3>', self.flipBrowserButton)
        button.grid()
        return buttonFrame

    def genBasicBrowserButton(self, row: int, text: str = 'open',
                              clickFunc=None, browser=None):
        if browser is None:
            browser = self.browser
        buttonFrame = Frame(browser)
        buttonFrame.configure(
            highlightcolor=COLOUR_DICT['primary'],
            highlightbackground=COLOUR_DICT['primary'],
            highlightthickness=1
        )
        buttonFrame.grid(
            column=1, row=row, rowspan=1, ipady=0,
            padx=(_edge_pad, _edge_pad), pady=(0, 9), sticky=E
        )
        button = tkintools.LabelButton(
            buttonFrame, text=text, padx=LeftPane.BROWSER_BUTTON_PADX,
            pady=0, clickFunc=clickFunc
        )
        button.grid()
        return buttonFrame

    def genBrowserLabel(self, row: int, text: str, label_type: str,
                        data: str, dblClickFunc=None, browser=None):
        if browser is None:
            browser = self.browser
        b_label = tkintools.TypedLabel(
            browser,
            label_type=label_type,
            text=" " + text,
            data=data,
            bootstyle='info',
            # makes the highlight bar go fully across
            width=browser.cget('width')
        )
        b_label.grid(column=0, row=row, rowspan=1, sticky=NW)
        b_label.bind('<Button-1>', self.select)
        b_label.bind('<Double-Button-1>', dblClickFunc)
        b_label.bind('<Button-3>', self.do_popup)
        return b_label

    def genPopupMenu(self):
        self.popup_menu = self.DropDownMenu()

    def genPlaylistMenu(self):
        self.playlist_menu = Menu(self.frame, tearoff=0,
                                  font=(DEFAULT_FONT_FAMILY, 12))
        for title in Aplayer.get_playlist_titles():
            self.playlist_menu.add_command(
                label=title, command=lambda t=title: self.__add_to_playlist(t))

    def DropDownMenu(self):
        m = Menu(self.frame, tearoff=0)
        m.configure(background=COLOUR_DICT['dark'],
                    activeforeground=COLOUR_DICT['info'])
        m.configure(font=(DEFAULT_FONT_FAMILY, 12))
        m.add_command(
            label="Play all",
            command=lambda queue=False: self.play_all(queue))
        m.add_command(
            label="Queue all",
            command=lambda queue=True: self.play_all(queue))
        m.add_separator()
        m.add_cascade(label="Add to playlist...", menu=self.playlist_menu)
        m.add_separator()
        m.add_command(label="Clear selection", command=self.clear_selection)
        return m

    def play_all(self, queue_all):
        threading.Thread(target=self.__play_all, args=(queue_all,)).start()

    def do_popup(self, e: Event):
        if e.widget.cget('text') == PLAYLISTS_TEXT:
            return
        self.select(e, force=True)
        self.genPlaylistMenu()
        m = self.popup_menu
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    def __play_all(self, queue_all):
        queue = queue_all
        i = 0
        link = db.DBLink()
        for key, widget in self.selectedContent.items():
            if widget.label_type == TRACKS:
                self.__play_track(key, queue)
            elif widget.label_type == ALBUMS:
                self.__play_album(key, queue, link)
            elif widget.label_type == ARTISTS:
                self.__play_artist(key, queue, link)
            elif widget.label_type == PLAYLISTS:
                self.__play_playlist(key, queue)
            elif widget.label_type == PLAYLIST_SONGS:
                self.__play_playlist_track(key, True)
                if queue is False:
                    if Aplayer.is_paused():
                        Aplayer.pauseplay()
            elif widget.label_type is None:
                continue
            prefix = ' [{}]'.format(i + 1)
            threading.Thread(
                target=self._temp_mark_label,
                args=(widget, queue, prefix), daemon=True).start()
            queue = True
            i += 1

    def __add_to_playlist(self, playlist_title):
        with open(Aplayer.playlist_path(playlist_title), mode='a') as playlist:
            i = 0
            for key, widget in self.selectedContent.items():
                if widget.label_type == TRACKS:
                    playlist.write(widget.cget('text') + '\n')
                elif widget.label_type == ALBUMS:
                    for file in self.__get_album_filenames(key):
                        playlist.write(file + '\n')
                elif widget.label_type == ARTISTS:
                    for file in self.__get_artist_filenames(key):
                        playlist.write(file + '\n')
                elif widget.label_type == PLAYLISTS:
                    with open(Aplayer.playlist_path(key), mode='r') as sel:
                        for file in sel.readlines():
                            playlist.write(file)
                elif widget.label_type == PLAYLIST_SONGS:
                    playlist.write(key.split('|')[0] + '\n')
                elif widget.label_type is None:
                    continue
                prefix = ' [{}] {}'.format(i + 1, '..adding..')
                threading.Thread(
                    target=self._temp_mark_label,
                    args=(widget, False, prefix, True), daemon=True).start()
                i += 1

    def wrapSquares(self, e: Event):
        text = e.widget.cget('text')
        e.widget.configure(text='[' + text + ']')

    def unwrapSquares(self, e: Event):
        text = e.widget.cget('text')
        if text.startswith('['):
            e.widget.configure(text=text[1:-1])

    def updateSubheader(self, new_page: str, subheader: str = ''):
        if self.currentPage != new_page:
            self.selectedContent.clear()
        self.currentPage = new_page
        if self.currentPage != ARTISTS:
            self.backButton.configure(text=LeftPane.BACK_TEXT)
        else:
            self.backButton.configure(text=LeftPane.NO_BACK_TEXT)
        if self.currentPage == ARTISTS:
            text = LeftPane.DEFAULT_SUBHEADER
        elif self.currentPage == ALBUMS:
            text = ">> {}".format(self.chosenArtist)
        elif self.currentPage == TRACKS:
            text = ">> {}\\{}".format(self.chosenArtist, self.chosenAlbum)
        elif self.currentPage == PLAYLISTS:
            text = ">> {}".format(PLAYLIST_FOLDER_NAME)
        elif self.currentPage == PLAYLIST_SONGS:
            text = ">> {}\\{}".format(
                PLAYLIST_FOLDER_NAME, self.chosenPlaylist)
        elif self.currentPage == SEARCH_RESULTS:
            text = subheader
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
        playlist_titles = Aplayer.get_playlist_titles()
        title_count = len(playlist_titles)
        for title in playlist_titles:
            label = self.genBrowserLabel(
                i, title, PLAYLISTS, title,
                self.__go_to_playlist_songs,
                browser=browser)
            self.genBrowserButton(
                i, browser=browser,
                clickFunc=(lambda e, d=title, l=label:
                           self.play(e, d, l)))
            if e is not None:
                self.__show_label_load_stats(
                    e, ' ' + PLAYLISTS_TEXT, i, title_count)
            i += 1
        self.drawBrowser(browser)

    def __show_label_load_stats(
            self, e: Event, text: str, count: int, max: int):
        if text == '':
            self.strip_widget_text(e)
        e.widget.configure(text="{} [{:.1f}%]".format(text, 100 * count / max))
        self.root.update()

    def __go_to_playlist_songs(self, e: Event):
        if self.loading is True:
            return
        playlist_title = self.strip_widget_text(e)
        self.chosenPlaylist = playlist_title
        self.updateSubheader(PLAYLIST_SONGS)
        browser = self.genBrowser()
        playlist_file = Aplayer.playlist_path(playlist_title)
        chosen_playlist_files = open(playlist_file, 'r').readlines()
        playlist_length = len(chosen_playlist_files)
        i = 0
        for path in chosen_playlist_files:
            data = "{}|{}".format(path, i)
            label = self.genBrowserLabel(
                i, Aplayer.get_title_from_file(path),
                PLAYLIST_SONGS, data, self.play, browser=browser)
            self.genBrowserButton(
                i, browser=browser,
                clickFunc=(lambda e, d=data, l=label:
                           self.play(e, d, l)))
            self.__show_label_load_stats(
                e, ' ' + playlist_title, i, playlist_length)
            i += 1
        self.drawBrowser(browser)

    def __play_track(self, FQFN, queue):
        threading.Thread(target=Aplayer.loadfile, args=(FQFN, queue)).start()

    def __play_playlist_track(self, FQFN_index, queue):
        FQFN, index = FQFN_index.split('|')
        if queue is True:
            self.__play_track(FQFN, queue=True)
        else:
            threading.Thread(
                target=Aplayer.loadlist,
                args=(self.chosenPlaylist, index, queue)).start()

    def __get_album_filenames(self, album_artist: str, custom_dblink=None):
        link = custom_dblink if custom_dblink is not None else dbLink
        album, artist = album_artist.split('|')
        return link.get_album_filenames(album, artist)

    def __play_album(self, album_artist, queue, custom_dblink=None):
        track_list = self.__get_album_filenames(album_artist, custom_dblink)
        threading.Thread(
            target=Aplayer.loadall, args=(track_list, queue)).start()

    def __get_artist_filenames(self, artist: str, custom_dblink=None):
        link = custom_dblink if custom_dblink is not None else dbLink
        return link.get_artist_filenames(artist)

    def __play_artist(self, artist, queue, custom_dblink=None):
        artist_list = self.__get_artist_filenames(artist, custom_dblink)
        threading.Thread(
            target=Aplayer.loadall, args=(artist_list, queue)).start()

    def __play_playlist(self, title, queue):
        if queue is False:
            threading.Thread(
                target=Aplayer.loadlist, args=(title,)).start()
        else:
            files = open(Aplayer.playlist_path(title), 'r').readlines()
            threading.Thread(
                target=Aplayer.loadall, args=(files, True)).start()

    def play(self, e: Event = None, data: str = None,
             external_label=None, queue_files=False):
        # this function needs at least one of data or external_label
        button = None
        _data = data
        if external_label is None:
            widget = e.widget
        else:
            button = e.widget
            widget = external_label
        if queue_files is False and button is not None:
            queue = button.state == 1
        else:
            queue = queue_files
        if data is None:
            _data = widget.data
        label_type = widget.label_type
        if label_type == TRACKS:
            self.__play_track(_data, queue)
        elif label_type == ALBUMS:
            self.__play_album(_data, queue)
        elif label_type == ARTISTS:
            self.__play_artist(_data, queue)
        elif label_type == PLAYLISTS:
            self.__play_playlist(_data, queue)
        elif label_type == PLAYLIST_SONGS:
            self.__play_playlist_track(_data, queue)
        threading.Thread(target=self._temp_mark_label,
                         args=(widget, queue), daemon=True).start()

    def _temp_mark_label(self, widget, queue, prefix='', prefix_overrides=False):
        old_fg = widget.cget('foreground')
        if str(old_fg) == str(LeftPane.SPECIAL_HEX):
            return
        old_text = widget.cget('text')
        if prefix_overrides is False:
            new_text = LeftPane.STARTING_TEXT if queue is False else LeftPane.QUEUING_TEXT
            new_text = prefix + new_text
        else:
            new_text = prefix
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
        if self.fetchedArtists is None:
            self.fetchedArtists = dbLink.get_artists()
        i = 0
        if Aplayer.get_number_of_playlists() > 0:
            pl = self.genBrowserLabel(
                i, PLAYLISTS_TEXT, None,
                PLAYLISTS_TEXT, self.__go_to_playlists)
            pl.configure(foreground=COLOUR_DICT['light'])
            self.genBasicBrowserButton(i, text="open")
            i += 1
        for tuple in self.fetchedArtists:
            name = tuple[0]
            al = self.genBrowserLabel(i, name, ARTISTS, name, self.loadAlbums)
            self.genBrowserButton(
                i,
                clickFunc=lambda e, d=name, al=al: self.play(e, d, al))
            i += 1
        if i == 0:
            txt = ttk.Text(self.browser, font=(DEFAULT_FONT_FAMILY, 15))
            txt.insert(INSERT, GUIDE_TEXT)
            txt.configure(
                background=self.background,
                highlightbackground=COLOUR_DICT['bg'], wrap=WORD)
            txt.grid(columnspan=2)

    def strip_widget_text(self, e: Event):
        text = e.widget.cget('text')
        if text.startswith(LeftPane.STARTING_TEXT):
            text = text[len(LeftPane.STARTING_TEXT):]
        elif text.startswith(LeftPane.QUEUING_TEXT):
            text = text[len(LeftPane.QUEUING_TEXT):]
        if text.endswith('%]'):
            text = text.rsplit(' [')[-1]
        return text.lstrip()

    def loadAlbums(self, e: Event = None):
        if self.loading is True:
            return
        if e is not None:
            self.chosenArtist = self.strip_widget_text(e)
        self.fetchedAlbums = dbLink.get_albums(self.chosenArtist)
        self.updateSubheader(ALBUMS)
        album_count = len(self.fetchedAlbums)
        browser = self.genBrowser()
        i = 0
        text = " " + self.chosenArtist
        for album_tuple in self.fetchedAlbums:
            label_data = album_tuple[0] + '|' + self.chosenArtist
            label = self.genBrowserLabel(
                i, album_tuple[0], ALBUMS,
                label_data, self.loadTracks, browser)
            self.genBrowserButton(
                i, browser=browser,
                clickFunc=(
                    lambda e, data=label_data, label=label:
                        self.play(e, data, label)))
            if e is not None:
                self.__show_label_load_stats(
                    e, text, i, album_count)
            i += 1
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
        if e is not None:
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
                i, tuple[0], TRACKS, tuple[1], self.play, browser)
            self.genBrowserButton(
                i, browser=browser,
                clickFunc=(lambda e, data=tuple[1], label=label:
                           self.play(e, data, label)))
            if e is not None:
                self.__show_label_load_stats(
                    e, text, i, song_count)
            i += 1
        self.loading = False
        self.browser.grid_remove()
        self.drawBrowser(browser)

    def clear_selection(self):
        for widget in self.browser.winfo_children():
            if not isinstance(widget, tkintools.TypedLabel):
                continue
            else:
                if self.selectedContent.pop(widget.data, None) is not None:
                    widget.config(background=COLOUR_DICT['bg'])
                if len(self.selectedContent) == 0:
                    break

    def select(self, e: Event, force: bool = False):
        clickedWidget = e.widget
        # IMPORTANT: for some reason the act of converting cget to a string
        # makes it work for comparisons
        if (str(clickedWidget.cget('background')) == SELECTED_LABEL_BG_HEX
                and force is False):
            clickedWidget.configure(background=COLOUR_DICT['bg'])
            self.selectedContent.pop(e.widget.data)
        else:
            clickedWidget.configure(background=SELECTED_LABEL_BG_HEX)
            self.selectedContent.update({e.widget.data: e.widget})