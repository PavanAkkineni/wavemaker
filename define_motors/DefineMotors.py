from inspect import trace
from re import S
from tkinter import ttk,  StringVar, IntVar, Checkbutton, Label, Button, Entry, messagebox, OptionMenu, Event, EventType
from typing import Dict, List, Any

from Model import Model
from Motor import Motor
from modules.tooltip import Tooltip
# use partial when making event handlers with arguments
from functools import partial


class DefineMotors:

    tab: ttk.Frame
    model: Model
    isDragging: bool = False

    dragCoords: List[int] = [-1, -1, -1, -1]
    root: ttk.Notebook  # need to hold a copy of the root for mouse position

    selected_motors: List[Motor]

    def __init__(self, root: ttk.Notebook, model: Model):
        """Main Frame and driver for the Define Motors ab."""
        self.model = model
        self.root = root

        self.tab = ttk.Frame(root)

        # set up and place title and content frames
        self.title_frame = ttk.Frame(self.tab, padding=(25, 25, 0, 0))
        self.content_frame = ttk.Frame(self.tab, padding=25)
        self.title_frame.grid(row=0, column=0)
        self.content_frame.grid(row=1, column=0)

        # add title
        ttk.Label(self.title_frame, text="Define Motors",
                  style="Heading.TLabel").grid()

        # add and place content frames
        self.movement_frame = ttk.Frame(self.content_frame)
        self.param_frame = ttk.Frame(self.content_frame)

        self.motor_frame = ttk.Frame(self.content_frame, borderwidth=15)
        self.motor_frame.bind('<B1-Motion>', self.startDragSelect)
        self.motor_frame.bind('<ButtonRelease-1>', self.endDragSelect)
        #self.motor_frame.grid(row=0, column=0)

        self.button_frame = ttk.Frame(self.content_frame)
        #self.button_frame.grid(row=1, column=0)

        self.motor_frame.grid(row=0)
        self.button_frame.grid(row=1)
        self.movement_frame.grid(row=2)
        self.param_frame.grid(row=3)

        # Create Widgets for self.motor_frame

        self.intVars = [IntVar() for _ in range(30)]
        self.checkButtons: List[Checkbutton] = []
        self.checkButtonTips: List[Tooltip] = []
        for i in range(30):
            self.checkButtons.append(Checkbutton(
                self.motor_frame, text=f'Motor {i}', variable=self.intVars[i], command=partial(model.onCheck, i, self.intVars[i])))
            self.model.motdict[i] = 0
            self.checkButtonTips.append(
                Tooltip(self.checkButtons[i], "Deactivated"))

        # Place widgets in self.motor_frame
        for i in range(10):
            for j in range(3):
                self.checkButtons[i * 3 +
                                  j].grid(row=j + 1, column=i+1, padx=(0, 10), pady=5)

        root.update()  # update assigns pixel coordinates for checkbuttons.

        self.define_button_moved = ttk.Button(self.button_frame,  text="Add Selected Motors to Set",
                                              command=lambda: self.motor_define()).grid(row=0, column=0)
        ttk.Label(self.button_frame, text='     ').grid(row=0, column=1)
        self.off_and_reset = ttk.Button(self.button_frame, text="Turn Off Live Motors and Reset",
                                        command=lambda: self.motor_off()).grid(row=0, column=2)
        ttk.Label(self.button_frame, text='     ').grid(row=0, column=3)

        # Create Widgets for self.movement_frame
        self.curr_set_label = ttk.Label(self.movement_frame,
                                  text='Activated Sets: ')
        
        self.setsStringVar = StringVar()
        
        self.sets_label = ttk.Label(self.movement_frame, text=self.setsStringVar.get())
        self.confirm_sets_button = ttk.Button(self.button_frame, text = 'Confirm Set', command=lambda: self.confirm_select(), state='disabled')

        self.param_button = ttk.Button(self.button_frame, text='(Parameter Details)',
                                       command=lambda: self.param_info_click())
        
                # create specification dropdown
        # self.specify_type_menu = StringVar()
        # self.specify_type_menu.set("Select Specification Method")
        # self.specify_type = OptionMenu(
        #     self.movement_frame, self.specify_type_menu, "Define All Live", "Define All Selected", "Define by Row", "Define by Column", command=self.specify_type_select)
        self.selected_motors = []
        self.specify_rc = None

        # Place widgets in self.movement_frame
        self.curr_set_label.grid(column=0, row=0, pady=30)
        self.sets_label.grid(column=1,row=0)
        #self.specify_type.grid(column=2, row=0, padx=(0, 30), pady=15)
        self.param_button.grid(column=4, row=0, padx=(0, 30))
        self.confirm_sets_button.grid(column=5,row=0,padx=(0,30))

        # create Widgets for self.param_frame
        self.param_input_labels = [ttk.Label(self.param_frame, text=param)
                                   for param in self.model.ALL_PARAMS]
        for i, param_tip in enumerate(self.model.ALL_PARAM_TIPS):
            Tooltip(self.param_input_labels[i], param_tip)
            self.param_input_labels[i]

        self.param_input_vars = {param: StringVar()
                                 for param in self.model.ALL_PARAMS}
        self.param_inputs = [ttk.Entry(self.param_frame, textvariable=self.param_input_vars[param])
                             for param in self.model.ALL_PARAMS]
        for param in self.model.ALL_PARAMS:
            self.param_input_vars[param].trace_add(
                'write', partial(self.update_motor_write_params, param=param))

        # Parameter Info
        self.position_msg = 'Position limits after homing are 370mm and - 20 mm \n\n'
        self.velocity_msg = 'Velocity limits are 0 and approx. 900 mm/sec. Dependant on Current(A) usage\n\n'
        self.accel_msg = 'Acceleration and Deceleration are limited at 50,000 mm/s^2\n\n'
        self.jerk_msg = 'Jerk in general should be larger than the Acceleration and Deceleration mm/s^3\n\n'
        self.profile_msg = 'Profile: Trapazoidal(0) Bestehorn(1) S-Curve(2) Sin(3)\n\n'
        self.movtype_msg = 'Move Type: Absolute(0): Based on defined axis. Incremental(1): Moves the amount specified in position argument'

        # Place widgets in self.param_frame
        for i in range(3):
            for j in range(6):
                self.param_input_labels[i * 6 +
                                        j].grid(column=i * 2, row=j + 1, padx=15, pady=15)
                self.param_inputs[i * 6 +
                                  j].grid(column=i * 2 + 1, row=j + 1, padx=15, pady=15)

        # Disable button in movement frame if the on/off buttons aren't enabled
        #self.movement_frame_enable()
        self.param_frame_enable()
        self.color_buttons_green()

        # Add tab name for Define Motors
        root.add(self.tab, text=' Define Motors')

    def onSelect(self):
        """This method is called when the notebook switched the view to this tab."""
        self.update_checkbutton_tips()
        self.param_frame_enable()
        self.color_buttons_green()        

    def specify_type_select(self, selected):
        #THIS FUNCTIONALITY HAS BEEN REMOVED
        """This method is called when a new type is selected in the specify type dropdown."""
        if not self.specify_rc == None:
            self.specify_rc.destroy()
        if selected == "Define All Live":
            self.selected_motors = [
                motor for motor in self.model.live_motors.values()]
            if len(self.selected_motors) > 0:
                for param in self.param_input_vars:
                    self.param_input_vars[param].set(
                        str(self.selected_motors[0].write_params[param]))
            self.param_frame_enable()
        if selected == "Define All Selected":
            self.selected_motors = []
            for mot_num in self.model.motdict:
                if self.model.motdict[mot_num] == 1:
                    if mot_num in self.model.live_motors:
                        self.selected_motors.append(
                            self.model.live_motors[mot_num])
            if len(self.selected_motors) > 0:
                for param in self.param_input_vars:
                    self.param_input_vars[param].set(
                        str(self.selected_motors[0].write_params[param]))
            self.param_frame_enable()
        # TODO: get rid of extra menus when not used
        if selected == "Define by Row":
            self.selected_motors = []

            self.specify_row_menu = StringVar()
            self.specify_row_menu.set('Select Row')
            rows: List[int] = self.model.get_rows()
            row_strings: List[str] = []
            for i in rows:
                row_strings.append(f"Row {i}")
            self.specify_rc = OptionMenu(
                self.movement_frame, self.specify_row_menu, *(row_strings), command=self.specify_row_select)
            self.specify_rc.grid(column=3, row=0, padx=15,
                                 pady=15, )
            self.param_frame_enable()

        if selected == "Define by Column":
            self.selected_motors = []

            self.specify_row_menu = StringVar()
            self.specify_row_menu.set('Select Column')
            columns: List[int] = self.model.get_columns()
            column_strings: List[str] = []
            for i in columns:
                column_strings.append(f"Column {i}")
            self.specify_rc = OptionMenu(
                self.movement_frame, self.specify_row_menu, *(column_strings), command=self.specify_column_select)

            self.specify_rc.grid(column=3, row=0, padx=15,
                                 pady=15)
            self.param_frame_enable()

    def specify_row_select(self, selected):
        row: int = int(selected[4])
        self.selected_motors = self.model.get_row(row)
        if len(self.selected_motors) > 0:
            for param in self.param_input_vars:
                self.param_input_vars[param].set(
                    str(self.selected_motors[0].write_params[param]))
        self.param_frame_enable()

    def specify_column_select(self, selected):
        column: int = int(selected[7])
        self.selected_motors = self.model.get_column(column)
        if len(self.selected_motors) > 0:
            for param in self.param_input_vars:
                self.param_input_vars[param].set(
                    str(self.selected_motors[0].write_params[param]))
        self.param_frame_enable()

    def param_info_click(self):
        messagebox.showinfo("Parameter Details", self.position_msg + self.velocity_msg +
                            self.accel_msg + self.jerk_msg + self.profile_msg + self.movtype_msg)

    def motorSet_to_string(self):
        formatted_output = ""
        for index, motor_dict in enumerate(self.model.live_motors_sets):
            formatted_output += f"Set {index +1}: Motors {list(motor_dict.keys())}\n"
        return formatted_output
    
    def confirm_set_confirmation(self):
        res = messagebox.askquestion("Check before proceeding!", "Are you sure the parameter values you entered are correct? \n You will need to clear all sets and re-enter parameters if not!")
        if res == 'yes':
            return True
        if res == 'no':
            return False
            

    def confirm_select(self):
        if(self.confirm_set_confirmation()): 
            self.model.live_motors_sets.append(self.model.live_motors.copy())
            self.confirm_sets_button['state'] = 'disabled'
            self.selected_motors = []
            for mot_num in self.model.motdict:
                if self.model.motdict[mot_num] == 1:
                    if mot_num in self.model.live_motors:
                        self.selected_motors.append(
                            self.model.live_motors[mot_num])
                        self.model.motdict[mot_num] = 2
                        self.checkButtons[mot_num]['bg'] = 'pink'
            if len(self.selected_motors) > 0:
                for param in self.param_input_vars:
                    self.param_input_vars[param].set(
                        str(self.selected_motors[0].write_params[param]))            
            self.param_frame_enable()
            self.setsStringVar.set(self.motorSet_to_string())
            self.sets_label.config(text = self.setsStringVar.get())
            print(self.model.motdict)
            print(self.selected_motors)
            print(self.model.live_motors)


    def motor_define(self):
        """Calls motor_define on model then updates UI upon response."""
        self.model.motor_define()
        self.confirm_sets_button['state'] = 'enable'
        self.update_checkbutton_tips()
        #self.movement_frame_enable()
        self.color_buttons_green()

    def update_checkbutton_tips(self):
        for i in range(30):
            self.checkButtonTips[i].updateText('Unactivated')
        for set in self.model.live_motors_sets:
            for key in set.keys():
                self.checkButtonTips[key].updateText(
                    set[key].generate_writter_param_str())

    def update_motor_write_params(self, *args, param) -> Any:
        """When a param is edited, update the write_params of all relevant motors."""
        new_val: str = self.param_input_vars[param].get()
        if new_val.lstrip('-').isnumeric():
            int_val: int = int(new_val)
            # FIXED: Only update motors that are currently being edited (selected_motors and live_motors)
            # This prevents parameter changes from affecting already-confirmed motor sets
            # Update motors in the working selection
            for motor in self.selected_motors:
                motor.write_params[param] = int_val
            # Update motors in live_motors (before they're confirmed to a set)
            for motor in self.model.live_motors.values():
                motor.write_params[param] = int_val
            self.update_checkbutton_tips()

    def motor_off(self):
        """Calls motor_off on model then updates UI upon response."""
        #TODO - CHANGE sets label according to this
        self.model.motor_off()
        for i in range(len(self.checkButtons)):
            if i in self.model.motdict:
                # turn motor off in motdict if it was checked
                self.model.motdict[i] = 0
            self.checkButtons[i].deselect()
        if self.model.CONNECTED:
            self.model.live_motor_reset()
        else:
            self.model.mock_live_motor_reset()
        self.model.live_motors_sets.clear()
        self.setsStringVar.set("")
        self.sets_label.config(text = self.setsStringVar.get())
        self.color_buttons_green()
        self.update_checkbutton_tips()
        self.param_frame_enable()
        #self.movement_frame_enable()

    # def movement_frame_enable(self):
    #     if len(self.model.live_motors) >= 1:
    #         self.specify_type['state'] = 'normal'
    #     else:
    #         self.specify_type['state'] = 'disabled'

    def show_current_param_values(self):
        ...
        # FIX: Show parameters from confirmed sets, not just live_motors
        # This ensures parameter fields display correct values for all motors
        motors_to_show = []
        
        # First check if there are motors in sets
        if len(self.model.live_motors_sets) > 0:
            for motor_set in self.model.live_motors_sets:
                motors_to_show.extend(motor_set.values())
        # Otherwise check live_motors
        elif self.model.live_motors != {}:
            motors_to_show = list(self.model.live_motors.values())
        
        if len(motors_to_show) > 0:
            for param in self.param_input_vars:
                self.param_input_vars[param].set(
                    str(motors_to_show[0].write_params[param]))

    def param_frame_enable(self):
        # FIX: Enable parameter editing if there are motors in sets OR live_motors
        # This allows parameter changes after motors are confirmed into sets
        has_motors = (self.model.live_motors != {}) or (len(self.model.live_motors_sets) > 0)
        
        if has_motors:
            for param in self.param_inputs:
                param['state'] = 'normal'
            self.show_current_param_values()
        else:
            for param in self.param_inputs:
                param['state'] = 'disabled'

    def color_buttons_green(self):
        for button in self.checkButtons:
            button['bg'] = 'light grey'
        for set in self.model.live_motors_sets:
            for key in set.keys():
                self.checkButtons[key]['bg'] = 'pink'
        for mot, value in self.model.motdict.items():
            if value == 2:
                self.checkButtons[mot]['bg'] = 'pink'
        for key in self.model.live_motors:
            self.checkButtons[key]['bg'] = 'light green'

    def startDragSelect(self, event):
        if self.isDragging:
            return
        else:
            # set start coords
            self.dragCoords[0] = self.root.winfo_pointerx()  # startX
            self.dragCoords[1] = self.root.winfo_pointery()  # startY
            self.isDragging = True

    def endDragSelect(self, event):
        if not self.isDragging:
            return
        else:
            # set end coords, calculate containing checkboxes, and select them. reset dragging afterwards
            self.dragCoords[2] = self.root.winfo_pointerx()  # endX
            self.dragCoords[3] = self.root.winfo_pointery()  # endY

            startX = self.dragCoords[0]
            startY = self.dragCoords[1]
            endX = self.dragCoords[2]
            endY = self.dragCoords[3]

            if(startX > endX):
                temp = startX
                startX = endX
                endX = temp

            if(startY > endY):
                temp = startY
                startY = endY
                endY = temp

            for i in range(30):
                checkX = self.checkButtons[i].winfo_rootx(
                ) + (self.checkButtons[i].winfo_width() // 2)
                checkY = self.checkButtons[i].winfo_rooty(
                ) + (self.checkButtons[i].winfo_height() // 2)

                if(startX < checkX < endX and startY < checkY < endY):
                    self.checkButtons[i].invoke()

            self.dragCoords = [-1, -1, -1, -1]
            self.isDragging = False
