from config import configureStyle, configureFont, configureRoot, THEME_NAME
import records
import db
import ttkbootstrap as ttk


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
