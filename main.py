import ttkbootstrap as ttk

import serenityapp.db as db
import serenityapp.records as records
from serenityapp.config import (THEME_NAME, configureFont, configureRoot,
                                configureStyle)


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
