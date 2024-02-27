import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk
from modules.logging.log_utils import log_setup
from Model import Model


class Feedback:

    tab: ttk.Frame
    model: Model

    def __init__(self, root: ttk.Notebook, model: Model):
        """Main Frame and driver for the Feedback tab."""

        self.tab: ttk.Frame = ttk.Frame(root)

        # set up and place title and content frames
        self.title_frame = ttk.Frame(self.tab, padding=25)
        self.content_frame = ttk.Frame(self.tab, padding=25)
        self.title_frame.grid(row=0, column=0)
        self.content_frame.grid(row=1, column=0)

        # add title
        ttk.Label(self.title_frame, text="Feedback",
                  style="Heading.TLabel").grid()

        # add other components
        textbox = ScrolledText(self.content_frame, width=125, height=37)
        textbox.grid(column=0, row=1, padx=30)
        textbox.configure(bg="black")
        textbox.configure(state=tk.DISABLED)
        log_setup(textbox)

        root.add(self.tab, text='   Feedback')

    def onSelect(self):
        """This method is called when the notebook switched the view to this tab."""
        ...
