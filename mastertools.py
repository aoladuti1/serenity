from config import *
from tkintools import *
from aplayer import Aplayer
from tkinter import messagebox
import screenery as scrn
import math


class Shield:
    """Must be initialised with init()."""

    grid_height = 0

    def init(master):
        global root
        root = master

    def edge_pad():
        return math.floor(25 * scrn.widget_monitor(root).width / 3840)

    def grid_root(expanded: bool = False):
        width, height = scrn.widget_monitor_geometry(root)
        maxwidth = LEFT_PANE_WIDTH(root, width)
        maxheight = height - scrn.reserved_geometry()[1]
        if expanded is False:
            maxheight -= scrn.title_bar_height(root, maximised=False)
        root.maxsize(width=maxwidth, height=maxheight)
        start_height = maxheight if expanded else math.ceil(2 * maxheight / 3)
        Shield.drawn_height = start_height
        root.geometry("%dx%d+0+0" % (maxwidth, start_height))
        root.update()

    def draw_header():
        header = DarkLabelButton(root)
        header.configure(
            font=(DEFAULT_FONT_FAMILY, 36), text='your library')
        header.grid(column=0, row=0, padx=10, pady=(0, 10), sticky=NW)
        return header

    def flip_screen_fill(e: Event):
        r = root.overrideredirect()
        if r is True:  # we in big mode
            e.widget.configure(text=EXPAND)
            i = 1
        else:  # we are in small mode
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


class Sword:

    def on_closing():
        if Aplayer.converting_audio is True:
            res = messagebox.askyesno(
                CONVERSION_WARNING[0], CONVERSION_WARNING[1])
            if not res:
                return
        os._exit(0)
