#========================================================================================================================
# This file is for the sub-menu for the sample (i.e. the object being measured).
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

class Sample(GUIElement):

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
        
        self.frame = ttk.LabelFrame(parent, text='Test Sample', padding=10)

        self.radius_label = ttk.Label(self.frame, text='Cylinder radius:')
        self.radius_label.grid(column=0, row=0, sticky=tk.E)
        self.radius_entry_variable = tk.StringVar(value='0.0')
        self.radius_entry = ttk.Entry(self.frame, textvariable=self.radius_entry_variable, validate='focus', validatecommand=(pos_num_validator, '%P'))
        self.radius_entry.grid(column=1, row=0, sticky=tk.W+tk.E)
        self.radius_units_variable = tk.StringVar(value='m')
        self.radius_units = ttk.Combobox(self.frame, textvariable=self.radius_units_variable, values=LENGTH_UNITS, width=5)
        self.radius_units.grid(column=2, row=0, sticky=tk.W+tk.E)
        self.radius_units.state(['!disabled', 'readonly'])

        self.length_label = ttk.Label(self.frame, text='Cylinder length:')
        self.length_label.grid(column=0, row=1, sticky=tk.E)
        self.length_entry_variable = tk.StringVar(value='0.0')
        self.length_entry = ttk.Entry(self.frame, textvariable=self.length_entry_variable, validate='focus', validatecommand=(pos_num_validator, '%P'))
        self.length_entry.grid(column=1, row=1, sticky=tk.W+tk.E)
        self.length_units_variable = tk.StringVar(value='m')
        self.length_units = ttk.Combobox(self.frame, textvariable=self.length_units_variable, values=LENGTH_UNITS, width=5)
        self.length_units.grid(column=2, row=1, sticky=tk.W+tk.E)
        self.length_units.state(['!disabled', 'readonly'])

        self.material_label = ttk.Label(self.frame, text='Material:')
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
        output['sample_radius'] = self.radius_entry_variable.get()
        output['sample_radius_units'] = self.radius_units_variable.get()
        output['sample_length'] = self.length_entry_variable.get()
        output['sample_length_units'] = self.length_units_variable.get()
        output['sample_mat'] = self.material_entry_variable.get()
        output['sample_offset'] = self.offset_entry_variable.get()
        output['sample_offset_units'] = self.offset_units_variable.get()

        if prev is None:
            return output
        else:
            prev.update(output)
            return prev
        
    #--------------------

    def set_configuration(self, config: dict) -> Tuple[int, str]:

        result = 0
        err_str = ''
        
        if 'sample_radius' in config and 'sample_radius_units' in config:
            var = config['sample_radius']
            unit = config['sample_radius_units']
            if is_nonneg_real_number(var) and unit in LENGTH_UNITS:
                self.radius_entry_variable.set(var)
                self.radius_units_variable.set(unit)
            else:
                self.radius_entry_variable.set('0.0')
                self.radius_units_variable.set('m')
                result = 1
                err_str += 'Sample radius invalid\n'
        else:
            self.radius_entry_variable.set('0.0')
            self.radius_units_variable.set('m')
            result = 1
            err_str += 'Missing sample radius\n'

        if 'sample_length' in config and 'sample_length_units' in config:
            var = config['sample_length']
            unit = config['sample_length_units']
            if is_nonneg_real_number(var) and unit in LENGTH_UNITS:
                self.length_entry_variable.set(var)
                self.length_units_variable.set(unit)
            else:
                self.length_entry_variable.set('0.0')
                self.length_units_variable.set('m')
                result = 1
                err_str += 'Sample length invalid\n'
        else:
            self.length_entry_variable.set('0.0')
            self.length_units_variable.set('m')
            result = 1
            err_str += 'Missing sample length\n'
            
        if 'sample_mat' in config:
            var = config['sample_mat']
            if os.path.isfile(var):
                self.material_entry_variable.set(var)
            else:
                self.material_entry_variable.set('')
                result = 1
                err_str += 'Sample material invalid\n'
        else:
            self.material_entry_variable.set('')
            result = 1
            err_str += 'Missing sample material\n'
        
        if 'sample_offset' in config and 'sample_offset_units' in config:
            var = config['sample_offset']
            unit = config['sample_offset_units']
            if is_real_number(var) and unit in LENGTH_UNITS:
                self.offset_entry_variable.set(var)
                self.offset_units_variable.set(unit)
            else:
                self.offset_entry_variable.set('0.0')
                self.offset_units_variable.set('m')
                result = 1
                err_str += 'Sample offset invalid\n'
        else:
            self.offset_entry_variable.set('0.0')
            self.offset_units_variable.set('m')
            result = 1
            err_str += 'Missing sample offset\n'

        return (result, err_str)

