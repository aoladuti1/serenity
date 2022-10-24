from config import *
import records
import db
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
    root.mainloop()


if __name__ == "__main__":
    main()