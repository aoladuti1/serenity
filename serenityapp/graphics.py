import math
import threading
import time
from pathlib import Path
from tkinter import *
from tkinter import filedialog
from tkinter.font import BOLD
from typing import Callable

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

import serenityapp.supertk as stk
from serenityapp.aplayer import Aplayer
from serenityapp.audiodl import AudioDL
from serenityapp.browsing import Browser, Librarian
from serenityapp.config import *
from serenityapp.mastertools import Shield

# TODO: Split up generation and drawing because
# things keep regenerating which glitches the program!!!

SEARCH_MODE = 0
STREAM_MODE = 1
STREAM_DOWNLOAD_MODE = 2
DOWNLOAD_MODE = 3

class LeftPane:

    PAUSE_LABELS = ['||', '|>']

    def __init__(self, status: stk.StatusBar):
        global _edge_pad
        _edge_pad = Shield.edge_pad()
        self.frame = Frame(Shield.root, width=Shield.max_pane())
        self.subheader = self.__gen_subheader()
        self.back_button = self.__gen_back_button()
        self.libTools = None
        self.controls = None
        self.control_buttons = None
        self.browser = self.__gen_browser()
        self.pauseButton = None
        self.entryBar = None
        self.libToolsVisible = False
        self.entryBarVisible = False
        self.updating_entry_label = False
        self.current_file = ''
        self.duration_str = ''
        self.playing_text = 'Now playing:'
        self.status = status
        self.adding_music_label = None
        self.seekBar = None
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

    def undrawAll(self):
        self.frame.grid_remove()

    def redrawAll(self):
        self.frame.grid(column=0, row=1, sticky='nsw', columnspan=1)

    def drawAll(self):
        self.drawFrame()
        self.drawAllExceptFrame()

    def drawAllExceptFrame(self):
        self.genLibTools()
        self.genEntryBar()
        self.drawControls()

    def drawFrame(self):
        self.frame.configure(width=Shield.max_pane())
        self.frame.grid(column=0, row=1, sticky='nsw', columnspan=1)

    def __gen_subheader(self):
        subheader = stk.DarkLabelButton(
            self.frame, clickFunc=self.showHideExtras,
            font=(DEFAULT_FONT_FAMILY, 15))
        subheader.grid(column=0, row=0, sticky=W)
        return subheader
        
    def __gen_back_button(self):
        ''' Note this returns the actual button not the frame. '''
        bbframe = Frame(self.frame, padx=_edge_pad)
        bbframe.grid(row=0, rowspan=1, sticky=NE)
        back_button = stk.LabelButton(
            bbframe,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['bg'],
            clickFunc=Librarian.go_back,
            font=(DEFAULT_FONT_FAMILY, 16, BOLD)
        )
        back_button.grid()
        return back_button

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
            self.entryBar.focus_entry()
        else:
            self.entryBar.grid_remove()
            Shield.root.focus_force()
        self.entryBarVisible = not self.entryBarVisible

    def finish_adding_music(self):
        self.adding_music_label.configure(text='done!')
        Shield.root_update()
        time.sleep(1)
        self.adding_music_label.grid_remove()

    def add_folders(self, e: Event, AAT_structure: bool):
        directory = filedialog.askdirectory()
        if not directory == '':
            self.adding_music_label.configure(text='adding...')
            self.adding_music_label.grid(row=2, column=3)
            Shield.root_update()
            records.addFolder(directory, AAT_structure)
            threading.Thread(target=self.finish_adding_music).start()
            Librarian.refresh_page()

    def entry_button_command(self, e: Event = None, queue: bool = False):
        threading.Thread(target=self.search_hit, args=(e, queue)).start()

    def genLibTools(self):
        self.libTools = Frame(self.frame)
        add_library = stk.LabelButton(
            self.libTools,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['bg'],
            clickFunc=lambda e, AAT=True: self.add_folders(e, AAT),
            text='[add library]',
            font=(DEFAULT_FONT_FAMILY, 12, BOLD))
        add_folders = stk.LabelButton(
            self.libTools,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['bg'],
            clickFunc=lambda e, AAT=False: self.add_folders(e, AAT),
            text='[add songs]',
            font=(DEFAULT_FONT_FAMILY, 12, BOLD)
        )
        refresh_button = stk.LabelButton(
            self.libTools,
            clickFG=COLOUR_DICT['info'],
            clickBG=COLOUR_DICT['bg'],
            clickFunc=lambda e: Librarian.refresh_page(e),
            text='[refresh]',
            font=(DEFAULT_FONT_FAMILY, 12, BOLD)
        )
        self.adding_music_label = ttk.Label(self.libTools,
                                            font=(DEFAULT_FONT_FAMILY, 12))
        padx = 7
        add_library.grid(column=0, row=2, sticky=S, padx=padx)
        add_folders.grid(column=1, row=2, sticky=S, padx=padx)
        refresh_button.grid(column=2, row=2, sticky=S, padx=padx)

    def genEntryBar(self):
        states = ['search', 'stream', 'stream + download', 'download']
        self.entryBar = stk.EntryBar(
            self.frame, self.search_hit, states,
            entry_placeholder='search...')
        self.entryBar.add_button(
            'queue', lambda e, q=True: self.search_hit(e, q))

    def __stream(self, queue: bool = False):
        entry_text = self.entryBar.get()
        if is_netpath(entry_text):
            try:
                threading.Thread(
                    target=Aplayer.loadall, args=([entry_text], queue)).start()
                return AudioDL.scrape_title(entry_text)
            except Exception:
                return None  # TODO: ERROR MSG
        else:
            link, title = AudioDL.get_link_and_title(entry_text)
            if link is None:
                return  # TODO: ERROR MSG
            threading.Thread(target=Aplayer.loadall,
                             args=([link], queue)).start()
            return title

    def __download_and_display(self):
        entry_text = self.entryBar.get()
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
        if not AudioDL.data_on_disk(data):
            threading.Thread(target=self.put_dl_percent).start()
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
        side_label = self.entryBar.side_label
        side_label.config(text='...')
        side_label.grid(row=0, column=3, sticky=E)
        Shield.root_update()
        while not AudioDL.download_started():
            time.sleep(0.01)
            if AudioDL.is_downloading() and not AudioDL.download_started():
                break
        while AudioDL.download_started():
            side_label.config(
                text=' \u2913' + str(AudioDL.download_percent()) + '%...')
            Shield.root_update()
            time.sleep(0.01)
            if AudioDL.download_percent() == 100:
                time.sleep(1)
                end_dl_prcnt = AudioDL.download_percent()
                if end_dl_prcnt == 0 or end_dl_prcnt == 100:
                    break
        while not AudioDL.is_finished():
            side_label.config(text='converting...')
            time.sleep(2)
        self.downloading = False
        side_label.grid_remove()
        Shield.root_update()

    def search_hit(self, e: Event = None, queue=False):
        mode = self.entryBar.state
        if mode == SEARCH_MODE:
            Librarian.search_library(self.entryBar.get())
        elif mode == STREAM_MODE:
            title = self.__stream(queue)
            if self.status.label.cget('text') == '':
                text = 'queuing... \"' + title + '\"' if queue else 'loading...'
                self.status.label.configure(text=text)
            else:
                if queue is True:
                    threading.Thread(
                        target=self.__override_status,
                        args=('queuing... \"' + title + '\"',)).start()
        elif mode == STREAM_DOWNLOAD_MODE:
            threading.Thread(target=self.__stream, args=(queue,)).start()
            threading.Thread(target=self.__download_and_display).start()
            if self.status.label.cget('text') == '':
                self.status.label.configure(text='loading and downloading...')
        elif mode == DOWNLOAD_MODE:
            threading.Thread(target=self.__download_and_display).start()
        Shield.root_update()


    def __override_status(self, text):
        """
        Temporarily override the status bar text.
        Usage: threading.Thread(target=self.__override_status).start()
        Then update self.status.label.
        """
        self.status.label.configure(text=text)
        time.sleep(1)
        self.status.label.configure(text=self.current_file)
        Shield.root_update()

    def seek(self, e, seconds):
        threading.Thread(target=Aplayer.seek, args=(seconds,)).start()
        light_wait()
        self.__update_status_time()

    def drawControls(self):
        self.controls = Frame(self.frame)
        self.controls.grid(row=3, pady=5, rowspan=1)
        self.control_buttons = Frame(self.controls)
        self.control_buttons.grid(row=0)
        shuffle = self.genControlButton(
            clickFunc=lambda e: Aplayer.shuffle(), text='¿?',
            unclickFunc=self.toggle_highlight)
        prev = self.genControlButton(
            clickFunc=lambda e: Aplayer.prev(),
            text='|<<')
        seek_neg = self.genControlButton(
            clickFunc=lambda e, t=-10: self.seek(e, t), text='<++')
        pause = self.genControlButton(
            clickFunc=lambda e: self.controlThreader(e, Aplayer.pauseplay),
            text='|>')
        seek_pos = self.genControlButton(
            clickFunc=lambda e, t=10: self.seek(e, t), text='++>')
        next = self.genControlButton(
            clickFunc=lambda e: Aplayer.next(),
            text='>>|')
        repeat = self.genControlButton(
            clickFunc=lambda e: Aplayer.change_loop(), text='{0}',
            unclickFunc=self.highlight_replay)
        self.cgrid([shuffle, prev, seek_neg, pause, seek_pos, next, repeat])
        self.seekBar = stk.SeekBar(
            self.controls, pady=int(3 * _edge_pad / 8))
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
            self.controls.columnconfigure(i, weight=1)
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

            if Aplayer.is_online():
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
        self.seekBar.pos.configure(text=str_pos)
        if self.duration_str != '':
            self.seekBar.duration.configure(text=self.duration_str)
        else:
            self.seekBar.duration.configure(text='--:--:--')
        self.seekBar.set_position(prcnt)
        Shield.root_update()

    def monitor_pos(self):
        self.status.time.configure(
            text=' | [{}/{}]'.format('00:00:00', '...?'))
        self.seekBar.pos.configure(text='00:00:00')
        self.seekBar.duration.configure(text='--:--:--')
        Shield.root_update()
        while not self.current_file == '':
            time.sleep(0.33)
            if self.__overriding_status is False:
                self.__update_status_time()
            self.monitoring_time = False
        Shield.root_update()

    def genControlButton(self, text: str, clickFunc: Callable,
                         unclickFunc: Callable = None):
        if unclickFunc is None:
            func = self.controlRelease
        else:
            func = unclickFunc
        return stk.LabelButton(
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

    def wrapSquares(self, e: Event):
        text = e.widget.cget('text')
        e.widget.configure(text='[' + text + ']')

    def unwrapSquares(self, e: Event):
        text = e.widget.cget('text')
        if text.startswith('['):
            e.widget.configure(text=text[1:-1])
    