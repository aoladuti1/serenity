import time
from math import ceil
from threading import Thread
from tkinter import (CENTER, END, HORIZONTAL, LEFT, MULTIPLE, DoubleVar, E,
                     Entry, Event, Frame, Label, Listbox, S, X, filedialog)
from tkinter.font import BOLD
from typing import Callable

import ttkbootstrap as ttk

import serenityapp.records as records
from serenityapp.aplayer import Aplayer
from serenityapp.config import (COLOUR_DICT, DEFAULT_FONT_FAMILY, light_wait,
                                next_valid_index)
from serenityapp.lang import L, rellipsis, wrap_sqb

ADDING_REL = rellipsis(L['ADDING'])
ACTIVE_BUTTON_BG_HEX = '#0b3740'
CLICK_BUTTON_BG_HEX = '#2696ad'

root = None


class StatusBar(Frame):
    # THIS DEFINES THE GLOBAL ROOT VARIABLE FOR THIS MODULE
    def __init__(self, master, **kw):
        from serenityapp.mastertools import Shield
        global root
        Frame.__init__(self, master, **kw)
        self.configure(width=Shield.base_pane_width())
        self.columnconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)
        self.label = ttk.Label(
            self, font=(DEFAULT_FONT_FAMILY, 12), padding='4 4 0 4',
            background=COLOUR_DICT['dark'])
        self.time = ttk.Label(
            self, font=(DEFAULT_FONT_FAMILY, 12), padding='0 4 4 4',
            background=COLOUR_DICT['dark'])
        root = Shield.root


class TypedLabel(ttk.Label):
    def __init__(self, master, label_type: str, data: str, **kw):
        self.label_type = label_type
        self.data = data
        ttk.Label.__init__(self, master, **kw)


class LabelButton(Label):

    def default_on_enter(self, e):
        self['background'] = self.active_bg
        self['foreground'] = self.active_fg

    def default_on_leave(self, e):
        self['background'] = self.default_bg
        self['foreground'] = self.default_fg

    def on_click(self, e: Event = None):
        self['background'] = self.click_bg
        self['foreground'] = self.click_fg
        if e is None:
            if self.click_func is not None:
                self.click_func()
        else:
            if self.click_func is not None:
                self.click_func(e)

    def __init__(
        self, master, click_func: Callable = None,
        onclick_func: Callable = None,
        active_bg=ACTIVE_BUTTON_BG_HEX,
        active_fg=COLOUR_DICT['info'],
        click_bg=CLICK_BUTTON_BG_HEX,
        click_fg=COLOUR_DICT['bg'],
        default_bg=COLOUR_DICT['bg'],
        default_fg=COLOUR_DICT['primary'],
        enter_func=None,
        leave_func=None,
        unclick_func=None,
        **kw
    ):
        # onclick_func totally overrides click_func
        # onclick_func, unclick_fun, enter_func, and leave_func require
        # Event arguments to be passed to them
        Label.__init__(self, master=master, **kw)
        self.onclick_func = onclick_func
        self.click_func = click_func
        self.default_bg = default_bg
        self.default_fg = default_fg
        self.active_bg = active_bg
        self.active_fg = active_fg
        self.click_bg = click_bg
        self.click_fg = click_fg
        self.enter_func = enter_func
        self.leave_func = leave_func
        self.unclick_func = unclick_func
        self.state = 0
        self.configure(cursor='hand2')
        if onclick_func is None:
            self.onclick_func = self.on_click
        if default_bg is None:
            self.default_bg = self['background']
        if default_fg is None:
            self.default_fg = self['foreground']
        if enter_func is None:
            self.enter_func = self.default_on_enter
        if leave_func is None:
            self.leave_func = self.default_on_leave
        if unclick_func is None:
            self.unclick_func = self.leave_func
        self['background'] = default_bg
        self['foreground'] = default_fg
        self.bind("<Enter>", self.enter_func)
        self.bind("<Leave>", self.leave_func)
        self.bind("<Button-1>", self.onclick_func)
        self.bind("<ButtonRelease-1>", self.unclick_func)


class SeekBar(Frame):
    def __init__(self, master, **kw):
        from serenityapp.mastertools import Shield
        Frame.__init__(self, master, **kw)
        self.columnconfigure((1, 2, 3, 4, 5, 6, 7, 8, 9, 10), weight=1)
        self.sliding = False
        self.pos = ttk.Label(
            self, font=(DEFAULT_FONT_FAMILY, 12), padding='0 0 10 0')
        self.pos.pack(side=LEFT)
        self.new_position = DoubleVar()
        self.slider = ttk.Scale(
            self, from_=0, to_=100, orient=HORIZONTAL,
            variable=self.new_position,
            command=self.seek_percent,
            length=int(Shield.base_pane_width() * 6/10))
        self.slider.bind('<Button-1>', self.set_value)
        self.slider.pack(side=LEFT, expand=True, fill=X, anchor=CENTER)
        self.duration = ttk.Label(
            self, font=(DEFAULT_FONT_FAMILY, 12), padding='10 0 0 0')
        self.duration.pack(side=LEFT)

    def unset_sliding(self, secs):
        time.sleep(secs)
        self.sliding = False

    def set_value(self, e: Event):
        self.slider.event_generate('<Button-3>', x=e.x, y=e.y)
        return 'break'

    def set_position(self, percent):
        if self.sliding:
            return
        else:
            self.new_position.set(percent)

    def seek_percent(self, p: float):
        if self.sliding is True:
            return
        self.sliding = True
        time.sleep(0.15)
        self.slider.update()
        self.new_position.set(self.slider.get())
        percent = ceil(float(self.new_position.get()))
        Aplayer.seek_percent(percent)
        sleep_secs = 0.15
        if percent == 100:
            sleep_secs = 1
        Thread(target=self.unset_sliding, args=(sleep_secs,)).start()


class DarkLabelButton(LabelButton):
    def __init__(self, master, click_func=None,
                 default_fg=COLOUR_DICT['primary'], **kw):
        LabelButton.__init__(
            self, master=master,
            unclick_func=click_func,
            default_fg=default_fg,
            active_fg=COLOUR_DICT['info'],
            active_bg=COLOUR_DICT['bg'],
            click_fg=COLOUR_DICT['info'],
            click_bg=COLOUR_DICT['bg'], **kw)


class QueueListbox(Listbox):
    """ A tkinter listbox with drag'n'drop reordering of entries. """

    def __init__(self, master, set_fg=COLOUR_DICT['light'],
                 current_song_fg=COLOUR_DICT['primary'], **kw):
        from serenityapp.mastertools import Shield
        kw['selectmode'] = MULTIPLE
        Listbox.__init__(self, master, **kw)
        kw['foreground'] = set_fg
        self.config(selectforeground=COLOUR_DICT['info'])
        self.cur_index = None
        self.cur_state = None
        self.current_song_fg = current_song_fg
        self.__last_playing_pos = -1
        self.config(foreground=set_fg)
        self.bind('<Button-1>', self.get_state, add='+')
        self.bind('<Button-1>', self.set_current, add='+')
        self.bind('<B1-Motion>', self.shift_selection)
        self.bind('<ButtonRelease-1>', self.moved_item)
        self.bind('<Double-Button-1>',
                  lambda e: Aplayer.play_index(self.cur_index))
        self.config(width=50, height=int(Shield.drawn_height / 55),
                    background=COLOUR_DICT['bg'])
        Aplayer.observe_playlist_changes(self.refresh_queue)
        Aplayer.observe_playlist_pos(self.update)

    def moved_item(self, e: Event = None):
        if self.cur_index != self.last_cur_index:
            Aplayer.playlist_move(self.last_cur_index, self.cur_index, True)

    def set_current(self, e: Event):
        ''' gets the current index of the clicked item in the listbox '''
        self.cur_index = self.nearest(e.y)
        self.last_cur_index = self.cur_index

    def get_state(self, e: Event):
        ''' checks if the clicked item in listbox is selected '''
        self.cur_state = 1

    def shift_selection(self, e: Event):
        ''' shifts item up or down in listbox '''
        i = self.nearest(e.y)
        if self.cur_state == 1:
            self.selection_set(self.cur_index)
        else:
            self.selection_clear(self.cur_index)
        if i < self.cur_index:
            # Moves up
            x = self.get(i)
            selected = self.selection_includes(i)
            self.delete(i)
            self.insert(i+1, x)
            if selected:
                self.selection_set(i+1)
            self.cur_index = i
        elif i > self.cur_index:
            # Moves down
            x = self.get(i)
            selected = self.selection_includes(i)
            self.delete(i)
            self.insert(i-1, x)
            if selected:
                self.selection_set(i-1)
            self.cur_index = i

    def update(self, _, _2):
        light_wait()
        pos = Aplayer.get_playlist_pos()
        size = self.size()
        if ((pos is None or pos < 0
            or pos > size - 1
                or self.__last_playing_pos > size - 1)):
            return
        valid_pos = pos if pos < size else size - 1
        if self.__last_playing_pos != -1:
            self.itemconfig(self.__last_playing_pos, {
                            'fg': self['foreground']})
        else:
            self.itemconfig(self.size() - 1, {'fg': self['foreground']})
        self.itemconfig(valid_pos, {'fg': self.current_song_fg})
        self.__last_playing_pos = valid_pos

    def refresh_queue(self, _, count):
        self.delete(0, END)
        for path in Aplayer.playlist_filenames():
            self.insert(END, Aplayer.get_title_from_file(path))
        if count == 1:
            self.__last_playing_pos = 0
        self.update(None, self.__last_playing_pos)
        root.update()

    # event should be from a DarkLabelButton
    def unselect_all(self, e: Event):
        self.selection_clear(0, END)
        e.widget['foreground'] = e.widget.default_fg

    # event should be from a DarkLabelButton
    def playlist_clear(self, e: Event):
        Aplayer.clear_queue()
        e.widget['foreground'] = e.widget.default_fg
        self.update(None, None)

    # event should be from a DarkLabelButton
    def playlist_remove_selection(self, e: Event):
        Aplayer.batch_clear(self.curselection())


class EntryBar(Frame):

    def __init__(self, master, main_func, states: list[str],
                 main_alterable=True, entry_placeholder='', smartxpad=6, **kw):
        Frame.__init__(self, master, **kw)
        self.state = 0
        self.states = states
        self.__padx = smartxpad
        self.button_frames = []
        main_button_widgets = self.add_button(
            self.states[0], main_func, alterable=main_alterable)
        self.main_button_frame = main_button_widgets[0]
        self.main_button = main_button_widgets[1]
        self.side_label = ttk.Label(self, font=(DEFAULT_FONT_FAMILY, 13, BOLD))
        self.entry = Entry(self, width=27)
        self.entry.grid(row=0, column=0, padx=(0, smartxpad))
        self.entry.configure(
            font=(DEFAULT_FONT_FAMILY, 13),
            background=COLOUR_DICT['dark'],
            selectbackground=COLOUR_DICT['selectbg'])
        self.entry.bind('<Return>', self.click_sim)
        self.entry.insert(0, entry_placeholder)

    def __grid_new_button(self, button_frame):
        i = len(self.button_frames)
        if i == 0:
            button_frame.grid(row=0, column=i, sticky=S)
        else:
            button_frame.grid(row=0, column=i, sticky=S, padx=self.__padx)

    def add_button(self, text, click_func=None, alterable=False):
        button_frame = Frame(self)
        button_frame.configure(
            highlightcolor=COLOUR_DICT['light'],
            highlightbackground=COLOUR_DICT['light'],
            highlightthickness=1)
        button = LabelButton(
            button_frame, text=text,
            click_func=click_func,
            font=(DEFAULT_FONT_FAMILY, 13, BOLD))
        if alterable:
            button.bind('<Button-3>', self.alter_button)
        button.grid()
        self.button_frames.append(button_frame)
        self.__grid_new_button(button_frame)
        return [button_frame, button]

    def click_sim(self, e: Event = None):
        self.main_button.event_generate('<Button-1>')
        root.update()
        time.sleep(0.08)
        self.main_button.event_generate('<ButtonRelease-1>')
        root.update()

    def alter_button(self, e: Event):
        self.state = next_valid_index(self.state, self.states)
        e.widget.configure(text=self.states[self.state])

    def focus_entry(self):
        self.entry.focus_force()
        self.entry.select_range(0, 'end')
        self.entry.icursor('end')

    def set_entry_bg(self, colour):
        self.entry['background'] = colour

    def show_side_label(self, text):
        self.side_label.configure(text=text)
        self.side_label.grid(row=0, column=len(
            self.button_frames) + 1, sticky=E)

    def hide_side_label(self, text=''):
        self.side_label.grid_remove()
        if text != '':
            self.side_label.configure(text=text)

    def set_side_label_text(self, text):
        self.side_label.configure(text=text)

    def get_side_label_text(self):
        return self.side_label.cget('text')

    def get(self):
        return self.entry.get()


class LibTools(Frame):

    BUTTON_PADX = 7

    def __init__(self, master, **kw):
        Frame.__init__(self, master, **kw)
        self.adding_music_label = ttk.Label(
            self, font=(DEFAULT_FONT_FAMILY, 12))
        self.lbuttons = []

    def add_button(self, text_nosqb, click_func):
        '''Add a button. Arg text_nosqb will be wrapped in square brackets.'''
        button = LabelButton(
            self, click_fg=COLOUR_DICT['info'], click_bg=COLOUR_DICT['bg'],
            click_func=click_func,
            text=wrap_sqb(text_nosqb), font=(DEFAULT_FONT_FAMILY, 12, BOLD))
        col = len(self.lbuttons)
        button.grid(column=col, row=0, sticky=S, padx=LibTools.BUTTON_PADX)
        self.lbuttons.append(button)

    def finish_adding_music(self):
        self.adding_music_label.configure(text=L['DONE_EXCL'])
        root.update()
        time.sleep(1)
        self.adding_music_label.grid_remove()

    def add_folders(self, e: Event, AAT_structure: bool):
        from serenityapp.browsing import Librarian
        directory = filedialog.askdirectory()
        if not directory == '':
            self.adding_music_label.configure(text=ADDING_REL)
            self.adding_music_label.grid(row=0, column=3)
            root.update()
            records.add_folder(directory, AAT_structure)
            Thread(target=self.finish_adding_music).start()
            Librarian.refresh_page()


class Controls(Frame):

    PAUSE_LABELS = ['||', '|>']

    def __init__(self, master, update_time_func, **kw):
        Frame.__init__(self, master, **kw)
        self.grid(row=3, pady=5, rowspan=1)
        self.buttons_frame = Frame(self)
        self.buttons_frame.grid(row=0)
        self.buttons = []
        self.pause_button = None
        self.paused = True
        self.__init_playstate = False
        self.__update_status_time = update_time_func
        self.add_button(
            click_func=lambda e: Aplayer.shuffle(), text='¿?',
            unclick_func=self.toggle_highlight)
        self.add_button(
            click_func=lambda e: Aplayer.prev(), text='|<<')
        self.add_button(
            click_func=lambda e, t=-10: self.seek(e, t), text='<++')
        self.add_pause_button()
        self.add_button(
            click_func=lambda e, t=10: self.seek(e, t), text='++>')
        self.add_button(
            click_func=lambda e: Aplayer.next(), text='>>|')
        self.add_button(
            click_func=lambda e: Aplayer.change_loop(), text='{0}',
            unclick_func=self.highlight_replay)

    def add_button(self, text: str, click_func: Callable,
                   unclick_func: Callable = None):
        if unclick_func is None:
            func = self.control_release
        else:
            func = unclick_func
        button = LabelButton(
            self.buttons_frame,
            enter_func=self.wrap_squares, leave_func=self.unwrap_squares,
            click_fg=COLOUR_DICT['info'], click_bg=COLOUR_DICT['bg'],
            click_func=click_func, unclick_func=func,
            text=text, font=(DEFAULT_FONT_FAMILY, 16, BOLD),
            padx=30)
        i = len(self.buttons)
        button.grid(
            column=i, row=0, sticky=S, pady=5, rowspan=1, columnspan=1)
        self.buttons.append(button)
        self.buttons_frame.columnconfigure(i, weight=1)
        self.columnconfigure(i, weight=1)

    def add_pause_button(self):
        self.add_button(
            click_func=lambda e: Aplayer.pauseplay(), text='|>')
        self.pause_button = self.buttons[len(self.buttons) - 1]
        Aplayer.observe_pause(self.monitor_playstate)
        Aplayer.observe_path(self.__check_file)

    def seek(self, e, seconds):
        Thread(target=Aplayer.seek, args=(seconds,)).start()
        light_wait()
        self.__update_status_time()

    def __check_file(self, _, file):
        if self.paused is True:
            if not Aplayer.is_paused() and file is not None:
                self.monitor_playstate(_, False)

    def monitor_playstate(self, _, paused):
        if self.__init_playstate is True:
            state = int(paused)
            self.paused = paused
            self.pause_button.configure(text=Controls.PAUSE_LABELS[state])
        else:
            self.__init_playstate = True

    def control_release(self, e: Event):
        e.widget.configure(foreground=COLOUR_DICT['primary'])
        self.unwrap_squares(e)

    def wrap_squares(self, e: Event):
        text = e.widget.cget('text')
        e.widget.configure(text='[' + text + ']')

    def unwrap_squares(self, e: Event):
        text = e.widget.cget('text')
        if text.startswith('['):
            e.widget.configure(text=text[1:-1])

    def highlight_replay(self, e: Event):
        states = [
            COLOUR_DICT['primary'], COLOUR_DICT['light'], COLOUR_DICT['info']]
        self.control_release(e)
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

    def toggle_highlight(self, e: Event):
        states = [COLOUR_DICT['primary'], COLOUR_DICT['info']]
        e.widget.state = 1 - e.widget.state
        self.control_release(e)
        e.widget.configure(foreground=states[e.widget.state])
