from config import *
from aplayer import *
from addFolder import *
import db
from tkinter import *

db.init()
db.deleteIf({'artist':'Bryson Tiller', 'track':'Sorrows'}, notCondition=True, conjunction=False)
root = Tk()


def on_closing():
    root.destroy()

#x = Aplayer("C:\\Users\\anton\\Music\\02 - Ampersand feat. Shing02.mp3")
#x.seek(260)
z = addFolderBox()


root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
