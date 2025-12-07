from tkinter import IntVar
import time
from typing import Any, Dict, List
from modules.eip import PLC
from threading import Lock, Thread
from logging import getLogger, Logger
from modules.logging.log_utils import LOGGER_NAME
from Motor import Motor
from os import getcwd
from datetime import date
from database.database import query_database, update_database

# Authors / Changes Made: TEAM D, COMP523 Fall 23

class Model:
    """Model class for organization of all motor and state variables."""
    IP_ADDRESS: str = '192.168.1.1'
    PROCESSOR_SLOT: int = 1
    LOGGER: Logger = getLogger(LOGGER_NAME)
    ALL_PARAM_TIPS: List[str] = ['Position limits after homing are 370mm and - 20 mm',
                                 'Position limits after homing are 370mm and - 20 mm',
                                 'Velocity limits are 0 and approx. 900 mm/sec. \nDependant on Current(A) usage',
                                 'Velocity limits are 0 and approx. 900 mm/sec. \nDependant on Current(A) usage',
                                 'Acceleration and Deceleration are limited at 50,000 mm/s^2',
                                 'Acceleration and Deceleration are limited at 50,000 mm/s^2',
                                 'Acceleration and Deceleration are limited at 50,000 mm/s^2',
                                 'Acceleration and Deceleration are limited at 50,000 mm/s^2',
                                 'Jerk in general should be larger than the Acceleration and Deceleration mm/s^3',
                                 'Jerk in general should be larger than the Acceleration and Deceleration mm/s^3',
                                 'Default to 0',
                                 'Default to 0',
                                 'Trapazoidal(0) \nBestehorn(1) \nS-Curve(2) \nSin(3)',
                                 'Absolute(0): Based on defined axis. \nIncremental(1): Moves the amount specified in position argument',
                                 'Used for curves.',
                                 'Used for curves.',
                                 'Used for curves.',
                                 'Used for curves.']

    ALL_PARAMS: List[str] = ['Position 1', 'Position 2', 'Speed 1', 'Speed 2', 'Accel 1', 'Accel 2', 'Decel 1', 'Decel 2', 'Jerk 1',
                             'Jerk 2', 'Time 1', 'Time 2', 'Profile', 'Move Type', 'Curve ID', 'Time Scale', 'Amplitude Scale', 'Curve Offset']

    # VISUAL STATE VARIABLES
    # diables start, stop and curve buttons when false
    RUN_ENABLE: bool = False
    # Dictionary of motor circles vizualized, key is motor num, value is ID in canvas
    MOT_CIRCLES: Dict[int, Any]

    # MODEL STATE VARIABLES
    # on GUI startup the model determines if it is connected to motors
    CONNECTED: bool = False
    # which motors to interact with. This can also house non active motors
    RECORD_ANALYTICS: bool = False
    ANALYTICS_INTERVAL: float = 0.25
    ANALYTICS_DURATION: float = 10.0

    motdict: Dict[int, int]
    # The list of motors which are active
    live_motors: Dict[int, Motor]
    live_motors_sets: List[Dict[int, Motor]]
    live_motors_params: List[Dict[str, int]]
    # Dictionary of attributes associated with each motor,column, or row
    attrcat: Dict[int, Dict[str, IntVar]]
    # Dictionary of attributes from CSV
    csvattrcat:  Dict[str, str]
    # Used for reading in csv
    csvlist: List[Dict[str, str]]

    # Motor on lock
    on_lock: Lock
    # Motor off lock
    off_lock: Lock
    # Motor home lock
    home_lock: Lock
    # Curve Lock
    curve_lock: Lock

    def __init__(self):
        """Initializes all state variables, connects to database, and runs live_motor_reset."""
        self.motdict = {}
        self.live_motors = {}
        self.live_motors_sets=[]
        self.attrcat = {}
        self.csvattrcat = {}
        self.csvlist = []
        self.MOT_CIRCLES = {}

        self.on_lock = Lock()
        self.off_lock = Lock()
        self.home_lock = Lock()
        self.curve_lock = Lock()

        # UNPREPARED_STATE:0, HOMED_STATE:1, RUNNING_STATE:2
        self.state = -1
        # Flag to track when homing is in progress (prevents button re-enabling during tab switch)
        self.is_homing = False

        # Reset Live motor array on the PLC to all 0s to ensure only operating on intended motors
        # If the live_motor_reset fails then the motors are not actually connected
        # we then set CONNECTED to false and run the program in a mock state
        try:
            self.live_motor_reset()
            self.CONNECTED = True
        except:
            self.CONNECTED = False

    # Runs when any checkButton is ticked, creates motdict: {motor number: ON/OFF (1/0)}
    def onCheck(self, motnum: int, IO: IntVar):
        if(self.motdict[motnum] != 2):
            self.motdict[motnum] = IO.get()

    def check_run_enable(self):
        if (len(self.live_motors_sets) == 0) and (len(self.live_motors) == 0):
            self.RUN_ENABLE = False
        else:
            for set in self.live_motors_sets:
                for motor in set.values():
                    self.RUN_ENABLE = True
                    if not motor.valid_write_dict():
                        self.RUN_ENABLE = False

    def write_success(self) -> bool:
        """Check if ALL motors in all sets were successfully written to."""
        for motor_set in self.live_motors_sets:
            for motor in motor_set.values():
                if not motor.write_success:
                    return False
        return True  # Only return True after checking ALL motors in ALL sets

    def written_matches_current(self) -> bool:
        """Check if write_params match current_params for ALL motors in all sets."""
        for motor_set in self.live_motors_sets:
            for motor in motor_set.values():
                for attr in motor.write_params:
                    # If current_params doesn't have this attr, it was never written
                    if attr not in motor.current_params:
                        return False
                    if motor.write_params[attr] != motor.current_params[attr]:
                        return False
        return True  # Only return True after checking ALL motors in ALL sets


    def register_view(self, view):
        self.view = view

    def register_define_motors_view(self, define_motors_view):
        self.define_motors_view = define_motors_view

    def notify_view(self):
        self.view.update_button_status()
        # Also notify DefineMotors view if registered
        if hasattr(self, 'define_motors_view') and self.define_motors_view is not None:
            self.define_motors_view.update_stop_button_status()

    def motor_on(self):
        """Flip the boolean motor on switch in the PLC code."""
        #self.on_lock.acquire()
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = self.IP_ADDRESS
                comm.ProcessorSlot = self.PROCESSOR_SLOT
                motor_on_bool = comm.Read('Program:Wave_Control.Motor_Boot')
                # Writes a 1 to the boolean switch Motor_Boot. The PLC code then executes this command
                comm.Write('Program:Wave_Control.Motor_Boot', 1)
                # wait 5 seconds for the command to happen
                time.sleep(5)
                # Write a 0 to the boolean switch Motor_Boot to stop execution
                comm.Write('Program:Wave_Control.Motor_Boot', 0)
                self.LOGGER.log(15, 'Motor(s) turned ON')
        else:
            self.LOGGER.log(15, 'Motor(s) mock turned ON')
        self.RUN_ENABLE = True
        #self.on_lock.release()

    def motor_off(self):
        """Turning off the motors also calls an error clearing method in the PLC code.
        To clear errors the motor_off function should be called.
        It should be called before turning on the motors to clear errors."""
        self.off_lock.acquire()
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = self.IP_ADDRESS
                comm.ProcessorSlot = self.PROCESSOR_SLOT
                # Writes a 1 to the boolean switch Clear_Motor_Error. The PLC executes the correspinding code
                comm.Write('Program:Wave_Control.Clear_Motor_Error', 1)
                # Wait 5 seconds
                time.sleep(5)
                # Turn the Clear_Motor_Error switch off.
                comm.Write('Program:Wave_Control.Clear_Motor_Error', 0)
                self.LOGGER.info(
                    "Motor(s) Turned Off and Motion Faults Cleared")
                # Call motion method to stop motors and reset the run Rung in Studio 5000
                # The 2 for Run_2 and the 1 for tracker
                self.motion(2, 1)
                comm.Write('Program:Wave_Control.Run_1', 0)
                comm.Write('Program:Wave_Control.Run_2', 0)
                comm.Write('Program:Wave_Control.Clear_Motor_Error', 0)
                comm.Write('Program:Wave_Control.Home_Button', 0)
                comm.Write('Program:Wave_Control.Run_Curve', 0)
            self.live_motor_reset()
        else:
            self.live_motor_reset_mock()
            time.sleep(5)
            self.LOGGER.info(
                "Motor(s) mock Turned Off and Motion Faults Cleared")
        self.RUN_ENABLE = False
        self.off_lock.release()


    def thread_motor_home(self):
        self.is_homing = True  # Set flag before starting homing thread
        Thread(target=self.motor_home).start()

    def motor_home(self):
        """Needs to check if the motors have reached home.
        This check will come from calling on each of the motors as they have been defined in the motor class.
        Live_Motors is a dictionary where each key corresponds to an instance of the motorclass."""
        #self.home_lock.acquire()
        # exexcuted twice to prevent homing at a wrong position
        # need further investigation on why will the piston home on a certain high position
        for count in range(2):
            # Keeping track of how many motors have successfuly homed
            motCount: int = 0
            # Keeping track of how many times the While loop has executed
            looptrack: int = 0
            # How many times the While loop will complete before breaking out of the loop
            loopend: int = 5  *count + 1
            # Tracking variable to help decide which branch to go down
            tracker: int = 0
            if self.CONNECTED:
                with PLC() as comm:
                    comm.IPAddress = self.IP_ADDRESS
                    comm.ProcessorSlot = self.PROCESSOR_SLOT
                    comm.Write('Program:Wave_Control.Home_Button', 0)
                    time.sleep(5)
                    # Reads the value of the home motor button in the PLC code, 0 is off 1 is on
                    home_bool = comm.Read('Program:Wave_Control.Home_Button')
                    #print(home_bool)
                    if home_bool == 0 and tracker == 0:
                        comm.Write('Program:Wave_Control.Home_Button', 1)
                        tracker = 1

                    while tracker == 1:
                        # Wait 5 sec before begining loop and in between loops
                        looptrack = looptrack+1
                        self.view.update_msg(f'Homing Motor(s) {count+1} trial ({looptrack*5}/20)')
                        # A command to keep contacting the PLC so do not lose connection
                        comm.GetProgramTagList('Program:Wave_Control')
                        time.sleep(5)
                        motCount = 0
                        for set in self.live_motors_sets:
                            for motor in set.values():
                                # homed is a method of the motor class which checks the Status Word bit for if the motor is in a home position
                                if motor.homed(self.IP_ADDRESS, self.PROCESSOR_SLOT) == True:
                                    motCount += 1

                        total_keys = sum(len(d) for d in self.live_motors_sets)
                        if motCount == total_keys:
                            comm.Write('Program:Wave_Control.Home_Button', 0)
                            tracker = 0
                            if count == 1:
                                self.LOGGER.info('Motor(s) Homed')
                                self.state = 1
                                self.is_homing = False  # Clear before notify
                                self.notify_view()
                                self.view.update_msg('Motor(s) Homed')
                            break

                        if looptrack > loopend:
                            comm.Write('Program:Wave_Control.Home_Button', 0)
                            if count == 1:
                                self.is_homing = False  # Clear before notify
                                self.notify_view()
                                self.view.update_msg('Unable to Home Motors: Execution timed out after 40 sec')
                                self.LOGGER.error('Unable to Home Motors: Execution timed out after 40 sec')
                            break
            else:
                time.sleep(5)
                self.LOGGER.info('Motor(s) mock Homed')
                self.state = 1
                self.is_homing = False  # Clear before notify
                self.notify_view()
        
        # Ensure homing flag is cleared (safety fallback)
        self.is_homing = False
        #self.home_lock.release()

    def motor_define(self):
        """Uses the dictionary of motor number and whether it is on or off. Dependant on motor class"""
        # initializes the motor class for the motors specified by the dictionary motdict
        if (len(self.motdict) == 0):
            self.RUN_ENABLE = False
        for key, value in self.motdict.items():
            print(self.motdict)
            if value == 1:
                # Create the instance of the motor class
                LiveMotor = Motor(key, self.CONNECTED)
                # Associate that instance of the motor class with the motor number in a dictionary
                self.live_motors[LiveMotor.axis_ID] = LiveMotor
                print(self.live_motors)
                #print(self.live_motor_sets)
                # Change the boolean switch in the PLC code to correspond with Live_Motors
                if self.CONNECTED:
                    with PLC() as comm:
                        comm.IPAddress = self.IP_ADDRESS
                        comm.ProcessorSlot = self.PROCESSOR_SLOT
                        comm.Write(
                            'Program:Wave_Control.Live_Motors.{0}'.format(key), value)
            # The value in motdict is 0. So the motor should be turned off and deleted from the Live_Motor dict
            if value == 2:
                # Create the instance of the motor class
                LiveMotor = Motor(key, self.CONNECTED)
                # Associate that instance of the motor class with the motor number in a dictionary
                print(self.live_motors)
                if (key in self.live_motors.keys()):
                    del self.live_motors[key]
                # Change the boolean switch in the PLC code to correspond with Live_Motors
                if self.CONNECTED:
                    with PLC() as comm:
                        comm.IPAddress = self.IP_ADDRESS
                        comm.ProcessorSlot = self.PROCESSOR_SLOT
                        comm.Write(
                            'Program:Wave_Control.Live_Motors.{0}'.format(key), value)
            # The value in motdict is 0. So the motor should be turned off and deleted from the Live_Motor dict
            if value == 0:
                if key in self.live_motors:
                    # turns off the motor as defined by the key from motdict
                    if self.CONNECTED:
                        with PLC() as comm:
                            comm.IPAddress = self.IP_ADDRESS
                            comm.ProcessorSlot = self.PROCESSOR_SLOT
                            comm.Write(
                                'Program:Wave_Control.Live_Motors.{0}'.format(key), value)
                    # Deletes the entry from the Live_Motors dictionary
                    del self.live_motors[key]
        ##self.motor_off()
            
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = self.IP_ADDRESS
                comm.ProcessorSlot = self.PROCESSOR_SLOT
                comm.Write('Program:Wave_Control.Clear_Motor_Error', 1)
                time.sleep(5)
                comm.Write('Program:Wave_Control.Clear_Motor_Error', 0)

        self.motor_on()


    def thread_motion(self, stroke, tracker):
        Thread(target=self.motion, args=(stroke, tracker,)).start()

    def record_positions(self,comm):
        # Starting dictionary for data to input database
        db_data = {}

        handle = open(
            f"{getcwd()}/analytics/{str(date.today())}.txt", "a+")
        i = 0
        max_runs = 10000
        runs = 0
        handle.write("\n" + "----- Run " + str(time.asctime()) + "-----\n" + "                 ")
        for set in self.live_motors_sets:
            for motor in set:
                # DO NOT DELETE
                # Creating aux_str to label motor
                aux_str = "Motor "+str(motor)

                # Creating entry in db_data
                db_data[aux_str] = {}

                handle.write(f"motor {motor:<18d}")
        handle.write("\n"+"t           ")
        for motor in self.live_motors:
            handle.write("demand      actual      ")
        handle.write("\n")
        while i < self.ANALYTICS_DURATION and runs < max_runs:
            self.view.update_progress_bar(i/self.ANALYTICS_DURATION)
            handle.write(f"{i:7.4f}")
            for motor in self.live_motors:
                demandPositon: Any = comm.Read('Program:Wave_Control.Axis[{0}].ComDemandPosition'.format(
                    motor))
                actualPosition: Any = comm.Read(
                    'Program:Wave_Control.Axis[{0}].ComActualPosition'.format(motor))
                displacement = abs(demandPositon - actualPosition)

                # DO NOT DELETE
                # Recreating aux_str to access keys in db_data
                aux_str = "Motor "+str(motor)
                
                # aux_str2 to access interval
                aux_str2 = str(i)

                # Adding the data to db_data
                db_data[aux_str][aux_str2] = {"Actual Position": actualPosition, "Expected Position": demandPositon, "Displacement": displacement}

                handle.write(f"{demandPositon:>12d}{actualPosition:>12d}")
            runs += 1
            handle.write("\n")
            time.sleep(self.ANALYTICS_INTERVAL)
            i += self.ANALYTICS_INTERVAL

        # DO NOT DELETE
        # Adding data to the database
        update_database(str(time.asctime()), self.ANALYTICS_INTERVAL, self.ANALYTICS_DURATION, db_data)

        self.view.destory_progress_bar()
        handle.close()

    def motion(self, stroke, tracker):
        """This command will commence motion.
        Stroke should be a 1 or 2 depending on if a single stroke is wanted or cyclical motion."""

        # For a single stroke, stroke = 1. Run_1 is set to true on the PLC and the code runs. 5 seconds later Run_1 is set False
        if stroke == 1:
            if tracker == 1:
                self.LOGGER.warning(
                    'Motor(s) are already STOPPED on single stroke run')
                # FIX: Keep state as HOMED (1) - motors are stopped but still homed
                if self.state == -1:
                    self.state = 0  # Never prepared, need to prepare
                else:
                    self.state = 1  # Already homed, can run again
                self.notify_view()
            else:
                if self.CONNECTED:
                    with PLC() as comm:
                        comm.IPAddress = self.IP_ADDRESS
                        comm.ProcessorSlot = self.PROCESSOR_SLOT
                        comm.Write('Program:Wave_Control.Run_1', 1)
                        self.view.update_msg('Motor(s) Running')
                        time.sleep(5)
                        comm.Write('Program:Wave_Control.Run_1', 0)
                        self.view.update_msg('Motor(s) Stopped')
                        self.LOGGER.log(15, 'Motor(s) single stroke STARTED')
                        # FIX: Keep state as HOMED (1) after single stroke completes
                        self.state = 1  # Can run another stroke without re-homing
                        self.notify_view()
                        self.view.curve_button['state'] = 'normal'
                else:
                    self.LOGGER.log(15, 'Motor(s) single stroke mock STARTED')
                    # FIX: Keep state as HOMED (1) after single stroke in mock mode
                    self.state = 1  # Can run another stroke without re-homing
                    self.notify_view()
                    ##time.sleep(5)
        # For cyclical strokes, stroke = 2. Run_2 is set true. If Motion is called again it needs the second argument tracker.
        # When tracker = 1 a 0 is written to Run_2, turning off the motion
        elif stroke == 2:
            if self.CONNECTED:
                with PLC() as comm:
                    comm.IPAddress = self.IP_ADDRESS
                    comm.ProcessorSlot = self.PROCESSOR_SLOT
                    comm.Write('Program:wave_Control.Run_2', 1)
                    self.LOGGER.log(15, 'Motor(s) continuous STARTED')
                    
                    if tracker == 1:
                        comm.Write('Program:Wave_Control.Run_2', 0)
                        self.LOGGER.log(15, 'Motor(s) STOPPED')
                        # FIX: Keep state as HOMED (1) after stopping, not UNPREPARED (0)
                        # Motors are still homed, just stopped - can restart without re-homing
                        if self.state == -1:
                            self.state = 0  # Never prepared, need to prepare
                        else:
                            self.state = 1  # Already homed, can restart directly
                            self.notify_view()
                    else:
                        self.state = 2
                        self.notify_view()
                        self.view.update_msg('Motor(s) Running')
                        if(self.RECORD_ANALYTICS):
                            # this could be expanded to other analytics.
                            self.record_positions(comm)
            else:
                if tracker == 1:
                    self.LOGGER.log(15, 'Motor(s) mock STOPPED')
                    # FIX: Keep state as HOMED (1) after stopping in mock mode
                    # Motors are still homed, just stopped - can restart without re-homing
                    if self.state == -1:
                        self.state = 0  # Never prepared, need to prepare
                    else:
                        self.state = 1  # Already homed, can restart directly
                    self.notify_view()
                else:
                    # i = 0
                    # while i < 60:
                    #     time.sleep(0.25)
                    #     i += 1
                    self.LOGGER.log(15, 'Motor(s) mock STARTED')
                    self.state = 2
                    self.notify_view()
                    i=0
                    while i < self.ANALYTICS_DURATION:
                        time.sleep(1)
                        
                        i+=self.ANALYTICS_INTERVAL
                        self.view.update_progress_bar(i/self.ANALYTICS_DURATION)
                    self.view.destory_progress_bar()
        else:
            self.LOGGER.error(
                'Failed to start motors. Make sure you\'ve selected either single stroke or continuous.')

    def thread_curve(self):
        Thread(target=self.curve).start()

    def curve(self):
        #self.curve_lock.acquire()
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = self.IP_ADDRESS
                comm.ProcessorSlot = self.PROCESSOR_SLOT
                curve_bool = comm.Read('Program:Wave_Control.Run_Curve')

                if curve_bool == 1:
                    self.LOGGER.warning(
                        'Curve is already running; ignored repeated button press.')
                elif curve_bool == 0:

                    # comm.Write('Program:Wave_Control.Run_1', 1)
                    # time.sleep(5)
                    # comm.Write('Program:Wave_Control.Run_1', 0)
                    # time.sleep(5)

                    # Writes a 1 to the boolean switch Run_Curve. The PLC executes the correspinding code
                    comm.Write('Program:Wave_Control.Run_Curve', 1)
                    # Wait 5 seconds
                    if(self.RECORD_ANALYTICS):
                        # this could be expanded to other analytics.
                        self.ANALYTICS_DURATION = 5
                        self.record_positions(comm)
                    else:
                        time.sleep(5)
                    # Turn the Run_Curve switch off.
                    comm.Write('Program:Wave_Control.Run_Curve', 0)
                    self.LOGGER.log(15, 'Successfully ran curve.')
        else:
            time.sleep(5)
        # FIX: Keep state as HOMED (1) after curve completes
        # Motors are still homed, can run another curve without re-homing
        self.state = 1
        self.notify_view()
        #self.curve_lock.release()

    def live_motor_reset(self):
        """Method to write all zeroes to the Live motors array. 
        This method is used to check if the motors are connected 
        on init so it is not protected by a self.CONNECTED check."""
        for x in range(0, 30):
            with PLC() as comm:
                comm.IPAddress = self.IP_ADDRESS
                comm.ProcessorSlot = self.PROCESSOR_SLOT
                comm.Write('Program:Wave_Control.Live_Motors.{}'.format(x), 0)
        self.live_motor_sets = []
        self.live_motors = {}

    def live_motor_reset_mock(self):
        """MOCK to write all zeroes to the Live motors array. 
        This method is used to check if the motors are connected 
        on init so it is not protected by a self.CONNECTED check."""
        self.live_motor_sets = []
        self.live_motors = {}

    def full_application_reset(self):
        """Comprehensive reset to bring application back to initial startup state.
        Resets all state variables, clears motors, and resets UI state."""
        # Turn off motors and clear errors first
        self.motor_off()
        
        # Reset all dictionaries and lists to initial state
        self.motdict = {}
        self.live_motors = {}
        self.live_motors_sets = []
        self.attrcat = {}
        self.csvattrcat = {}
        self.csvlist = []
        
        # Reset state to unprepared state (0) so Prepare Motors button is enabled
        self.state = 0
        self.is_homing = False
        
        # Reset analytics settings
        self.RECORD_ANALYTICS = False
        self.ANALYTICS_INTERVAL = 0.25
        self.ANALYTICS_DURATION = 10.0
        
        # Reset run enable flag
        self.RUN_ENABLE = False
        
        self.LOGGER.info("Application fully reset to initial state")

    def mock_live_motor_reset(self):
        """Method to mock a live motor reset since the actual
        live motor reset tries to connect with motors."""
        self.live_motor_sets = []
        self.live_motors = {}

    def get_rows(self) -> List[int]:
        """Creates list of rows that contain live motors."""
        row_list: List[int] = []
        for motor in self.live_motors.values():
            if motor.row not in row_list:
                row_list.append(motor.row)
        row_list.sort()
        return row_list

    def get_row(self, row: int) -> List[Motor]:
        """Creates list of rows that contain live motors."""
        row_list: List[Motor] = []
        for motor in self.live_motors.values():
            if motor.row == row:
                row_list.append(motor)
        return row_list

    def get_columns(self) -> List[int]:
        """Creates list of columns that contain live motors."""
        column_list: List[int] = []
        for motor in self.live_motors.values():
            if motor.column not in column_list:
                column_list.append(motor.column)
        column_list.sort()
        return column_list

    def get_column(self, column: int) -> List[Motor]:
        """Creates list of rows that contain live motors."""
        column_list: List[Motor] = []
        for motor in self.live_motors.values():
            if motor.column == column:
                column_list.append(motor)
        return column_list

    def get_live_motor_list(self) -> List[int]:
        """Creates sorted list of all live motors by number."""
        motor_list: List[int] = []
        for key in self.live_motors:
            motor_list.append(key)
        motor_list.sort()
        return motor_list
    
    def turnOn_motors(self):
        """Turns on motors AFTER pressing 'prepare motors' on control home"""
        for set in self.live_motor_sets:
            for motnum, motor in set.items():
                if (self.motdict[motnum]==1 or 2):
                    pass



    def attr_write(self):
        """Writes attributes to motors and returns true upon success."""
        for set in self.live_motors_sets:
            for motor in set.values():
                motor.write_to_motor(self.IP_ADDRESS, self.PROCESSOR_SLOT)
        # for motor in self.live_motors.values():
        #     motor.write_to_motor(self.IP_ADDRESS, self.PROCESSOR_SLOT)

        self.LOGGER.log(15, 'Successfully wrote to motors.')
