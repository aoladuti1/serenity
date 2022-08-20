import sqlite3

import subprocess
import os
import time
import tracemalloc
from config import *
from aplayer import *
from addFolder import *
from tkinter import *
from tkinter import ttk
from tkinter import dialog
from PIL import ImageTk, Image



root = Tk()

def on_closing():
    root.destroy()

#x = Aplayer("C:\\Users\\anton\\Music\\02 - Ampersand feat. Shing02.mp3")


#x.seek(260)
addFolderBox(False)




root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
