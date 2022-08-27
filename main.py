from distutils.log import info
from email.policy import default
from tkinter import filedialog
from tkinter.font import BOLD, ITALIC
from tkinter.ttk import Style
from config import *
from aplayer import *
import records
import db

from tkinter import *
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
import ttkbootstrap.dialogs.dialogs as dialogs

db.init() 
jukebox = Aplayer()


root = ttk.Window(themename='serenity')
style = ttk.Style('serenity')
default_font = ttk.font.nametofont("TkDefaultFont")
default_family = 'Cascadia Code Light'
default_font.configure(family=default_family, size = 14)
    # the following line stops annoying highlight lines on button click
style.configure('TButton', focuscolor=style.configure('TButton')['background'])
style.configure('Sel.TButton', foreground='black')

width = root.winfo_screenwidth()
height = root.winfo_screenheight()
root.geometry("%dx%d" % (width* 0.5, height * 0.5))
root.update()
root.rowconfigure(2,weight=1)
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.title("serenity")

ddd=ttk.Label(root, text="serenity", bootstyle='primary')
ddd.configure(font=(default_family,50, ITALIC), background='#000000')
ddd.grid(column=0, row=0, sticky=W)
ttk.Label(root, text="Your library").grid(sticky = W,column=0, row=1)
sf = ScrolledFrame(root, autohide=False, height=root.winfo_height(), width= 700)
sf.columnconfigure(0, weight=1)
sf.columnconfigure(1, weight=0)
sf.grid(column = 0, row=2, sticky='nsw', columnspan=1)
style.configure('TFrame', background='#000000')
ttk.Label(sf, text='<---').grid(column=0, row=0, sticky=W)
ttk.Label(root, text="HEY").grid(sticky = 'nsew', column=1, row=2)

global i
i = 1

selcount = 0
selwidget = None
def colour(y: Event):
    global selwidget
    global selcount
    clickedWidget = y.widget
    if selcount < 1:
        clickedWidget.config(background = style.lookup('TButton','background'))
        if selwidget != None:
            selwidget.config(background = style.lookup('TLabel','background'))
        selwidget = clickedWidget
        selcount += 1
    elif clickedWidget != selwidget:
        selcount -= 1
        clickedWidget.config(background = style.lookup('TButton','background'))
        selwidget.config(background = style.lookup('TLabel','background'))
        selwidget = clickedWidget
    else:
        selcount = 0
        selwidget = None
        clickedWidget.config(background = style.lookup('TLabel','background'))
def c(e):
    e.widget['foreground'] = '#000000'
for x in range(10):
    lb = ttk.Label(sf,text="Bryson Tiller - lonely christmaddddddddddds",bootstyle='info')
    lb.grid(column=0, row=i, rowspan=1, sticky=W, padx=5, ipadx=700)
    lb.configure(background='#000000')
    lb.bind('<Button-1>', colour)
    y = Button(sf, text='play', pady=2, background='black')
    y.bind('<Enter>', lambda e: c(e))
    y.grid(column=1, row=i,rowspan=1, pady=4, padx=(7,20), sticky=E)
    i += 1


# children are ordered in the order they were gridded
# for child in sf.winfo_children():
#     if child.winfo_class() == 'TLabel' :
#         print(child.cget("text"))

def on_closing():
    Aplayer.terminate()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()


