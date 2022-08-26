from tkinter import filedialog
from tkinter.ttk import Style
from config import *
from aplayer import *
import records
import db

from tkinter import *
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


db.init() 
jukebox = Aplayer()


root = ttk.Window(themename='vapor')
style = ttk.Style('vapor')
style.configure('TButton', focuscolor=style.configure('TButton')['background'])
width = root.winfo_screenwidth()
height = root.winfo_screenheight()
root.geometry("%dx%d" % (width* 0.5, height * 0.5))
root.title("Serenity")


cock = ttk.Button(root, text="HEYAHYEAH")
print (cock.winfo_class())
Button(root, text="WOWOWOWOWOWOOWOWOW").pack()
cock.pack()
b1 = ttk.Button(root, text="Button 1",)
b1.pack(side=LEFT, padx=5, pady=10)

b2 = ttk.Button(root, text="Button 2", bootstyle=(OUTLINE), takefocus=False)
print(b2.winfo_class())
b2.pack(side=LEFT, padx=5, pady=10)

def on_closing():
    Aplayer.terminate()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()


