from tkinter import messagebox
from tkinter.font import ITALIC
from config import *
import records
import db
import tkintools
from graphics import LeftPane
from tkinter import *
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


def main():
    db.init()
    records.refresh()
    root = ttk.Window(themename=THEME_NAME)
    configureStyle()
    configureFont()
    configureRoot(root, False)
    status_bar = tkintools.StatusBar(root)
    leftPane = LeftPane(root, status_bar)
    leftPane.drawAll()
    root.update()
    root.mainloop()


if __name__ == "__main__":
    main()
