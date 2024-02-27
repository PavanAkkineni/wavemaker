import tkinter as tk
from tkinter import ttk

from Model import Model

from control_home.ControlHome import ControlHome
from define_motors.DefineMotors import DefineMotors
from preset_options.PresetOptions import PresetOptions
from feedback.Feedback import Feedback
from style import style_GUI


class View:
    """View class."""

    root: tk.Tk
    model: Model

    def __init__(self, model: Model):
        """Sets up the screen and the turtle."""

        # saving the model
        self.model = model

        # basic window configuration
        self.root = tk.Tk()
        self.root.configure(bg='black')
        self.root.geometry('1400x800')
        self.root.title("Wavemaker System Control")

        # set up and use styling defined in style.py
        style_GUI()

        # create ttk Notebook to hold tabs
        self.tabControl = ttk.Notebook(self.root)

        # create the four main tabs
        self.control_home = ControlHome(self.tabControl, model)
        self.define_motors = DefineMotors(self.tabControl, model)
        self.preset_options = PresetOptions(self.tabControl, model)
        self.feedback = Feedback(self.tabControl, model)

        # pack the tabs
        self.tabControl.pack(expand=1, fill="both")

        # Bind to the <<NotebookTabChanged>> event
        self.tabControl.bind("<<NotebookTabChanged>>", self.tabChanged)

        # start the GUI
        self.root.mainloop()

    def tabChanged(self, event):
        """Checks which tab is selected and then runs that tabs onSelect method."""
        sTab: int = self.tabControl.index(self.tabControl.select())

        if sTab == 0:
            self.control_home.onSelect()
        if sTab == 1:
            self.define_motors.onSelect()
        if sTab == 2:
            self.preset_options.onSelect()
        if sTab == 3:
            self.feedback.onSelect()
