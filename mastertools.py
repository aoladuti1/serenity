from config import *
from tkintools import *
from aplayer import Aplayer
from tkinter import messagebox
import screenery as scrn
import math

class Shield:
    """Must be initialised with init()."""

    grid_height = 0
    last_normal_width = 0

    def _init(master: Toplevel, expanded: bool):
        global root
        root = master
        if not expanded:
            Shield.last_normal_width == root.winfo_width()
        else:
            root.overrideredirect(1)
        Shield.grid_root(expanded)
        Shield.draw_header()
        Shield.draw_size_button()
        root.update()
        root.protocol("WM_DELETE_WINDOW", Shield.on_closing)

    def base_pane_width(root, screen_width=None):
        if screen_width is None:
            width, _ = scrn.widget_monitor_geometry(root)
        else:
            width = screen_width
        if width < SMALL_SCREEN_CUTOFF:
            return math.floor(width / 2)
        else:
            return math.floor(width / 3)

    def edge_pad():
        return math.floor(25 * scrn.widget_monitor(root).width / 3840)

    def max_pane(screen_width: int = None, pane_width: int = None):
        if screen_width is None:
            sw, _ = scrn.widget_monitor_geometry(root)
        else:
            sw = screen_width
        if pane_width is None:
            pw = Shield.base_pane_width(root, sw)
        else:
            pw = pane_width
        if sw < SMALL_SCREEN_CUTOFF:
            return pw * 2
        else:
            return math.ceil(pw * 1.5)

    def grid_root(expanded: bool):
        width, height = scrn.widget_monitor_geometry(root)
        pane_width = Shield.base_pane_width(root, width)
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
        root.geometry("%dx%d+0+0" % (start_width, start_height))
        root.update()

    def draw_header():
        header = DarkLabelButton(root, clickFunc=Sword.switch_page)
        header.configure(
            font=(DEFAULT_FONT_FAMILY, 36), text='your library')
        header.grid(column=0, row=0, padx=15, pady=(0, 15), sticky=NW)
        return header

    def flip_screen_fill(e: Event):
        r = root.overrideredirect()
        if r is True:  # we in big mode
            e.widget.configure(text=EXPAND)
            i = 1
        else:  # we are in small mode
            Shield.last_normal_width = root.winfo_width()
            e.widget.configure(text=CONTRACT)
            if root.state() == 'zoomed':
                root.state('normal')
            i = 0
        root.attributes('-alpha', 0)
        root.overrideredirect(1 - i)
        Shield.grid_root(bool(1 - i))
        if i == 1:  # window manager just enabled
            root.update()
        root.attributes('-alpha', 1)

    def draw_size_button():
        expand_button = DarkLabelButton(
            root, Shield.flip_screen_fill, text=EXPAND)
        expand_button.configure(font=(DEFAULT_FONT_FAMILY, 13))
        expand_button.grid(
            column=0, row=0, padx=Shield.edge_pad(), sticky=E)

    def on_closing():
        if Aplayer.converting_audio is True:
            res = messagebox.askyesno(
                CONVERSION_WARNING[0], CONVERSION_WARNING[1])
            if not res:
                return
        os._exit(0)


class Sword:

    __pages = []
    page_index = 0
    current_pane = None

    def _init():
        from graphics import LeftPane
        global current_pane
        status_bar = StatusBar(root)
        current_pane = LeftPane(root, status_bar)
        Sword.__pages.append(current_pane)
        current_pane.drawAll()

    def switch_page(e: Event = None):
        pass


def init(root: Toplevel, expanded: bool = False):
    Shield._init(root, expanded)
    Sword._init()