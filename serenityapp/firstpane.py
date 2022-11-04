import math
import time
from pathlib import Path
from threading import Thread
from tkinter import NE, E, Event, Frame, W
from tkinter.font import BOLD

import serenityapp.supertk as stk
from serenityapp.aplayer import Aplayer
from serenityapp.audiodl import AudioDL
from serenityapp.browsing import Browser, Librarian
from serenityapp.config import (COLOUR_DICT, DEFAULT_FONT_FAMILY, is_netpath,
                                light_wait)
from serenityapp.lang import L, rellipsis
from serenityapp.mastertools import Shield

# TODO: Split up generation and drawing because
# things keep regenerating which glitches the program!!!

SEARCH_MODE = 0
STREAM_MODE = 1
STREAM_DOWNLOAD_MODE = 2
DOWNLOAD_MODE = 3
QUEUING_REL = rellipsis(L['QUEUING'])
LOADING_REL = rellipsis(L['LOADING'])
DOWNLOADING_REL = rellipsis(L['DOWNLOADING'])
LOADING_AND_DOWNLOADING_REL = rellipsis(L['LOADING_AND_DOWNLOADING'])
CONVERTING_REL = rellipsis(L['CONVERTING'])


class FirstPane:

    def __init__(self, status: stk.StatusBar):
        global _edge_pad
        _edge_pad = Shield.edge_pad()
        self.frame = Frame(Shield.root, width=Shield.max_pane())
        self.subheader = self.__gen_subheader()
        self.back_button = self.__gen_back_button()
        self.libtools = self.__gen_libtools()
        self.controls = self.__gen_controls()
        self.browser = self.__gen_browser()
        self.entrybar = self.__gen_entrybar()
        self.updating_entry_label = False
        self.current_file = ''
        self.duration_str = ''
        self.playing_text = L['NOW_PLAYING_CAP_COL']
        self.status = status
        self.seekbar = self.__gen_seekbar()
        self.downloading = False
        self.monitoring_time = False
        self.__overriding_status = False
        self.frame.rowconfigure(5, weight=1)  # browser is stretchy!
        self.frame.columnconfigure(0, weight=1)
        Aplayer.observe_path(self.observe_title)

    def __gen_browser(self):
        browser = Browser(self.frame)
        Librarian._init(browser, self.frame, self.subheader, self.back_button)
        Librarian.draw_browser()
        Librarian.load_artists()
        return browser

    def undraw(self):
        self.frame.grid_remove()

    def draw(self):
        self.frame.configure(width=Shield.max_pane())
        self.frame.grid(column=0, row=1, sticky='nsw', columnspan=1)

    def __gen_subheader(self):
        subheader = stk.DarkLabelButton(
            self.frame, click_func=self.show_hide_extras,
            font=(DEFAULT_FONT_FAMILY, 15))
        subheader.grid(column=0, row=0, sticky=W)
        return subheader

    def __gen_back_button(self):
        ''' Note this returns the actual button not the frame. '''
        bbframe = Frame(self.frame, padx=_edge_pad)
        bbframe.grid(row=0, rowspan=1, sticky=NE)
        back_button = stk.LabelButton(
            bbframe,
            click_fg=COLOUR_DICT['info'],
            click_bg=COLOUR_DICT['bg'],
            click_func=Librarian.go_back,
            font=(DEFAULT_FONT_FAMILY, 16, BOLD)
        )
        back_button.grid()
        return back_button

    def show_hide_extras(self, e: Event = None):
        self.__show_hide_libtools()
        self.__show_hide_entrybar()

    def __show_hide_libtools(self):
        if not self.libtools.grid_info():
            self.libtools.grid(row=2, pady=5)
        else:
            self.libtools.grid_remove()

    def __show_hide_entrybar(self):
        if not self.entrybar.grid_info():
            self.entrybar.grid(row=1, rowspan=1, pady=5)
            self.entrybar.focus_entry()
        else:
            self.entrybar.grid_remove()
            Shield.root.focus_force()

    def entry_button_command(self, e: Event = None, queue: bool = False):
        Thread(target=self.search_hit, args=(e, queue)).start()

    def __gen_libtools(self):
        lt = stk.LibTools(self.frame)
        lt.add_button(
            L['ADD_LIBRARY'], lambda e, AAT=True: lt.add_folders(e, AAT))
        lt.add_button(
            L['ADD_FOLDERS'], lambda e, AAT=False: lt.add_folders(e, AAT))
        lt.add_button(
            L['REFRESH'], lambda e: Librarian.refresh_page(e))
        return lt

    def __gen_entrybar(self):
        states = [
            L['SEARCH'], L['STREAM'], L['STREAM+DOWNLOAD'], L['DOWNLOAD']]
        entrybar = stk.EntryBar(
            self.frame, self.search_hit, states,
            entry_placeholder=rellipsis(L['SEARCH']))
        entrybar.add_button(
            L['QUEUE'], lambda e, q=True: self.search_hit(e, q))
        return entrybar

    def __stream(self, queue: bool = False):
        entry_text = self.entrybar.get()
        title = ''
        if is_netpath(entry_text):
            try:
                Thread(
                    target=Aplayer.loadall, args=([entry_text], queue)).start()

                if queue:
                    title = AudioDL.scrape_title(entry_text)
            except Exception:
                return  # TODO: ERROR MSG
        else:
            link, title = AudioDL.get_link_and_title(entry_text)
            if link is None:
                return  # TODO: ERROR MSG
            Thread(target=Aplayer.loadall,
                   args=([link], queue)).start()

        status_visible = self.status.grid_info()
        text = ''
        if queue:
            text = '{} \"{}\"'.format(QUEUING_REL, title)
        if not status_visible:
            self.status.grid(row=5)
            self.status.label.grid(column=0, row=0)
            if not queue:
                text = LOADING_REL
            self.status.label.configure(text=text)
        elif queue is True:
            Thread(target=self.__override_status, args=(text,)).start()

    def __download_and_display(self):
        entry_text = self.entrybar.get()
        if is_netpath(entry_text):
            link = entry_text
            title = Aplayer.get_title_from_file(link, '', True)
            if title is None:
                return  # TODO: ERROR MSG
        else:
            link, title_rough = AudioDL.get_link_and_title(entry_text)
            title = AudioDL.validate_title(title_rough)
            if title is None:
                return  # TODO: ERROR MSG
        data = AudioDL.get_online_data(title)
        if (not AudioDL.data_on_disk(data)
                and title not in AudioDL.active_titles()):
            Thread(target=self.put_dl_percent).start()
            AudioDL.download([link], data)
        else:
            # TODO: add new label to row saying that the file exists
            pass

    def put_dl_percent(self):
        if self.downloading is True:
            time.sleep(2)
            if self.downloading is True:
                return
        self.downloading = True
        side_label = self.entrybar.side_label
        side_label.config(text='...')
        side_label.grid(row=0, column=3, sticky=E)
        Shield.root_update()
        while not AudioDL.download_started():
            time.sleep(0.01)
            if AudioDL.is_downloading() and not AudioDL.download_started():
                break
        while AudioDL.download_started():
            side_label.config(
                text=' {}{}{}'.format(
                    '\u2913', AudioDL.download_percent(), '%...'))
            Shield.root_update()
            time.sleep(0.01)
            if AudioDL.download_percent() == 100:
                time.sleep(1)
                end_dl_prcnt = AudioDL.download_percent()
                if end_dl_prcnt == 0 or end_dl_prcnt == 100:
                    break
        while not AudioDL.is_finished():
            side_label.config(text=CONVERTING_REL)
            time.sleep(2)
        self.downloading = False
        side_label.grid_remove()
        Shield.root_update()

    def search_hit(self, e: Event = None, queue=False):
        mode = self.entrybar.state
        if mode == SEARCH_MODE and not queue:
            Librarian.search_library(self.entrybar.get())
        elif mode == STREAM_MODE or (mode == SEARCH_MODE and queue):
            Thread(target=self.__stream, args=(queue,)).start()
        elif mode == STREAM_DOWNLOAD_MODE:
            Thread(target=self.__stream, args=(queue,)).start()
            Thread(target=self.__download_and_display).start()
            if self.status.label.cget('text') == '':
                self.status.label.configure(text=LOADING_AND_DOWNLOADING_REL)
        elif mode == DOWNLOAD_MODE:
            Thread(target=self.__download_and_display).start()

    def __override_status(self, text):
        """
        Temporarily override the status bar text.
        Usage: Thread(target=self.__override_status).start()
        Then update self.status.label.
        """
        self.status.label.configure(text=text)
        time.sleep(1)
        self.status.label.configure(text=self.current_file)
        Shield.root_update()

    def __gen_controls(self):
        controls = stk.Controls(self.frame, self.__update_status_time)
        controls.grid(row=3, pady=5, rowspan=1)
        return controls

    def __gen_seekbar(self):
        seekbar = stk.SeekBar(self.controls, pady=int(3 * _edge_pad / 8))
        seekbar.grid(row=1)
        seekbar.bind('<Button-1>', lambda e: self.__update_status_time)
        return seekbar

    def observe_title(self, path, file):
        if file is None:
            self.current_file = ''
            self.duration_str = ''
            self.status.grid_remove()
        else:

            if Aplayer.is_online():
                self.current_file = Aplayer.get_title_from_file(file)

                self.playing_text = L['NOW_STREAMING_CAP_COL']
            else:
                self.current_file = Path(file).name
                self.playing_text = L['NOW_PLAYING_CAP_COL']
            self.status.grid(row=5)
            self.status.label.grid(column=0, row=0)
            self.status.time.grid(column=1, row=0)
            self.status.configure(background=COLOUR_DICT['bg'])
            self.status.label.configure(
                text='{} {}'.format(self.playing_text, self.current_file))
            if not self.monitoring_time:
                self.monitoring_time = True
                Thread(target=self.monitor_pos, daemon=True).start()

    def str_pos(self, secs: float):
        if secs < 0 or secs is None:
            return '00:00:00'
        else:
            return time.strftime("%H:%M:%S", time.gmtime(secs))

    def __update_status_time(self):
        duration = math.floor(Aplayer.duration())
        secs = Aplayer.time_pos()
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
        self.seekbar.pos.configure(text=str_pos)
        if self.duration_str != '':
            self.seekbar.duration.configure(text=self.duration_str)
        else:
            self.seekbar.duration.configure(text='--:--:--')
        self.seekbar.set_position(prcnt)
        Shield.root_update()

    def monitor_pos(self):
        self.status.time.configure(
            text=' | [{}/{}]'.format('00:00:00', '...?'))
        self.seekbar.pos.configure(text='00:00:00')
        self.seekbar.duration.configure(text='--:--:--')
        Shield.root_update()
        while not self.current_file == '':
            time.sleep(0.33)
            if self.__overriding_status is False:
                self.__update_status_time()
            self.monitoring_time = False
        Shield.root_update()
