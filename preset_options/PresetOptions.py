import tkinter as tk
from tkinter import StringVar, ttk, filedialog, simpledialog
from typing import Optional

from preset_options.PresetProcessor import PresetProcessor
from preset_options.Preset import Preset
from Model import Model


class PresetOptions:
    """PresetOptions Class."""

    tab: ttk.Frame
    model: Model
    processor: PresetProcessor
    loadedPreset: Optional[Preset] = None

    def __init__(self, root: ttk.Notebook, model: Model):
        """Main Frame and driver for the Preset Options tab."""

        self.tab = ttk.Frame(root)
        self.model = model
        self.processor = PresetProcessor(self.model)

        # set up and place title and content frames
        self.title_frame = ttk.Frame(self.tab, padding=25)
        self.content_frame = ttk.Frame(self.tab, padding=25)
        self.title_frame.grid(row=0, column=0)
        self.content_frame.grid(row=1, column=0)

        # add title
        ttk.Label(self.title_frame, text="Preset Options",
                  style="Heading.TLabel").grid()

        # set up and place preview and control frames
        self.control_frame = ttk.Frame(self.content_frame)
        self.preview_frame = ttk.Frame(self.content_frame)
        self.control_frame.grid(row=0, column=0, padx=(20, 50))
        self.preview_frame.grid(row=0, column=1)

        # create and place buttons inside control frame, disable apply button
        self.select_button = ttk.Button(
            self.control_frame, text="Select Preset", width=15, command=self.browse)
        self.apply_button = ttk.Button(
            self.control_frame, text='Apply This Preset', width=15, command=lambda: self.apply_preset())
        self.create_button = ttk.Button(
            self.control_frame, text="Create New Preset", width=15, command=self.create_preset)
        self.select_button.grid(column=0, row=0)
        ttk.Label(self.control_frame, text='  ').grid(column=0, row=1)
        self.apply_button.grid(column=0, row=2)
        ttk.Label(self.control_frame, text='  ').grid(column=0, row=3)
        self.create_button.grid(column=0, row=4)
        self.enable_apply_preset()

        # create and place widgets for param preview frame display
        self.param_input_vars = {param: StringVar()
                                 for param in self.model.ALL_PARAMS}
        self.param_input_labels = [ttk.Label(self.preview_frame, text=param, width=10)
                                   for param in self.model.ALL_PARAMS]
        self.param_inputs = [ttk.Label(self.preview_frame, textvariable=self.param_input_vars[param], width=7)
                             for param in self.model.ALL_PARAMS]
        for i in range(3):
            for j in range(6):
                self.param_input_labels[i * 6 +
                                        j].grid(column=i * 2, row=j + 1, padx=15, pady=15)
                self.param_inputs[i * 6 +
                                  j].grid(column=i * 2 + 1, row=j + 1, padx=15, pady=15)

        root.add(self.tab, text='Preset Options')

    def onSelect(self):
        """This method is called when the notebook switched the view to this tab."""
        self.enable_apply_preset()

    def browse(self):
        """Function to browse for desired preset file. Need to change to correct starting directory"""
        filename = filedialog.askopenfilename(
            initialdir='Presets', title="Select a Preset CSV File")
        try:
            self.loadedPreset = self.processor.processPreset(filename)
            for key in self.loadedPreset .all_row:
                self.param_input_vars[key].set(self.loadedPreset .all_row[key])
            self.enable_apply_preset()
        except:
            self.model.LOGGER.debug(
                "Internal Error: Could not open the specified file name.")

    def apply_preset(self):
        if (self.loadedPreset is not None):
            for mot_num, motor in self.model.live_motors.items():
                for key, value in self.loadedPreset.rows[mot_num].items():
                    motor.write_params[key] = value

    def create_preset(self):
        filename = simpledialog.askstring(
            'Create New Preset', 'Enter name of new preset:')
        if type(filename) is str:
            self.processor.create_preset(filename)

    def enable_apply_preset(self):
        if (self.loadedPreset == None):
            self.apply_button['state'] = 'disabled'
        else:
            self.apply_button['state'] = 'normal'
