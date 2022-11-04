import ttkbootstrap as ttk
from serenityapp.config import (THEME_NAME, configure_font, configure_root,
                                configure_style)


def main():
    import serenityapp.db as db
    import serenityapp.records as records
    db.init()
    records.refresh()
    root = ttk.Window(themename=THEME_NAME)
    configure_style()
    configure_font()
    configure_root(root, False)
    root.mainloop()


if __name__ == "__main__":
    main()
