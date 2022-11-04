import time
from threading import Thread
from tkinter import (DISABLED, INSERT, NW, UNDERLINE, WORD, E, Event, Frame,
                     Menu, W)
from tkinter.font import BOLD

import screenery
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

import serenityapp.supertk as stk
from serenityapp.aplayer import Aplayer
from serenityapp.config import COLOUR_DICT, DEFAULT_FONT_FAMILY
from serenityapp.db import DBLink
from serenityapp.lang import L, rellipsis, wd_ls, wrap_dots
from serenityapp.mastertools import Shield

ARTISTS_ID = 0
ALBUMS_ID = 1
TRACKS_ID = 2
PLAYLISTS_ID = 3
PLAYLIST_SONGS_ID = 4
SEARCH_RESULTS_ID = 5

ADDING_WDLS = wd_ls(L['ADDING'])
ADDING_REL = rellipsis(L['ADDING'])
QUEUING_WDLS = wd_ls(L['QUEUING'])
STARTING_WDLS = wd_ls(L['STARTING'])
HIGHLIGHT_HEX = COLOUR_DICT['primary']
FIRST_SUBHEADER_TEXT = ' -> ' + rellipsis(L['MORE'])
DELETING_WD = wrap_dots(L['DELETING'])
PLAY_ALL_CAP = L['PLAY_ALL'].capitalize()
QUEUE_ALL_CAP = L['QUEUE_ALL'].capitalize()
CLEAR_SELECTION_CAP = L['CLEAR_SELECTION'].capitalize()
BACK_TEXT = '<--'
NO_BACK_TEXT = '---'

DELETING_HEX = '#ff4040'
SELECTED_LABEL_BG_HEX = '#1a1836'


class Browser(ScrolledFrame):

    BUTTON_TEXT_STATES = [L['PLAY'], L['QUEUE']]
    BUTTON_WIDTH = max(len(BUTTON_TEXT_STATES[0]), len(BUTTON_TEXT_STATES[1]))
    BUTTON_PADX = 4

    def __init__(self, master, **kw):

        if not Shield.expanded:
            height = int(2 * Shield.drawn_height / 3)
        else:
            height = int(0.8 * Shield.drawn_height)
        if Shield.small_screen is True:
            height *= 1.4 * screenery.primary_geometry()[1] / 2160
            if Shield.expanded is True:
                height *= 1.2
        width = Shield.max_pane()
        ScrolledFrame.__init__(
            self, master, autohide=True, width=width, height=height, **kw)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.popup_menu = None
        self.playlist_menu = None
        self.selection = {}
        self.playlists_in_selection = 0
        self.last_search_query = ''
        global _edge_pad
        _edge_pad = Shield.edge_pad()

    def flip_button(self, e):
        text_states = Browser.BUTTON_TEXT_STATES
        button = e.widget
        button.configure(text=text_states[int(not e.widget.state)])
        button.state = int(not button.state)

    def add_label(self, row: int, text: str, label_type: str,
                  data: str, dblClickFunc=None):
        b_label = stk.TypedLabel(
            self, label_type=label_type, text=" " + text, data=data,
            bootstyle='info', width=self.cget('width'))
        b_label.grid(column=0, row=row, rowspan=1, sticky=NW)
        b_label.bind('<Button-1>', self.select)
        b_label.bind('<Double-Button-1>', dblClickFunc)
        b_label.bind('<Button-3>', self.do_popup)
        return b_label

    def add_button(self, row: int, text: str = L['PLAY'],
                   clickFunc=None, flippable=True):
        buttonFrame = Frame(self)
        buttonFrame.configure(
            highlightcolor=COLOUR_DICT['primary'],
            highlightbackground=COLOUR_DICT['primary'],
            highlightthickness=1)
        buttonFrame.grid(
            column=1, row=row, rowspan=1, ipady=0,
            padx=(_edge_pad, _edge_pad), pady=(0, 9), sticky=E)
        button = stk.LabelButton(
            buttonFrame, text=text, padx=Browser.BUTTON_PADX,
            pady=0, clickFunc=clickFunc)
        if flippable is True:
            button.bind('<Button-3>', self.flip_button)
            button.configure(width=Browser.BUTTON_WIDTH)
        button.grid()
        return buttonFrame

    def play_all(self, queue_all):
        Thread(target=self.__play_all, args=(queue_all,)).start()

    def __play_all(self, queue_all):
        queue = queue_all
        i = 0
        link = DBLink()
        songlist = []
        for key, widget in self.selection.items():
            if widget.label_type == TRACKS_ID:
                songlist.extend([key.split('|')[0]])
            elif widget.label_type == ALBUMS_ID:
                songlist.extend(self.__get_album_filenames(key, link))
            elif widget.label_type == ARTISTS_ID:
                songlist.extend(self.__get_artist_filenames(key, link))
            elif widget.label_type == PLAYLISTS_ID:
                songlist.extend(self.__get_playlist_filenames(key))
            elif widget.label_type == PLAYLIST_SONGS_ID:
                songlist.extend([key.split('|')[0]])
            elif widget.label_type is None:
                continue
            prefix = ' [{}]'.format(i + 1)
            self.temp_mark_label(widget, queue, prefix)
            i += 1
        Aplayer.loadall(songlist, queue_all)

    def do_popup(self, e: Event):
        if e.widget.cget('text') == L['PLAYLISTS']:
            return
        self.select(e, force=True)
        self.gen_playlist_menu()
        self.popup_menu = self.gen_popup_menu()
        m = self.popup_menu
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    def gen_playlist_menu(self):
        self.playlist_menu = Menu(self.master, tearoff=0,
                                  font=(DEFAULT_FONT_FAMILY, 12))
        for title in Aplayer.titles_of_playlists():
            self.playlist_menu.add_command(
                label=title, command=lambda t=title: self.__add_to_playlist(t))

    def gen_popup_menu(self):
        m = ttk.Menu(Librarian.frame, tearoff=0)
        m.configure(background=COLOUR_DICT['dark'],
                    activeforeground=COLOUR_DICT['info'])
        m.configure(font=(DEFAULT_FONT_FAMILY, 12))
        m.add_command(
            label=PLAY_ALL_CAP,
            command=lambda queue=False: self.play_all(queue))
        m.add_command(
            label=QUEUE_ALL_CAP,
            command=lambda queue=True: self.play_all(queue))
        m.add_separator()
        m.add_cascade(
            label=L['ADD_TO_PLAYLIST_CAP_REL'], menu=self.playlist_menu)
        if self.playlists_in_selection > 0:
            m.add_command(label=L['DELETE_PLAYLISTS_CAP_REL'],
                          command=self.delete_playlists)
        m.add_separator()
        m.add_command(label=CLEAR_SELECTION_CAP, command=self.clear_selection)
        return m

    def __add_to_playlist(self, playlist_title):
        with open(Aplayer.playlist_path(playlist_title), mode='a') as playlist:
            i = 0
            for key, widget in self.selection.items():
                if widget.label_type == TRACKS_ID:
                    playlist.write(widget.cget('text') + '\n')
                elif widget.label_type == ALBUMS_ID:
                    for file in self.__get_album_filenames(key):
                        playlist.write(file + '\n')
                elif widget.label_type == ARTISTS_ID:
                    for file in self.__get_artist_filenames(key):
                        playlist.write(file + '\n')
                elif widget.label_type == PLAYLISTS_ID:
                    with open(Aplayer.playlist_path(key), mode='r') as sel:
                        for file in sel.readlines():
                            playlist.write(file)
                elif widget.label_type == PLAYLIST_SONGS_ID:
                    playlist.write(key.split('|')[0] + '\n')
                elif widget.label_type is None:
                    continue
                prefix = ' [{}]{}'.format(i + 1, ADDING_WDLS)
                self.temp_mark_label(widget, False, prefix, True)
                i += 1

    def temp_mark_label(
            self, widget, queue, prefix='',
            prefix_overrides=False, fg=HIGHLIGHT_HEX, secs=1.25):
        """ Temporarily changes the text of a label. If queue is false
            and there is no prefix, it will have STARTING_WDLS prepended.
            If queue is True and there is no prefix it will have
            QUEUING_WDLS prepended. Otherwise, if prefix_overrides is False,
            the specified prefix will be prepended just before the
            starting/queuing text is prepended.
            If prefix_overrides is True, just the prefix is prepended. """
        Thread(target=self._temp_mark_label,
               args=(widget, queue, prefix, prefix_overrides, fg, secs),
               daemon=True).start()

    def _temp_mark_label(
            self, widget, queue, prefix, prefix_overrides, fg, secs):
        old_fg = widget.cget('foreground')
        if str(old_fg) == str(fg):
            return
        old_text = widget.cget('text')
        if prefix_overrides is False:
            new_text = STARTING_WDLS if queue is False else QUEUING_WDLS
            new_text = prefix + new_text
        else:
            new_text = prefix
        widget.configure(foreground=fg)
        widget.configure(text=new_text + old_text)
        Shield.root_update()
        time.sleep(secs)
        widget.configure(foreground=old_fg)
        widget.configure(text=old_text)

    def draw_subtitle(self, text, row):
        ttk.Label(
            self, text=text,
            padding='0 0 0 10',
            font=(DEFAULT_FONT_FAMILY, 14, UNDERLINE)).grid(sticky=W, row=row)

    def _search_playlists(self, insert_row, query):
        pl_titles = Aplayer.titles_of_playlists()
        playlist_results = [
            title for title in pl_titles
            if query.casefold() in title]
        i = insert_row
        if len(playlist_results) > 0:
            self.draw_subtitle(L['PLAYLISTS'], i)
            i += 1
        Librarian.loading = True
        for title in playlist_results:
            label = self.add_label(
                i, title, PLAYLISTS_ID, title,
                Librarian.load_playlist_songs)
            self.add_button(
                i, clickFunc=(lambda e, d=title, l=label:
                              self.play(e, d, l)))
            i += 1
        return i

    def _search_artists(self, insert_row, query):
        artist_results = DBLink().search_artists(query)
        i = insert_row
        if len(artist_results) > 0:
            self.draw_subtitle(L['ARTISTS'], i)
            i += 1
        for artist_tuple in artist_results:
            name = artist_tuple[0]
            label = self.add_label(
                i, name, ARTISTS_ID, name, Librarian.load_albums)
            label_data = artist_tuple[0]
            self.add_button(
                i, clickFunc=(
                    lambda e, data=label_data, label=label:
                        self.play(e, data, label)))
            i += 1
        return i

    def _search_albums(self, insert_row, query):
        album_results = DBLink().search_albums(query)
        i = insert_row
        if len(album_results) > 0:
            self.draw_subtitle(L['ALBUMS'], i)
            i += 1
        for album_tuple in album_results:
            album = album_tuple[0]
            artist = album_tuple[1]
            data = album + '|' + artist  # note the difference 2 lines down
            label = self.add_label(
                i, album + ' | ' + artist, ALBUMS_ID, data,
                lambda e, artist=artist: Librarian.load_tracks(e, artist))
            self.add_button(
                i, clickFunc=(
                    lambda e, data=data, label=label:
                        self.play(e, data, label)))
            i += 1
        return i

    def _search_tracks(self, insert_row, query):
        track_results = DBLink().search_tracks(query)
        i = insert_row
        if len(track_results) > 0:
            self.draw_subtitle(L['TRACKS'], i)
            i += 1
        for tuple in track_results:
            label = self.add_label(
                i, tuple[0], TRACKS_ID, tuple[1], self.play)
            self.add_button(
                i, clickFunc=(
                    lambda e, data=tuple[1], label=label:
                        self.play(e, data, label)))
            i += 1
        return i

    def delete_playlists(self):
        widgets = []
        for data, widget in self.selection.items():
            if widget.label_type != PLAYLISTS_ID:
                continue
            widgets.append(widget)
            Aplayer.delete_playlist(data)
        for widget in widgets:
            self.temp_mark_label(
                widget, False, DELETING_WD, True, DELETING_HEX)
        Librarian.refresh_page()

    def delete_playlist(self, e: Event):
        Aplayer.delete_playlist(Librarian.chosen_playlist)
        Librarian.go_back()

    def __play_track(self, FQFN, queue):
        Thread(target=Aplayer.loadall, args=([FQFN], queue)).start()

    def __play_playlist_track(self, FQFN_index, queue):
        FQFN, index = FQFN_index.split('|')
        if queue is True:
            self.__play_track(FQFN, queue=True)
        else:
            Thread(target=Aplayer.loadlist,
                   args=(Librarian.chosen_playlist, index, queue)).start()

    def __get_album_filenames(self, album_artist: str, custom_dblink=None):
        link = custom_dblink if custom_dblink is not None else DBLink()
        album, artist = album_artist.split('|')
        return link.get_album_filenames(album, artist)

    def __play_album(self, album_artist, queue, custom_dblink=None):
        track_list = self.__get_album_filenames(album_artist, custom_dblink)
        Thread(target=Aplayer.loadall, args=(track_list, queue)).start()

    def __get_artist_filenames(self, artist: str, custom_dblink=None):
        link = custom_dblink if custom_dblink is not None else DBLink()
        return link.get_artist_filenames(artist)

    def __play_artist(self, artist, queue, custom_dblink=None):
        artist_list = self.__get_artist_filenames(artist, custom_dblink)
        Thread(target=Aplayer.loadall, args=(artist_list, queue)).start()

    def __play_playlist(self, title, queue):
        if queue is False:
            Thread(target=Aplayer.loadlist, args=(title,)).start()
        else:
            files = open(Aplayer.playlist_path(title), 'r').readlines()
            Thread(target=Aplayer.loadall, args=(files, True)).start()

    def __get_playlist_filenames(self, title):
        files = open(Aplayer.playlist_path(title), 'r').readlines()
        return files

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
        if label_type == TRACKS_ID:
            self.__play_track(_data, queue)
        elif label_type == ALBUMS_ID:
            self.__play_album(_data, queue)
        elif label_type == ARTISTS_ID:
            self.__play_artist(_data, queue)
        elif label_type == PLAYLISTS_ID:
            self.__play_playlist(_data, queue)
        elif label_type == PLAYLIST_SONGS_ID:
            self.__play_playlist_track(_data, queue)
        self.temp_mark_label(widget, queue)

    def __play_playlist_track(self, FQFN_index, queue):
        FQFN, index = FQFN_index.split('|')
        if queue is True:
            self.__play_track(FQFN, queue=True)
        else:
            Thread(
                target=Aplayer.loadlist,
                args=(Librarian.chosen_playlist, index, queue)).start()

    def is_loading(self):
        return Librarian.loading

    def page(self):
        return self.current_page

    def select(self, e: Event, force: bool = False):
        clicked_widget = e.widget
        # IMPORTANT: for some reason the act of converting cget to a string
        # makes it work for comparisons
        if (str(clicked_widget.cget('background')) == SELECTED_LABEL_BG_HEX
                and force is False):
            clicked_widget.configure(background=COLOUR_DICT['bg'])
            self.selection.pop(e.widget.data)
            if e.widget.label_type == PLAYLISTS_ID:
                self.playlists_in_selection -= 1
        else:
            clicked_widget.configure(background=SELECTED_LABEL_BG_HEX)
            self.selection.update({e.widget.data: e.widget})
            if e.widget.label_type == PLAYLISTS_ID:
                self.playlists_in_selection += 1

    def clear_selection(self):
        for widget in self.winfo_children():
            if not isinstance(widget, stk.TypedLabel):
                continue
            else:
                if self.selection.pop(widget.data, None) is not None:
                    widget.config(background=COLOUR_DICT['bg'])
                if len(self.selection) == 0:
                    break
        self.selection.clear()
        self.playlists_in_selection = 0

##############################################################################


class Librarian:

    chosen_artist = None
    chosen_album = None
    chosen_playlist = None
    current_page = -1
    frame = None
    browser = None
    loading = False
    subheader = None
    back_button = None
    PREFIXES = [ADDING_WDLS, QUEUING_WDLS, STARTING_WDLS]
    __refreshing = False
    __last_query = ''

    def _init(browser, frame, subheader, back_button):
        Librarian.browser = browser
        Librarian.frame = frame
        Librarian.subheader = subheader
        Librarian.back_button = back_button

    def go_back(e: Event = None):
        if Librarian.current_page == TRACKS_ID:
            Librarian.load_albums()
        elif (Librarian.current_page == ALBUMS_ID
                or Librarian.current_page == PLAYLISTS_ID
                or Librarian.current_page == SEARCH_RESULTS_ID):
            Librarian.load_artists()
        elif Librarian.current_page == PLAYLIST_SONGS_ID:
            Librarian.load_playlists()

    def draw_browser(browser=None):
        if browser is None:
            Librarian.browser = Browser(Librarian.frame)
        else:
            Librarian.browser.grid_remove()
            Librarian.browser = browser
        Librarian.loading = False
        Librarian.browser.grid(row=4, sticky=NW, columnspan=1, rowspan=1)
        Shield.root.update()

    def strip_widget_text(e: Event):
        text = e.widget.cget('text')
        for prefix in Librarian.PREFIXES:
            index = text.find(prefix)
            if index != -1:
                text = text[len(prefix):]
                break
        if text.endswith('%]'):
            text = text.rsplit(' [')[-1]
        return text.lstrip()

    def __show_label_load_stats(e: Event, text: str, count: int, max: int):
        if text == '':
            Librarian.strip_widget_text(e)
        e.widget.configure(text="{} [{:.1f}%]".format(text, 100 * count / max))
        Shield.root_update()

    def search_library(query: str = None):
        if Librarian.loading is True:
            return
        if query is None:
            q = Librarian.__last_query
        else:
            q = query
            Librarian.__last_query = query
        Librarian.update_subheader(
            SEARCH_RESULTS_ID, ' Search results for: ' + q)
        browser = Browser(Librarian.frame)
        i = 0
        i = browser._search_playlists(i, q)
        i = browser._search_artists(i, q)
        i = browser._search_albums(i, q)
        i = browser._search_tracks(i, q)
        Librarian.browser.grid_remove()
        Librarian.draw_browser(browser)

    def update_subheader(new_page: str, new_text: str = ''):
        Librarian.browser.clear_selection()
        if Librarian.current_page != new_page:
            Librarian.browser.selection.clear()
        Librarian.current_page = new_page
        if Librarian.current_page != ARTISTS_ID:
            Librarian.back_button.configure(text=BACK_TEXT)
        else:
            Librarian.back_button.configure(text=NO_BACK_TEXT)
        if Librarian.current_page == ARTISTS_ID:
            text = FIRST_SUBHEADER_TEXT
        elif Librarian.current_page == ALBUMS_ID:
            text = ">> {}".format(Librarian.chosen_artist)
        elif Librarian.current_page == TRACKS_ID:
            text = ">> {}\\{}".format(
                Librarian.chosen_artist, Librarian.chosen_album)
        elif Librarian.current_page == PLAYLISTS_ID:
            text = ">> {}".format(L['PLAYLISTS'])
        elif Librarian.current_page == PLAYLIST_SONGS_ID:
            text = ">> {}\\{}".format(
                L['PLAYLISTS'], Librarian.chosen_playlist)
        elif Librarian.current_page == SEARCH_RESULTS_ID:
            text = new_text
        Librarian.subheader.configure(text=text)

    def draw_guide():
        txt = ttk.Text(Librarian.browser, font=(DEFAULT_FONT_FAMILY, 15))
        txt.insert(INSERT, L['GUIDE'])
        txt.configure(
            state=DISABLED, background=COLOUR_DICT['bg'],
            highlightbackground=COLOUR_DICT['bg'], wrap=WORD)
        txt.grid(columnspan=2)

    def load_artists():
        if Librarian.loading is True:
            return
        Librarian.browser.grid_remove()
        Librarian.draw_browser()
        Librarian.update_subheader(ARTISTS_ID)
        artists = DBLink().get_artists()
        i = 0
        browser = Librarian.browser
        if Aplayer.number_of_playlists() > 0:
            pl = browser.add_label(
                i, L['PLAYLISTS'], None,
                L['PLAYLISTS'], Librarian.load_playlists)
            pl.configure(foreground=COLOUR_DICT['light'])
            browser.add_button(i, text="open", flippable=False)
            i += 1
        for tuple in artists:
            name = tuple[0]
            al = browser.add_label(
                i, name, ARTISTS_ID, name, Librarian.load_albums)
            browser.add_button(
                i, clickFunc=lambda e, d=name, al=al: browser.play(e, d, al))
            i += 1
        if i == 0:
            Librarian.draw_guide()

    def load_albums(e: Event = None):
        if Librarian.loading is True:
            return
        if e is not None:
            Librarian.chosen_artist = Librarian.strip_widget_text(e)
        albums = DBLink().get_albums(Librarian.chosen_artist)
        Librarian.update_subheader(ALBUMS_ID)
        album_count = len(albums)
        browser = Browser(Librarian.frame)
        i = 0
        text = " " + Librarian.chosen_artist
        for album_tuple in albums:
            label_data = album_tuple[0] + '|' + Librarian.chosen_artist
            label = browser.add_label(
                i, album_tuple[0], ALBUMS_ID,
                label_data, Librarian.load_tracks)
            browser.add_button(
                i, clickFunc=(
                    lambda e, data=label_data, label=label:
                        browser.play(e, data, label)))
            if e is not None:
                Librarian.__show_label_load_stats(
                    e, text, i, album_count)
            i += 1
        Librarian.browser.grid_remove()
        Librarian.draw_browser(browser)

    def load_tracks(e: Event = None, artist: str = ''):
        """Will load tracks into the browser.

        Args:
            e (Event, optional): The event that of the calling widget.
                Defaults to None.
            artist (str, optional): If specified, will set the
                chosen_artist of this Librarian and
                set the chosen_album as if it was returned from a search
                result, taking the first element of a split on the
                album LabelButton text ' | '. Defaults to ''.
        """
        if Librarian.loading is True:
            return
        text = ''
        album = ''
        if e is not None:
            text = e.widget.cget('text')
            album = Librarian.strip_widget_text(e)
            if artist != '':
                Librarian.chosen_artist = artist
                album = album.split(' | ')[0]
            Librarian.chosen_album = album
        else:
            artist = Librarian.chosen_artist
            album = Librarian.chosen_album
        tracks_paths = DBLink().get_all_tracks_and_paths(
            Librarian.chosen_album, Librarian.chosen_artist)
        Librarian.update_subheader(TRACKS_ID)
        song_count = len(tracks_paths)
        browser = Browser(Librarian.frame)
        i = 0
        text = ' ' + Librarian.chosen_album
        Librarian.loading = True
        for tuple in tracks_paths:
            label = browser.add_label(
                i, tuple[0], TRACKS_ID, tuple[1], browser.play)
            browser.add_button(
                i, clickFunc=(lambda e, data=tuple[1], label=label:
                              browser.play(e, data, label)))
            if e is not None:
                Librarian.__show_label_load_stats(
                    e, text, i, song_count)
            i += 1
        Librarian.loading = False
        Librarian.browser.grid_remove()
        Librarian.draw_browser(browser)

    def load_playlists(e: Event = None):
        if Librarian.loading is True:
            return
        browser = Browser(Librarian.frame)
        Librarian.update_subheader(PLAYLISTS_ID)
        i = 0
        Librarian.loading = True
        playlist_titles = Aplayer.titles_of_playlists()
        title_count = len(playlist_titles)
        for title in playlist_titles:
            label = browser.add_label(
                i, title, PLAYLISTS_ID, title, Librarian.load_playlist_songs)
            browser.add_button(
                i, clickFunc=(lambda e, d=title, l=label:
                              browser.play(e, d, l)))
            if e is not None:
                Librarian.__show_label_load_stats(
                    e, ' ' + L['PLAYLISTS'], i, title_count)
            i += 1
        Librarian.draw_browser(browser)

    def load_playlist_songs(e: Event):
        if Librarian.loading is True:
            return
        playlist_title = Librarian.strip_widget_text(e)
        Librarian.chosen_playlist = playlist_title
        Librarian.update_subheader(PLAYLIST_SONGS_ID)
        browser = Browser(Librarian.frame)
        playlist_file = Aplayer.playlist_path(playlist_title)
        chosen_playlist_files = open(playlist_file, 'r').readlines()
        playlist_length = len(chosen_playlist_files)
        del_pl_button = stk.DarkLabelButton(
            browser, browser.delete_playlist,
            text='--{}--'.format(L['DELETE_PLAYLIST']),
            font=(DEFAULT_FONT_FAMILY, 14, BOLD),
            defaultFG=DELETING_HEX, pady=10)
        del_pl_button.grid(row=0)
        i = 1
        for path in chosen_playlist_files:
            data = "{}|{}".format(path, i - 1)
            label = browser.add_label(
                i, Aplayer.get_title_from_file(path),
                PLAYLIST_SONGS_ID, data, browser.play)
            browser.add_button(
                i, clickFunc=(lambda e, d=data, l=label:
                              browser.play(e, d, l)))
            Librarian.__show_label_load_stats(
                e, ' ' + playlist_title, i, playlist_length)
            i += 1
        Librarian.draw_browser(browser)

    def __refresh_page(lbutton_event: Event, sleep_secs: float):
        if Librarian.__refreshing is True:
            return
        Librarian.__refreshing = True
        if lbutton_event is not None:
            widget = lbutton_event.widget
            widget.defaultFG = COLOUR_DICT['light']
            Shield.root_update()
            time.sleep(sleep_secs)
        page = Librarian.current_page
        time.sleep(sleep_secs)
        Librarian.browser.grid_remove()
        if Librarian.current_page != page:
            return
        elif Librarian.current_page == TRACKS_ID:
            Librarian.load_tracks()
        elif Librarian.current_page == ALBUMS_ID:
            Librarian.load_albums()
        elif Librarian.current_page == ARTISTS_ID:
            Librarian.load_artists()
        elif Librarian.current_page == PLAYLIST_SONGS_ID:
            Librarian.load_playlist_songs()
        elif Librarian.current_page == PLAYLISTS_ID:
            Librarian.load_playlists()
        elif Librarian.current_page == SEARCH_RESULTS_ID:
            Librarian.search_library()
        if lbutton_event is not None:
            widget.defaultFG = COLOUR_DICT['primary']
            widget['foreground'] = COLOUR_DICT['primary']
            Shield.root_update()
        Librarian.__refreshing = False

    def refresh_page(e: Event = None, after=1.15):
        Thread(target=Librarian.__refresh_page, args=(e, after)).start()
