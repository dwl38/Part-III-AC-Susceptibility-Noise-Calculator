#========================================================================================================================
# This file is for the sub-menu for the sample coil.
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

class Samplecoil(GUIElement):

    #--------------------------------------------------------------------------------------------------------------------
    # Class constructor. The parameters are as follows:
    #
    #     - parent:            A Tkinter widget (e.g. frame) which serves as the parent of this sub-menu.
    #     - num_validator:     A Tcl-registered lambda, which should check if the input string can be parsed as a
    #                            real number of either sign (and return True or False accordingly).
    #     - pos_num_validator: A Tcl-registered lambda, which should check if the input string can be parsed as a
    #                            nonnegative real number (and return True or False accordingly).
    #     - pos_int_validator: A Tcl-registered lambda, which should check if the input string can be parsed as a
    #                            nonnegative integer (and return True or False accordingly).
    #     - PROGRAM_DIRECTORY: The program main's current working directory.
    #

    def __init__(self, parent, num_validator, pos_num_validator, pos_int_validator, PROGRAM_DIRECTORY):
        
        self.frame = ttk.LabelFrame(parent, text='Sample Coil Parameters', padding=10)

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
                try:
                    if os.path.commonpath([PROGRAM_DIRECTORY,]) == os.path.commonpath([PROGRAM_DIRECTORY, filename]):
                        filename = os.path.relpath(filename, PROGRAM_DIRECTORY)
                except:
                    pass
                self.material_entry_variable.set(filename)
        self.material_button = ttk.Button(self.frame, text='Open...', command=material_button_action)
        self.material_button.grid(column=3, row=4, sticky=tk.W+tk.E)

        self.offset_label = ttk.Label(self.frame, text='Offset along axis:')
        self.offset_label.grid(column=0, row=5, sticky=tk.E)
        self.offset_entry_variable = tk.StringVar(value='0.0')
        self.offset_entry = ttk.Entry(self.frame, textvariable=self.offset_entry_variable, validate='focus', validatecommand=(num_validator, '%P'))
        self.offset_entry.grid(column=1, row=5, sticky=tk.W+tk.E)
        self.offset_units_variable = tk.StringVar(value='m')
        self.offset_units = ttk.Combobox(self.frame, textvariable=self.length_units_variable, values=LENGTH_UNITS, width=5)
        self.offset_units.grid(column=2, row=5, sticky=tk.W+tk.E)
        self.offset_units.state(['!disabled', 'readonly'])
        

    #--------------------------------------------------------------------------------------------------------------------
    # Satisfying GUIElement inheritance requirements

    def grid(self, **kwargs) -> None:
        self.frame.grid(**kwargs)
        
    #--------------------

    def get_configuration(self, prev: dict = None) -> dict:
        output = dict()
        output['samplecoil_radius'] = self.radius_entry_variable.get()
        output['samplecoil_radius_units'] = self.radius_units_variable.get()
        output['samplecoil_length'] = self.length_entry_variable.get()
        output['samplecoil_length_units'] = self.length_units_variable.get()
        output['samplecoil_nturns'] = self.nturns_entry_variable.get()
        output['samplecoil_thickness'] = self.thickness_entry_variable.get()
        output['samplecoil_thickness_units'] = self.thickness_units_variable.get()
        output['samplecoil_mat'] = self.material_entry_variable.get()
        output['samplecoil_offset'] = self.offset_entry_variable.get()
        output['samplecoil_offset_units'] = self.offset_units_variable.get()

        if prev is None:
            return output
        else:
            prev.update(output)
            return prev
        
    #--------------------

    def set_configuration(self, config: dict) -> Tuple[int, str]:

        result = 0
        err_str = ''
        
        if 'samplecoil_radius' in config and 'samplecoil_radius_units' in config:
            var = config['samplecoil_radius']
            unit = config['samplecoil_radius_units']
            if is_nonneg_real_number(var) and unit in LENGTH_UNITS:
                self.radius_entry_variable.set(var)
                self.radius_units_variable.set(unit)
            else:
                self.radius_entry_variable.set('0.0')
                self.radius_units_variable.set('m')
                result = 1
                err_str += 'Samplecoil radius invalid\n'
        else:
            self.radius_entry_variable.set('0.0')
            self.radius_units_variable.set('m')
            result = 1
            err_str += 'Missing samplecoil radius\n'

        if 'samplecoil_length' in config and 'samplecoil_length_units' in config:
            var = config['samplecoil_length']
            unit = config['samplecoil_length_units']
            if is_nonneg_real_number(var) and unit in LENGTH_UNITS:
                self.length_entry_variable.set(var)
                self.length_units_variable.set(unit)
            else:
                self.length_entry_variable.set('0.0')
                self.length_units_variable.set('m')
                result = 1
                err_str += 'Samplecoil length invalid\n'
        else:
            self.length_entry_variable.set('0.0')
            self.length_units_variable.set('m')
            result = 1
            err_str += 'Missing samplecoil length\n'
            
        if 'samplecoil_nturns' in config:
            var = config['samplecoil_nturns']
            if is_nonneg_int(var):
                self.nturns_entry_variable.set(var)
            else:
                self.nturns_entry_variable.set('0')
                result = 1
                err_str += 'Samplecoil number of turns invalid\n'
        else:
            self.nturns_entry_variable.set('0')
            result = 1
            err_str += 'Missing samplecoil number of turns\n'
            
        if 'samplecoil_thickness' in config and 'samplecoil_thickness_units' in config:
            var = config['samplecoil_thickness']
            unit = config['samplecoil_thickness_units']
            if is_nonneg_real_number(var) and unit in LENGTH_UNITS:
                self.thickness_entry_variable.set(var)
                self.thickness_units_variable.set(unit)
            else:
                self.thickness_entry_variable.set('0.0')
                self.thickness_units_variable.set('mm')
                result = 1
                err_str += 'Samplecoil thickness invalid\n'
        else:
            self.thickness_entry_variable.set('0.0')
            self.thickness_units_variable.set('mm')
            result = 1
            err_str += 'Missing samplecoil thickness\n'
            
        if 'samplecoil_mat' in config:
            var = config['samplecoil_mat']
            if os.path.isfile(var):
                self.material_entry_variable.set(var)
            else:
                self.material_entry_variable.set('')
                result = 1
                err_str += 'Samplecoil material invalid\n'
        else:
            self.material_entry_variable.set('')
            result = 1
            err_str += 'Missing samplecoil material\n'
        
        if 'samplecoil_offset' in config and 'samplecoil_offset_units' in config:
            var = config['samplecoil_offset']
            unit = config['samplecoil_offset_units']
            if is_real_number(var) and unit in LENGTH_UNITS:
                self.offset_entry_variable.set(var)
                self.offset_units_variable.set(unit)
            else:
                self.offset_entry_variable.set('0.0')
                self.offset_units_variable.set('m')
                result = 1
                err_str += 'Samplecoil offset invalid\n'
        else:
            self.offset_entry_variable.set('0.0')
            self.offset_units_variable.set('m')
            result = 1
            err_str += 'Missing samplecoil offset\n'

        return (result, err_str)

