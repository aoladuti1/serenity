import math
import os
from tkinter import NW, E, Event, Label, messagebox

import screenery as scrn
import serenityapp.supertk as stk
from serenityapp.audiodl import AudioDL
from serenityapp.config import DEFAULT_FONT_FAMILY, SMALL_SCREEN_CUTOFF
from serenityapp.lang import L

root = None


class Shield:
    """Manages the graphics. Call mastertools.init() once before use."""

    grid_height = 0
    last_normal_width = 0
    small_screen = False
    expanded = None
    welcome_button = None
    root = None

    def _init(master, expanded):
        global root
        root = master
        Shield.root = root
        if not expanded:
            Shield.last_normal_width == root.winfo_width()
        else:
            root.overrideredirect(1)
        root.rowconfigure(0, weight=1)
        root.update()
        Shield.welcome_button = Label(
            root, text='welcome', font=(DEFAULT_FONT_FAMILY, 20))
        Shield.welcome_button.grid(row=0)
        Shield.grid_root(expanded)
        root.update()
        root.protocol("WM_DELETE_WINDOW", Shield.on_closing)
        root.attributes('-alpha', 1)

    def base_pane_width(screen_width=None):
        if screen_width is None:
            width, _ = scrn.widget_monitor_geometry(root)
        else:
            width = screen_width
        if width < SMALL_SCREEN_CUTOFF:
            Shield.small_screen = True
            return math.floor(width / 2)
        else:
            Shield.small_screen = False
            return math.floor(width / 3)

    def root_update():
        Shield.root.update()

    def edge_pad():
        return math.floor(25 * scrn.widget_monitor(root).width / 3840)

    def max_pane(screen_width: int = None, pane_width: int = None):
        if screen_width is None:
            sw, _ = scrn.widget_monitor_geometry(root)
        else:
            sw = screen_width
        if pane_width is None:
            pw = Shield.base_pane_width(sw)
        else:
            pw = pane_width
        if sw < SMALL_SCREEN_CUTOFF:
            return pw * 2
        else:
            return math.ceil(3 * pw / 2)

    def grid_root(expanded: bool):
        width, height = scrn.widget_monitor_geometry(root)
        pane_width = Shield.base_pane_width(width)
        max_height = height - scrn.reserved_geometry()[1]
        if expanded is False:
            max_height -= scrn.title_bar_height(root, maximised=False)
            start_width = root.winfo_width()
            if Shield.last_normal_width == 0:
                Shield.last_normal_width = pane_width
            start_width = Shield.last_normal_width
        else:
            start_width = pane_width
        root.maxsize(
            width=Shield.max_pane(width, pane_width), height=max_height)
        start_height = max_height if expanded else math.ceil(2 * max_height/3)
        Shield.drawn_height = start_height
        Shield.expanded = expanded
        root.geometry("%dx%d+0+0" % (start_width, start_height))
        root.update()

    def flip_screen_fill(e: Event):
        r = root.overrideredirect()
        if r is True:  # we in big mode
            e.widget.configure(text=L['EXPAND'])
            i = 1
        else:  # we are in small mode
            Shield.last_normal_width = root.winfo_width()
            e.widget.configure(text=L['CONTRACT'])
            if root.state() == 'zoomed':
                root.state('normal')
            i = 0
        root.attributes('-alpha', 0)
        root.overrideredirect(1 - i)
        Shield.grid_root(bool(1 - i))
        if i == 1:  # window manager just enabled
            root.update()
        root.attributes('-alpha', 1)

    def on_closing():
        if not AudioDL.is_finished():
            addendum = '\n______________\n['
            for t in AudioDL.active_titles():
                addendum += t + '\n'
            addendum = addendum[0:-1] + ']'
            res = messagebox.askyesno(L['CLOSE_WARNING'][0],
                                      L['CLOSE_WARNING'][1] + addendum)
            if not res:
                return
        os._exit(0)


class Sword:
    """Manages the panes. Call mastertools.init() once before use."""

    __panes = []
    __pane_titles = ['library', 'queue']
    pane_index = -1
    current_pane = None
    header = None

    def _init():
        from serenityapp.graphics import LeftPane
        from serenityapp.secondpane import SecondPane
        global current_pane, pane_index
        status_bar = stk.StatusBar(root)
        libPane = LeftPane(status_bar)
        queuePane = SecondPane()
        Shield.welcome_button.destroy()
        root.rowconfigure(0, weight=0)
        root.rowconfigure(1, weight=1)
        root.rowconfigure(2, weight=1)
        Sword.draw_size_button()
        Sword.draw_header()
        root.update()
        Sword.__panes.append(libPane)
        Sword.__panes.append(queuePane)
        pane_index = 0
        current_pane = Sword.__panes[pane_index]
        current_pane.drawAll()

    def switch_pane(e: Event = None):
        global current_pane, pane_index
        current_pane.undrawAll()
        pane_index += 1
        if pane_index > len(Sword.__panes) - 1:
            pane_index = 0
        current_pane = Sword.__panes[pane_index]
        header.configure(
            text='serenity /{}/'.format(Sword.__pane_titles[pane_index]))
        current_pane.drawAll()

    def pane(index):
        return Sword.__panes[index]

    def draw_header():
        global header
        header = stk.DarkLabelButton(root, clickFunc=Sword.switch_pane)
        header.configure(
            font=(DEFAULT_FONT_FAMILY, 34),
            text='serenity /{}/'.format(Sword.__pane_titles[0]))
        header.grid(column=0, row=0, padx=15, pady=(0, 15), sticky=NW)
        return header

    def draw_size_button():
        expand_button = stk.DarkLabelButton(
            root, Shield.flip_screen_fill, text=L['EXPAND'])
        expand_button.configure(font=(DEFAULT_FONT_FAMILY, 13))
        expand_button.grid(
            column=0, row=0, padx=Shield.edge_pad(), sticky=E)


##############################################################################
def init(root, expanded=False):
    """Initialises all master tools."""
    if Sword.pane_index != -1:
        return
    Shield._init(root, expanded)
    Sword._init()
