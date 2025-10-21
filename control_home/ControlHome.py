import time
import os
from os import getcwd
from datetime import date
from tkinter import Canvas, ttk
from tkinter import Button, StringVar, IntVar, Message, Radiobutton, Label, Checkbutton, messagebox, Entry
from Model import Model  # todo back to model
from logging import getLogger, Logger
from modules.logging.log_utils import LOGGER_NAME


class ControlHome:
    """ControlHome class."""
    tab: ttk.Frame
    model: Model
    logger: Logger = getLogger(LOGGER_NAME)

    def __init__(self, root: ttk.Notebook, model: Model):
        """Main Frame and driver for the Control Home tab."""
        self.tab = ttk.Frame(root)
        self.model = model
        self.model.register_view(self)
        # set up and place title and content frames
        self.title_frame = ttk.Frame(self.tab, padding=25)
        self.content_frame = ttk.Frame(self.tab, padding=25)
        self.title_frame.grid(row=0, column=0)
        self.content_frame.grid(row=1, column=0)

        # add title
        ttk.Label(self.title_frame, text="Control Home",
                  style="Heading.TLabel").grid()

        # Visualize motors with circles
        self.spacer = ttk.Label(self.content_frame, text='   ',
                                background="black").grid(row=1, column=0)
        self.circles = Canvas(self.content_frame, width=1000,
                              height=150, background="#777A7A")
        h = 27
        w = 50
        for i in range(10):
            for j in range(3):
                if h >= 150:
                    h = 27
                # create dictionary to easily access motor circles
                self.model.MOT_CIRCLES[i*3 +
                                       j] = self.create_circle(w, h, 20, self.circles)
                h += 50
            w += 100

        self.circles.grid(row=1, column=1, columnspan=10, rowspan=3)
        
        # Message Box
        self.msgvar = StringVar()
        self.msg_box = Message(
            self.content_frame, textvariable=self.msgvar, padx=5, pady=5, width=400)
        self.msgvar.set('Visit the define motors frame to activate motors.')
        # Selections for run button
        self.run = IntVar()
        self.run1 = Radiobutton(
            self.content_frame, text='One Stroke', variable=self.run, value=1)
        self.run2 = Radiobutton(
            self.content_frame, text='Continuous', variable=self.run, value=2)
        self.run1.select()
        self.run.set(1)

        self.prepare_button = ttk.Button(self.content_frame, text='Prepare Motor(s)',
                                         command=lambda: self.prepare_motors(self.run.get(), False))
        # Run Button
        self.start_button = ttk.Button(self.content_frame, text='Start Motor(s)',
                                       command=lambda: self.start_motors(self.run.get(), False))
        # Stop button for motor
        self.stop_button = ttk.Button(
            self.content_frame, text='Stop Motor(s)',  command=lambda: self.stop_motors(self.run.get()))
        self.curve_id_label = Label(self.content_frame, text='Curve ID')
        self.curve_button = ttk.Button(self.content_frame, text='Start Curve',
                                       command=lambda: self.start_motors(self.run.get(), True))
        self.off_and_reset_button = ttk.Button(self.content_frame, text='Off and Reset',
                                               command=lambda: self.off_and_reset())
        self.analytics_checkbox = Checkbutton(
            self.content_frame, text='Record Analytics', command=lambda: self.flip_analytics())

        self.analytics_info = Button(self.content_frame, text='What is This?', command=lambda: self.show_analytics_info())
        self.msg_box.grid(row=7, column=2, columnspan=8,
                          sticky='nsew', pady=20)
        self.run1.grid(row=8, column=5, columnspan=2, sticky='w', pady=(0, 20))
        self.run2.grid(row=8, column=6,  columnspan=2,
                       sticky='w', pady=(0, 20))

        self.prepare_button.grid(row=9, column=5, columnspan=2, sticky='nsew')
        self.start_button.grid(row=10, column=5, columnspan=2, sticky='nsew')
        self.curve_button.grid(row=11, column=5, columnspan=2, sticky='nsew')
        self.stop_button.grid(row=12, column=5, columnspan=2,  sticky='nsew')
        ttk.Label(self.content_frame, text='  ').grid(column=0, row=13)

        self.off_and_reset_button.grid(
            row=14, column=5, columnspan=2, sticky="nesw")
        ttk.Label(self.content_frame, text='  ').grid(column=0, row=15)
        self.analytics_info.grid(row=16, column=6)
        self.analytics_checkbox.grid(row=16, column=5)
        ttk.Label(self.content_frame, text='  ').grid(column=0, row=17)

        # self.progress_bar=Canvas(self.content_frame,bg="white",width = 450,height = 20)    
        # self.progress_bar.place(relx=0.3, rely=1)
        # ttk.Label(self.content_frame, text='  ').grid(column=0, row=18)
        # self.canvas_shape = self.progress_bar.create_rectangle(0,0,0,25,fill = 'green')
        # self.percentage = StringVar()
        # self.percentage.set('0%')
        # self.label_percentage=Label(self.content_frame,textvariable = self.percentage)
        # self.label_percentage.place(relx=0.2, rely=1)

        # Disables start,stop, and curve buttons
        self.disable_run()

        # Label and pack tab
        root.add(self.tab, text=' Control Home')

    def onSelect(self):
        """This method is called when the notebook switched the view to this tab."""
        self.model.check_run_enable()
        if (self.model.RUN_ENABLE):
            self.msgvar.set("Ready to run")
            self.update_button_status()
        if not (self.model.RUN_ENABLE):
            self.disable_run()
        self.color_motors_green()

    def update_msg(self, var:str):
        self.msgvar.set(var)

    def update_button_status(self):
        self.disable_run()
        if (self.model.state == 0):
            self.prepare_button['state'] = 'normal'
        elif (self.model.state == 1):
            #self.curve_button['state'] = 'normal'
            self.start_button['state'] = 'normal'
        else:
            self.stop_button['state'] = 'normal'
    
    def destory_progress_bar(self):
        self.progress_bar.destroy()
        self.label_percentage.destroy()
        msg_box = messagebox.askquestion ('Recording Finished','Do you want to open the analytics data?',icon = 'info')
        if msg_box == 'yes':
            os.startfile(f"{getcwd()}/analytics/{str(date.today())}.txt")

    def create_circle(self, x: int, y: int, r: int, canvasName: Canvas):
        """Method to create circles for motor vizualization. center coordinates are x/y , radius is r."""
        x0 = x - r
        y0 = y - r
        x1 = x + r
        y1 = y + r
        return canvasName.create_oval(x0, y0, x1, y1, fill="white", outline="white")

    def color_motors_green(self):
        """Searches through live motors dictionary and displays motors that are on."""
        for i in range(0, 30):                
                self.circles.itemconfig(
                    self.model.MOT_CIRCLES[i], fill="white")
        for set in self.model.live_motors_sets:
            for key in set.keys():
                self.circles.itemconfig(
                    self.model.MOT_CIRCLES[key], fill="light green")

    ## this is redundant
    def enable_run(self):
        """Enables the button for running the motors and curves."""
        self.prepare_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        self.stop_button['state'] = 'disabled'
        self.curve_button['state'] = 'disabled'

    ##
    def disable_run(self):
        """Disables the button for running the motors and curves."""
        self.prepare_button['state'] = 'disabled'
        self.start_button['state'] = 'disabled'
        self.stop_button['state'] = 'disabled'
        self.curve_button['state'] = 'disabled'

    def prepare_motors(self, motion_type: int, is_curve: bool):
        """Part one of the start sequence. Attempts to write to motors."""
        # self.msgvar.set('Writing attributes to motors...')
        # self.model.attr_write()
        # # TODO: need to determine how long to set this time
        # self.tab.after(2000, lambda: self.home_motors(
        #     motion_type=motion_type, is_curve=is_curve))
        # If all the motors are already written to then skip to homing
        self.prepare_button['state']='disabled'
        if self.model.write_success() and self.model.written_matches_current():
            self.msgvar.set('Motors already written .. skipping to homing.')
            self.tab.after(1000, lambda: self.home_motors(
                motion_type=motion_type))
        else:
            # set message box to writing message
            self.msgvar.set('Writing attributes to motors...')
            self.model.attr_write()
            # TODO: need to determine how long to set this time
            self.tab.after(2000, lambda: self.home_motors(
                motion_type=motion_type))

    def home_motors(self, motion_type: int):
        """Part two of the start sequence. Attempts to home the motors."""
        if self.model.write_success():
            self.msgvar.set('Homing motors...')
            self.model.thread_motor_home()
            
            # ready: bool = True
            # for motor in self.model.live_motors.values():
            #     if not motor.home:
            #         ready = False
            # if ready or not Model.CONNECTED:
            #     # TODO: need to determine how long to set this time
            #     self.tab.after(2000, lambda: self.msgvar.set('Motor(s) prepared'))
            #     ##self.start_button['state'] = 'normal'
            #     ##self.curve_button['state'] = 'normal'
            # else:
            #     self.msgvar.set('Motors not homed, try starting again.')
        else:
            self.msgvar.set('Values were not successfully written to motors.')

    def start_motors(self, motion_type: int, is_curve: bool):
        """Part three of the start sequence. Attempts to run the motors."""
        self.start_button['state'] = 'disabled'
        self.curve_button['state'] = 'disabled'
        ##self.prepare_button['state'] = 'disabled'
        
        # FIX: Check if parameters have changed since last write and re-write them
        # This allows parameter updates after stopping without requiring rehoming
        if not self.model.written_matches_current():
            self.msgvar.set('Parameters changed - updating motors...')
            self.model.attr_write()
            # Wait for write to complete
            self.tab.after(1000, lambda: self._continue_start_motors(motion_type, is_curve))
            return
        
        self._continue_start_motors(motion_type, is_curve)
    
    def _continue_start_motors(self, motion_type: int, is_curve: bool):
        """Continue starting motors after parameter update (if needed)."""
        if self.model.RECORD_ANALYTICS and (motion_type == 2 or is_curve):
            self.update_analytics()
            self.progress_bar=Canvas(self.content_frame,bg="white",width = 450,height = 20)    
            self.progress_bar.place(relx=0.3, rely=1)
            ttk.Label(self.content_frame, text='  ').grid(column=0, row=18)
            self.canvas_shape = self.progress_bar.create_rectangle(0,0,0,25,fill = 'green')
            self.percentage = StringVar()
            self.percentage.set('0%')
            self.label_percentage=Label(self.content_frame,textvariable = self.percentage)
            self.label_percentage.place(relx=0.2, rely=1)
            
        if is_curve:
            self.msgvar.set('Starting curve...')
            self.model.thread_curve()
            # TODO: need to determine how long to set this time
            self.tab.after(2000, lambda: self.msgvar.set('Curve running'))
        else:
            #self.msgvar.set('Starting motors...')
            self.model.thread_motion(motion_type, 0)
            # TODO: need to determine how long to set this time
            #self.tab.after(2000, lambda: self.msgvar.set('Motors running'))
        
        ## may want to wait for the thread to end here
        
        ##self.stop_button['state']='normal'
        ## print(self.model.ANALYTICS_DURATION)

    def stop_motors(self, motion_type: int):
        """Method for stopping motors while running."""
        self.stop_button['state']='disabled'
        self.msgvar.set('Stopping motors...')
        self.model.motion(motion_type, 1)
        self.msgvar.set('Motors stopped')
        ##self.start_button['state'] = 'normal'
        ##self.curve_button['state'] = 'normal'
        ##self.prepare_button['state'] = 'disabled'
        ##self.stop_button['state']='disabled'
    

    def off_and_reset(self):
        self.model.motor_off()
        self.disable_run()
        self.color_motors_green()
        self.msgvar.set('Visit the define motors frame to activate motors.')

    def update_progress_bar(self,percent):
        self.progress_bar.coords(self.canvas_shape,(0,0,int(450*percent),25))
        self.percentage.set('%0.2f %%' % (percent*100))

    def flip_analytics(self):
        self.model.RECORD_ANALYTICS = not self.model.RECORD_ANALYTICS
        self.analytics_interval_var = StringVar(None)
        self.analytics_duration_var = StringVar(None)
        if self.model.RECORD_ANALYTICS:

            self.interval_label = ttk.Label(self.content_frame, text="Record Interval (s)")
            self.analytics_interval_entry = ttk.Entry(self.content_frame, textvariable=self.analytics_interval_var)
            self.duration_label = ttk.Label(self.content_frame, text="Record Time (s)")
            self.analytics_duration_entry = ttk.Entry(self.content_frame, textvariable=self.analytics_duration_var)

            ## self.update_analytics_button = ttk.Button(self.content_frame, text="Update Analytics Info", command=lambda: self.update_analytics())

            self.interval_label.grid(row=17, column=5)
            self.analytics_interval_entry.grid(row=17, column=6)
            self.duration_label.grid(row=18, column=5)
            self.analytics_duration_entry.grid(row=18, column=6)
            ## self.update_analytics_button.grid(row=19, column=5, columnspan=2)
        else:
            if self.interval_label is not None:
                self.interval_label.destroy()
            if self.analytics_duration_entry is not None:
                self.analytics_duration_entry.destroy()
            if self.analytics_interval_entry is not None:
                self.analytics_interval_entry.destroy()
            if self.duration_label is not None:
                self.duration_label.destroy()
            ## if self.update_analytics_button is not None:
                ## self.update_analytics_button.destroy()

    def update_analytics(self):
        
        if self.analytics_interval_var != "":
            try:
                self.model.ANALYTICS_INTERVAL = float(self.analytics_interval_var.get())
                self.logger.info(f"Updated analytics interval to every {self.model.ANALYTICS_INTERVAL} seconds.")
            except:
                self.logger.error("Could not update analytics interval; an illegal value was passed. Make sure to use decimals instead of fractions.")
                self.model.ANALYTICS_INTERVAL = 0.25
        
        if self.analytics_duration_var != "":
            try:
                self.model.ANALYTICS_DURATION = float(self.analytics_duration_var.get())
                self.logger.info(f"Updated analytics duration to {self.model.ANALYTICS_DURATION} total seconds.")
            except:
                self.logger.error("Could not update analytics duration; an illegal value was passed. Make sure to use decimals instead of fractions.")
                self.model.ANALYTICS_DURATION = 10
        self.analytics_duration_var.set(f'{self.model.ANALYTICS_DURATION}')
        self.analytics_interval_var.set(f'{self.model.ANALYTICS_INTERVAL}')

    def show_analytics_info(self):

        msg = """When checked, record analytics will cause the motors to output additional information during runtime. This information will be outputted to an analytics file with the date of the run.

Analytics from multiple runs on the same day will be in the same file, but will be clearly separated.
    
This can only be done when the motors are run continuously.
        
NOTE: Since this information is pulled during runtime, the motors will appear unresponsive, and can't be stopped (right now) while information is being collected. By default, information is collected every 1/4 of a second for 10 seconds. After 10 seconds, the motors can be stopped.

We suggest that you test run your parameters first to ensure they won't fault the machine, then run again with analytics.
    """

        messagebox.showinfo("Record Analytics", msg)
