from modules.eip import PLC
from typing import Any, Dict, List
from logging import getLogger, Logger
from modules.logging.log_utils import LOGGER_NAME
import time


class Motor():
    """Given a Motor_ID number (0-29) that corresponds to the motor being defined
    we use this class to access and control information concerning that specific motor.

    For the drive state, warn word, and status word the meanings of each bit can be found
    in the 0185-1093-E_6V7_MA_MotionCtrlSW-SG5-SG7.pdf"""
    LOGGER: Logger = getLogger(LOGGER_NAME)
    # whether the GUI is connected to the motors
    CONNECTED: bool

    # Were the motors correctly written to
    write_success: bool
    # Is the drive homed?
    home: bool
    # is there an error? (Should be detected using the warn word)
    error: bool
    # Operation enabled
    op_enable: bool
    # Drive turned on
    switch_on: bool

    # Row identifier for motor in wavemaker
    row: int
    # Column identifier for motor in wavemaker
    column: int

    # motion parameters that will be written to the motor
    write_params: Dict[str, int]
    # motion parameters that have most recently been written to the motor
    current_params: Dict[str, int]

    # Drive State
    statevar: str
    # Drive error word
    warn_word: str
    # Status Word
    status_word: str
    # Control Word
    control_word: str

    def __init__(self, motor_ID: int, CONNECTED: bool):
        # Checking the motor_ID
        if type(motor_ID) != int:
            raise Exception(
                'The motor_ID should be an integer indicating which drive you wish to work with')
        elif motor_ID < 0 or motor_ID > 29:
            raise Exception(
                'The motor_ID must be an integer between  and 29 inclusive')
        else:
            self.motor_ID = motor_ID + 1
            self.axis_ID = motor_ID

        self.CONNECTED = CONNECTED

        self.home = False
        self.error = False
        self.op_enable = False
        self.switch_on = False
        self.write_success = False

        self.statevar = ''
        self.warn_word = ''
        self.status_word = ''

        self.row = 0
        self.column = 0

        self.write_params = {'Position 1': 0, 'Position 2': 350, 'Speed 1': 500, 'Speed 2': 500, 'Accel 1': 10000, 'Accel 2': 10000,
                             'Decel 1': 10000, 'Decel 2': 10000, 'Jerk 1': 2000, 'Jerk 2': 2000,
                             'Time 1': 0, 'Time 2': 0, 'Profile': 1, 'Move Type': 0, 'Curve ID': 0, 'Time Scale': 0,
                             'Amplitude Scale': 0, 'Curve Offset': 0}
        self.current_params = {}

        # Call motor_sort to get the motors row and column position
        self.motor_sort()

    def valid_write_dict(self) -> bool:
        all_params: List[str] = ['Position 1', 'Position 2', 'Speed 1', 'Speed 2', 'Accel 1', 'Accel 2',
                                 'Decel 1', 'Decel 2', 'Jerk 1', 'Jerk 2',
                                 'Time 1', 'Time 2', 'Profile', 'Move Type', 'Curve ID', 'Time Scale',
                                 'Amplitude Scale', 'Curve Offset']
        for param in all_params:
            if param not in self.write_params:
                return False
        return True

    def generate_writter_param_str(self) -> str:
        if self.current_params == {}:
            final: str = "Unwritten Parameters:"
            for key in self.write_params.keys():
                final += f"\n{key}: {self.write_params[key]}"
            return final
        final: str = ""
        for key in self.current_params.keys():
            if self.current_params[key] != self.write_params[key]:
                final += f"{key}: {self.current_params[key]} -> {self.write_params[key]} \n"
            else:
                final += f"{key}: {self.current_params[key]} \n"
        return final

    def motor_sort(self):
        if self.axis_ID % 3 == 0:
            self.row = 1
            self.column = 1 + int(self.axis_ID/3)
        elif self.axis_ID % 3 == 1:
            self.row = 2
            self.column = 1 + int(self.axis_ID/3)
        elif self.axis_ID % 3 == 2:
            self.row = 3
            self.column = 1 + int(self.axis_ID/3)

    def DriveState(self, ip: str, slot: int):
        """Drive State from MotionCtrlSW-SG5-SG7."""
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = ip
                comm.ProcessorSlot = slot
                statevar_name = 'Program:Wave_Control.Axis[{0}].StateVar'.format(
                    self.axis_ID)
                state: Any = comm.Read(statevar_name)
                self.statevar = bin(state)
        else:
            self.statevar = 'Motors not currently connected.'
        return self.statevar

    def WarnWord(self, ip: str, slot: int):
        """Drive warn word from MotionCtrlSW-SG5-SG7."""
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = ip
                comm.ProcessorSlot = slot
                warnword_name = 'Program:Wave_Control.Axis[{0}].WarnWord'.format(
                    self.axis_ID)
                warn: Any = comm.Read(warnword_name)
                self.warn_word = bin(warn)
        else:
            self.warn_word = 'Motors not currently connected.'
        return self.warn_word

    def StatusWord(self, ip: str, slot: int):
        """Status word from MotionCtrlSW-SG5-SG7."""
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = ip
                comm.ProcessorSlot = slot
                statusword_name = 'Program:Wave_Control.Axis[{0}].StatusWord'.format(
                    self.axis_ID)
                status: Any = comm.Read(statusword_name)
                self.status_word = bin(status)
        else:
            self.status_word = 'Motors not currently connected.'
        return self.status_word

    def ControlWord(self, ip: str, slot: int):
        """Control word from MotionCtrlSW-SG5-SG7."""
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = ip
                comm.ProcessorSlot = slot
                controlword_name = 'Program:Wave_Control.Axis[{0}].ControlWord'.format(
                    self.axis_ID)
                control: Any = comm.Read(controlword_name)
                self.control_word = bin(control)
        else:
            self.control_word = 'Motors not currently connected.'
        return self.control_word

    def homed(self, ip: str, slot: int):
        """Is the drive homed? Checking the 12th bit of the Status Word for if the motor is homed or not"""
        if self.CONNECTED:
            self.StatusWord(ip, slot)
            self.ControlWord(ip, slot)
            homing_bit_pos = len(self.control_word)-12
            # This give the position of the home bit counting from the right of the string
            # Because the bin function deletes leading zeroes there could be an issue here if there is not a 1 to the left of the
            # Home bit position. The 12 comes from the length of the status word and counting from the right
            # The 14 is from the 0b identifier from the bin() method
            if len(self.status_word) >= 14:
                home_pos = len(self.status_word)-12
                if int(self.status_word[home_pos]) == 1:
                    self.home = True
                else:
                    self.home = False
            elif len(self.status_word) < 14 and int(self.control_word[homing_bit_pos]) != 1:
                raise Exception(
                    'Status Word less than 12 bits in length, check Status Word and documentation')
        else:
            self.home = True
        return(self.home)

    def write_to_motor(self, ip: str, slot: int):
        """Calls all write functions on motor."""
        # attempt to write to all motors
        if self.CONNECTED:
            self.write_movetype(ip, slot)
            self.write_profile(ip, slot)
            self.write_position(ip, slot)
            self.write_speed(ip, slot)
            self.write_accel(ip, slot)
            self.write_decel(ip, slot)
            self.write_jerk(ip, slot)
            self.write_time(ip, slot)
            self.write_curve(ip, slot)
        else:
            time.sleep(.5)
            self.current_params = self.write_params.copy()
        # compare current and write dictionaries to determine if write was successful
        if (self.current_params != self.write_params):
            self.write_success = False
            self.LOGGER.error('Not all values were written to motors.')
        else:
            self.write_success = True

    def write_generic(self, ip: str, slot: int, param: str, param_name: str):
        """Generic method for writing to a motor param."""
        with PLC() as comm:
            comm.IPAddress = ip
            comm.ProcessorSlot = slot

            comm.Write(
                f'Program:Wave_Control.Motor_{self.motor_ID}.{param}', self.write_params[param_name])
            self.current_params[param_name] = self.write_params[param_name]

    def write_generic_curve(self, ip: str, slot: int, param: str, param_name: str):
        """Generic method for writing to a motor param."""
        with PLC() as comm:
            comm.IPAddress = ip
            comm.ProcessorSlot = slot

            comm.Write(
                f'Program:Wave_Control.Curve_{self.motor_ID}.{param}', self.write_params[param_name])
            self.current_params[param_name] = self.write_params[param_name]

    def write_movetype(self, ip: str, slot: int):
        """Method for writingthe movetype of motor.
        Movetype should be Absolute(0) or Incremental(1)."""
        if self.write_params['Move Type'] == 0 or self.write_params['Move Type'] == 1:
            self.write_generic(ip, slot, 'MoveType', 'Move Type')
        else:
            raise Exception(
                'The MoveType argument must be a 1 or a 0. 0 for absolute 1 for Incremental')

    def write_profile(self, ip: str, slot: int):
        """Method for writing movement profile the motor should use.
        Profile: Trapazoidal(0) Bestehorn(1) S-Curve(2) Sin(3)"""
        if self.write_params['Profile'] >= 0 and self.write_params['Profile'] <= 3:
            self.write_generic(ip, slot, 'Profile', 'Profile')
        else:
            raise Exception(
                'The argument for Profile must be an integer 0,1,2,3. Trapazoidal(0) Bestehorn(1) S-Curve(2) Sin(3)')

    def write_position(self, ip: str, slot: int):
        """Method for writing Position values.
        368 is the limit on the down stroke and -20 is the limit for the upstroke."""
        if self.write_params['Position 1'] > 368 or self.write_params['Position 1'] < -20:
            raise Exception('Position 1 out of stroke range')
        elif self.write_params['Position 2'] > 368 or self.write_params['Position 2'] < -20:
            raise Exception('Position 2 out of stroke range')
        else:
            self.write_generic(ip, slot, 'Pos_1', 'Position 1')
            self.write_generic(ip, slot, 'Pos_2', 'Position 2')

    def write_speed(self, ip: str, slot: int):
        """Method for writing speed values."""
        if self.write_params['Speed 1'] > 900 or self.write_params['Speed 1'] < 0:
            raise Exception(
                'Speed 1 is outside the bounds of the speed limits')
        elif self.write_params['Speed 2'] > 900 or self.write_params['Speed 2'] < 0:
            raise Exception(
                'Speed 2 is outside the bounds of the speed limits')
        else:
            self.write_generic(ip, slot, 'Spd_1', 'Speed 1')
            self.write_generic(ip, slot, 'Spd_2', 'Speed 2')

    def write_accel(self, ip: str, slot: int):
        """Method for writing accelarration values."""
        if self.write_params['Accel 1'] > 20000 or self.write_params['Accel 1'] < 0:
            raise Exception(
                'Accel 1 is outside the bounds of the acceleration limit')
        elif self.write_params['Accel 2'] > 20000 or self.write_params['Accel 2'] < 0:
            raise Exception(
                'Accel 2 is outside the bounds of the acceleration limit')
        else:
            self.write_generic(ip, slot, 'Accel_1', 'Accel 1')
            self.write_generic(ip, slot, 'Accel_2', 'Accel 2')

    def write_decel(self, ip: str, slot: int):
        """Method for writing decelarration values."""
        if (self.write_params['Decel 1'] > 20000 or self.write_params['Decel 1'] < 0):
            raise Exception(
                'Decel 1 is outside the bounds of the deceleration limit')
        elif (self.write_params['Decel 2'] > 20000 or self.write_params['Decel 2'] < 0):
            raise Exception(
                'Decel 2 is outside the bounds of the deceleration limit')
        else:
            self.write_generic(ip, slot, 'Decel_1', 'Decel 1')
            self.write_generic(ip, slot, 'Decel_2', 'Decel 2')

    def write_jerk(self, ip: str, slot: int):
        """Method for writing Jerk values."""
        self.write_generic(ip, slot, 'Jerk_1', 'Jerk 1')
        self.write_generic(ip, slot, 'Jerk_2', 'Jerk 2')

    def write_time(self, ip: str, slot: int):
        """Method for writing Time values."""
        self.write_generic(ip, slot, 'Time1', 'Time 1')
        self.write_generic(ip, slot, 'Time2', 'Time 2')

    def write_curve(self, ip: str, slot: int):
        """Method for writing curve values."""
        self.write_generic_curve(ip, slot, 'Curve_ID', 'Curve ID')
        self.write_generic_curve(ip, slot, 'TimeScale', 'Time Scale')
        self.write_generic_curve(ip, slot, 'AmplitudeScale', 'Amplitude Scale')
        self.write_generic_curve(ip, slot, 'CurveOffset', 'Curve Offset')

    def read_movetype(self, ip: str, slot: int):
        """Method for reading the movetype of motor. 
        Movetype should be Absolute(0) or Incremental(1)."""
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = ip
                comm.ProcessorSlot = slot

                move_type: Any = comm.Read(
                    'Program:Wave_Control.motor_{0}.MoveType'.format(self.motor_ID))
                assert(type(move_type) == int)
                self.current_params['Move Type'] = move_type

    def read_profile(self, ip: str, slot: int):
        """Method for reading movement profile the motor should use.
        Profile: Trapazoidal(0) Bestehorn(1) S-Curve(2) Sin(3)"""
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = ip
                comm.ProcessorSlot = slot

                profile: Any = comm.Read(
                    'Program:Wave_Control.Motor_{0}.Profile'.format(self.motor_ID))
                assert(type(profile) == int)
                self.current_params['Profile'] = profile

    def read_position(self, ip: str, slot: int):
        """Method for reading Position values."""
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = ip
                comm.ProcessorSlot = slot

                pos1: Any = comm.Read(
                    'Program:Wave_Control.Motor_{0}.Pos_{1}'.format(self.motor_ID, 1))
                pos2: Any = comm.Read(
                    'Program:Wave_Control.Motor_{0}.Pos_{1}'.format(self.motor_ID, 2))
                assert (type(pos1) == int and type(pos2) == int)
                self.current_params['Position 1'] = pos1
                self.current_params['Position 2'] = pos2

    def read_speed(self, ip: str, slot: int):
        """Method for reading speed values."""
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = ip
                comm.ProcessorSlot = slot

                self.Speed_1 = comm.Read(
                    'Program:Wave_Control.Motor_{0}.Spd_{1}'.format(self.motor_ID, 1))
                self.Speed_2 = comm.Read(
                    'Program:Wave_Control.Motor_{0}.Spd_{1}'.format(self.motor_ID, 2))

    def read_accel(self, ip: str, slot: int):
        """Method for reading accelarration values."""
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = ip
                comm.ProcessorSlot = slot

                self.Accel_1 = comm.Read(
                    'Program:Wave_Control.Motor_{0}.Accel_{1}'.format(self.motor_ID, 1))
                self.Accel_2 = comm.Read(
                    'Program:Wave_Control.Motor_{0}.Accel_{1}'.format(self.motor_ID, 2))

    def read_decel(self, ip: str, slot: int):
        """Method for reading decelarration values."""
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = ip
                comm.ProcessorSlot = slot
                self.Decel_1 = comm.Read(
                    'Program:Wave_Control.Motor_{0}.Decel_{1}'.format(self.motor_ID, 1))
                self.Decel_2 = comm.Read(
                    'Program:Wave_Control.Motor_{0}.Decel_{1}'.format(self.motor_ID, 2))

    def read_jerk(self, ip: str, slot: int):
        """Method for reading Jerk values."""
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = ip
                comm.ProcessorSlot = slot

                self.Jerk_1 = comm.Read(
                    'Program:Wave_Control.Motor_{0}.Jerk_{1}'.format(self.motor_ID, 1))
                self.Jerk_2 = comm.Read(
                    'Program:Wave_Control.Motor_{0}.Jerk_{1}'.format(self.motor_ID, 2))

    def read_time(self, ip: str, slot: int):
        """Method for reading Time values."""
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = ip
                comm.ProcessorSlot = slot

                self.Time_1 = comm.Read(
                    'Program:Wave_Control.Motor_{0}.Time{1}'.format(self.motor_ID, 1))
                self.Time_2 = comm.Read(
                    'Program:Wave_Control.Motor_{0}.Time{1}'.format(self.motor_ID, 2))

    def read_curve(self, ip: str, slot: int):
        """Method for reading curve values."""
        if self.CONNECTED:
            with PLC() as comm:
                comm.IPAddress = ip
                comm.ProcessorSlot = slot

                self.Curve_ID = comm.Read(
                    'Program:Wave_Control.Curve_{0}.Curve_ID'.format(self.motor_ID))
                self.TimeScale = comm.Read(
                    'Program:Wave_Control.Curve_{0}.TimeScale'.format(self.motor_ID))
                self.AmplitudeScale = comm.Read(
                    'Program:Wave_Control.Curve_{0}.AmplitudeScale'.format(self.motor_ID))
                self.CurveOffset = comm.Read(
                    'Program:Wave_Control.Curve_{0}.CurveOffset'.format(self.motor_ID))
