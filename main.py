from tkinter import messagebox
from config import *
from aplayer import *
import records
import db
import tkintools
from graphics import LeftPane
from tkinter import *
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

db.init()
records.refresh()
root = ttk.Window(themename=THEME_NAME)
status_bar = tkintools.StatusBar(root)
configureStyle()
configureFont()
configureRoot(root)


def on_closing():
    if Aplayer.converting_audio is True:
        res = messagebox.askyesno(
            'Hold on!',
            'Files are still converting/downloading. Quit?')
        if not res:
            return
    os._exit(0)


def main():
    leftPane = LeftPane(root, status_bar)
    leftPane.drawAll()
    root.update()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
