from tkinter import ttk

UNSELECTED_TAB = "#C4C4C4"
SELECTED_TAB = "#777A7A"
NAV_BG = "#444A4A"


def style_GUI():
    # define main styling
    main_theme()
    # extra styling
    ttk.Style().configure('Heading.TLabel', font=('Helvetica', 20))


def main_theme():
    style = ttk.Style()
    style.theme_create("Main_Theme", parent="alt", settings={
        "TNotebook": {"configure": {"tabmargins": [10, 10, 10, 10], "tabposition": "wn", "background": NAV_BG, "borderwidth": "0"}},
        "TNotebook.Tab": {
            "configure": {"padding": [65, 15], "margin": [10, 10, 10, 10], "background": UNSELECTED_TAB, "width": "15", "borderwidth": "0", "expand": [1, 1, 1, 1]},
            "map": {"background": [("selected", SELECTED_TAB)]},
        },
        "TFrame": {"configure": {"background": 'black', "foreground": "white"}},
        "TLabel": {"configure": {"background": 'black', "foreground": "white"}},
        "TButton": {"configure": {'foreground': 'white', "padding": [5, 5], "anchor": "center"},
                    "map": {"background": [("!active", SELECTED_TAB), ("active", NAV_BG)],
                            "foreground": [("disabled", UNSELECTED_TAB)]}},
        'TEntry': {"configure": {"padding": [1, 3]}}
    })
    style.theme_use('Main_Theme')
