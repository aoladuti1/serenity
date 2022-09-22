
from config import *
from aplayer import *
import records
import db
from graphics import LeftPane
from tkinter import *
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

db.init() 

root = ttk.Window(themename=THEME_NAME)

configureStyle()
configureFont()
configureRoot(root)

leftPane = LeftPane(root)
leftPane.drawAll()
ttk.Label(
    root, text="hi gang", 
    font=(DEFAULT_FONT_FAMILY,100)
    ).grid(sticky='nsew',column=1, row=0)

def on_closing():
    Aplayer.kill()
    root.destroy()

root.update()
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()


