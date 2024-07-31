#========================================================================================================================
# This file is for the sub-menu for the drive coil.
#========================================================================================================================

from typing import Tuple
from .gui_element import GUIElement
from .. import *
import os
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog

#========================================================================================================================
# Class definition

class Drivecoil(GUIElement):

    #--------------------------------------------------------------------------------------------------------------------
    # Class constructor. The parameters are as follows:
    #
    #     - parent:            A Tkinter widget (e.g. frame) which serves as the parent of this sub-menu.
    #     - pos_num_validator: A Tcl-registered lambda, which should check if the input string can be parsed as a
    #                            nonnegative real number (and return True or False accordingly).
    #     - pos_int_validator: A Tcl-registered lambda, which should check if the input string can be parsed as a
    #                            nonnegative integer (and return True or False accordingly).
    #     - PROGRAM_DIRECTORY: The program main's current working directory.
    #

    def __init__(self, parent, pos_num_validator, pos_int_validator, PROGRAM_DIRECTORY):
        
        self.frame = ttk.LabelFrame(parent, text='Drive Coil Parameters', padding=10)

        self.radius_label = ttk.Label(self.frame, text='Nominal coil radius:')
        self.radius_label.grid(column=0, row=0, sticky=tk.E)
        self.radius_entry_variable = tk.StringVar(value='0.0')
        self.radius_entry = ttk.Entry(self.frame, textvariable=self.radius_entry_variable, validate='focus', validatecommand=(pos_num_validator, '%P'))
        self.radius_entry.grid(column=1, row=0, sticky=tk.W+tk.E)
        self.radius_units_variable = tk.StringVar(value='m')
        self.radius_units = ttk.Combobox(self.frame, textvariable=self.radius_units_variable, values=LENGTH_UNITS, width=5)
        self.radius_units.grid(column=2, row=0, sticky=tk.W+tk.E)
        self.radius_units.state(['!disabled', 'readonly'])

        self.length_label = ttk.Label(self.frame, text='Coil length:')
        self.length_label.grid(column=0, row=1, sticky=tk.E)
        self.length_entry_variable = tk.StringVar(value='0.0')
        self.length_entry = ttk.Entry(self.frame, textvariable=self.length_entry_variable, validate='focus', validatecommand=(pos_num_validator, '%P'))
        self.length_entry.grid(column=1, row=1, sticky=tk.W+tk.E)
        self.length_units_variable = tk.StringVar(value='m')
        self.length_units = ttk.Combobox(self.frame, textvariable=self.length_units_variable, values=LENGTH_UNITS, width=5)
        self.length_units.grid(column=2, row=1, sticky=tk.W+tk.E)
        self.length_units.state(['!disabled', 'readonly'])

        self.nturns_label = ttk.Label(self.frame, text='Number of turns:')
        self.nturns_label.grid(column=0, row=2, sticky=tk.E)
        self.nturns_entry_variable = tk.StringVar(value='0')
        self.nturns_entry = ttk.Entry(self.frame, textvariable=self.nturns_entry_variable, validate='focus', validatecommand=(pos_int_validator, '%P'))
        self.nturns_entry.grid(column=1, row=2, sticky=tk.W+tk.E)

        self.thickness_label = ttk.Label(self.frame, text='Wire thickness:')
        self.thickness_label.grid(column=0, row=3, sticky=tk.E)
        self.thickness_entry_variable = tk.StringVar(value='0.0')
        self.thickness_entry = ttk.Entry(self.frame, textvariable=self.thickness_entry_variable, validate='focus', validatecommand=(pos_num_validator, '%P'))
        self.thickness_entry.grid(column=1, row=3, sticky=tk.W+tk.E)
        self.thickness_units_variable = tk.StringVar(value='mm')
        self.thickness_units = ttk.Combobox(self.frame, textvariable=self.thickness_units_variable, values=LENGTH_UNITS, width=5)
        self.thickness_units.grid(column=2, row=3, sticky=tk.W+tk.E)
        self.thickness_units.state(['!disabled', 'readonly'])

        self.material_label = ttk.Label(self.frame, text='Wire material:')
        self.material_label.grid(column=0, row=4, sticky=tk.E)
        self.material_entry_variable = tk.StringVar(value='')
        self.material_entry = ttk.Entry(self.frame, textvariable=self.material_entry_variable)
        self.material_entry.grid(column=1, row=4, columnspan=2, sticky=tk.W+tk.E)
        self.material_entry.state(['readonly'])
        def material_button_action():
            initdir = os.path.join(PROGRAM_DIRECTORY, 'data', 'materials')
            if not os.path.isdir(initdir):
                initdir = PROGRAM_DIRECTORY
            filename = tkinter.filedialog.askopenfilename(initialdir=initdir, filetypes=(('Config file', '*.cfg'), ('All files', '*.*')))
            if filename is not None:
                self.material_entry_variable.set(filename)
        self.material_button = ttk.Button(self.frame, text='Open...', command=material_button_action)
        self.material_button.grid(column=3, row=4, sticky=tk.W+tk.E)

        self.freq_label = ttk.Label(self.frame, text='Frequency:')
        self.freq_label.grid(column=0, row=5, sticky=tk.E)
        self.freq_entry_variable = tk.StringVar(value='0.0')
        self.freq_entry = ttk.Entry(self.frame, textvariable=self.freq_entry_variable, validate='focus', validatecommand=(pos_num_validator, '%P'))
        self.freq_entry.grid(column=1, row=5, sticky=tk.W+tk.E)
        self.freq_units_variable = tk.StringVar(value='Hz')
        self.freq_units = ttk.Combobox(self.frame, textvariable=self.freq_units_variable, values=FREQ_UNITS, width=5)
        self.freq_units.grid(column=2, row=5, sticky=tk.W+tk.E)
        self.freq_units.state(['!disabled', 'readonly'])

        self.amp_label = ttk.Label(self.frame, text='Current:')
        self.amp_label.grid(column=0, row=6, sticky=tk.E)
        self.amp_entry_variable = tk.StringVar(value='0.0')
        self.amp_entry = ttk.Entry(self.frame, textvariable=self.amp_entry_variable, validate='focus', validatecommand=(pos_num_validator, '%P'))
        self.amp_entry.grid(column=1, row=6, sticky=tk.W+tk.E)
        self.amp_units_variable = tk.StringVar(value='A')
        self.amp_units = ttk.Combobox(self.frame, textvariable=self.amp_units_variable, values=CURRENT_UNITS, width=5)
        self.amp_units.grid(column=2, row=6, sticky=tk.W+tk.E)
        self.amp_units.state(['!disabled', 'readonly'])
        self.amp_type_variable = tk.StringVar(value='pkpk')
        self.amp_type = ttk.Combobox(self.frame, textvariable=self.amp_type_variable, values=('pkpk', 'rms'), width=5)
        self.amp_type.grid(column=3, row=6, sticky=tk.W+tk.E)
        self.amp_type.state(['!disabled', 'readonly'])
        

    #--------------------------------------------------------------------------------------------------------------------
    # Satisfying GUIElement inheritance requirements

    def grid(self, **kwargs) -> None:
        self.frame.grid(**kwargs)
        
    #--------------------

    def get_configuration(self, prev: dict = None) -> dict:
        output = dict()
        output['drivecoil_radius'] = self.radius_entry_variable.get()
        output['drivecoil_radius_units'] = self.radius_units_variable.get()
        output['drivecoil_length'] = self.length_entry_variable.get()
        output['drivecoil_length_units'] = self.length_units_variable.get()
        output['drivecoil_nturns'] = self.nturns_entry_variable.get()
        output['drivecoil_thickness'] = self.thickness_entry_variable.get()
        output['drivecoil_thickness_units'] = self.thickness_units_variable.get()
        output['drivecoil_mat'] = self.material_entry_variable.get()
        
        
        ang_freq = float(self.freq_entry_variable.get())
        if self.freq_units_variable.get() == 'Hz':
            ang_freq *= (2 * np.pi)     # 1 Hz = 2pi rad/s
        elif self.freq_units_variable.get() == 'rpm':
            ang_freq *= (np.pi / 30)    # 1 rpm = pi/30 rad/s
        output['drivecoil_ang_freq'] = str(ang_freq)
    
        current = float(self.amp_entry_variable.get())
        if self.amp_type_variable.get() == 'rms':
            current *= np.sqrt(2)
        output['drivecoil_amp'] = str(current)
        output['drivecoil_amp_units'] = self.amp_units_variable.get()

        if prev is None:
            return output
        else:
            prev.update(output)
            return prev
        
    #--------------------

    def set_configuration(self, config: dict) -> Tuple[int, str]:

        result = 0
        err_str = ''
        
        if 'drivecoil_radius' in config and 'drivecoil_radius_units' in config:
            var = config['drivecoil_radius']
            unit = config['drivecoil_radius_units']
            if is_nonneg_real_number(var) and unit in LENGTH_UNITS:
                self.radius_entry_variable.set(var)
                self.radius_units_variable.set(unit)
            else:
                self.radius_entry_variable.set('0.0')
                self.radius_units_variable.set('m')
                result = 1
                err_str += 'Drivecoil radius invalid\n'
        else:
            self.radius_entry_variable.set('0.0')
            self.radius_units_variable.set('m')
            result = 1
            err_str += 'Missing drivecoil radius\n'

        if 'drivecoil_length' in config and 'drivecoil_length_units' in config:
            var = config['drivecoil_length']
            unit = config['drivecoil_length_units']
            if is_nonneg_real_number(var) and unit in LENGTH_UNITS:
                self.length_entry_variable.set(var)
                self.length_units_variable.set(unit)
            else:
                self.length_entry_variable.set('0.0')
                self.length_units_variable.set('m')
                result = 1
                err_str += 'Drivecoil length invalid\n'
        else:
            self.length_entry_variable.set('0.0')
            self.length_units_variable.set('m')
            result = 1
            err_str += 'Missing drivecoil length\n'
            
        if 'drivecoil_nturns' in config:
            var = config['drivecoil_nturns']
            if is_nonneg_int(var):
                self.nturns_entry_variable.set(var)
            else:
                self.nturns_entry_variable.set('0')
                result = 1
                err_str += 'Drivecoil number of turns invalid\n'
        else:
            self.nturns_entry_variable.set('0')
            result = 1
            err_str += 'Missing drivecoil number of turns\n'
            
        if 'drivecoil_thickness' in config and 'drivecoil_thickness_units' in config:
            var = config['drivecoil_thickness']
            unit = config['drivecoil_thickness_units']
            if is_nonneg_real_number(var) and unit in LENGTH_UNITS:
                self.thickness_entry_variable.set(var)
                self.thickness_units_variable.set(unit)
            else:
                self.thickness_entry_variable.set('0.0')
                self.thickness_units_variable.set('mm')
                result = 1
                err_str += 'Drivecoil thickness invalid\n'
        else:
            self.thickness_entry_variable.set('0.0')
            self.thickness_units_variable.set('mm')
            result = 1
            err_str += 'Missing drivecoil thickness\n'
            
        if 'drivecoil_mat' in config:
            var = config['drivecoil_mat']
            if os.path.isfile(var):
                self.material_entry_variable.set(var)
            else:
                self.material_entry_variable.set('')
                result = 1
                err_str += 'Drivecoil material invalid\n'
        else:
            self.material_entry_variable.set('')
            result = 1
            err_str += 'Missing drivecoil material\n'
            
        if 'drivecoil_ang_freq' in config:
            var = config['drivecoil_ang_freq']
            if is_nonneg_real_number(var):
                self.freq_entry_variable.set(str(float(var) / (2 * np.pi)))
                self.freq_units_variable.set('Hz') # Defaults to Hz
            else:
                self.freq_entry_variable.set('0.0')
                self.freq_units_variable.set('Hz')
                result = 1
                err_str += 'Drivecoil frequency invalid\n'
        else:
            self.freq_entry_variable.set('0.0')
            self.freq_units_variable.set('Hz')
            result = 1
            err_str += 'Missing drivecoil frequency\n'
        
        if 'drivecoil_amp' in config and 'drivecoil_amp_units' in config:
            var = config['drivecoil_amp']
            unit = config['drivecoil_amp_units']
            if is_nonneg_real_number(var):
                self.amp_entry_variable.set(var)
                self.amp_units_variable.set(unit)
                self.amp_type_variable.set('pkpk')
            else:
                self.amp_entry_variable.set('0.0')
                self.amp_units_variable.set('A')
                self.amp_type_variable.set('pkpk')
                result = 1
                err_str += 'Drivecoil current invalid\n'
        else:
            self.amp_entry_variable.set('0.0')
            self.amp_units_variable.set('A')
            self.amp_type_variable.set('pkpk')
            result = 1
            err_str += 'Missing drivecoil current\n'

        return (result, err_str)

