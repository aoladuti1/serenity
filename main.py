from config import *
from aplayer import *
import records
import db
from tkinter import *





db.init()
jukebox = Aplayer()

root = Tk()

def on_closing():
    root.destroy()
    Aplayer.terminate()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
