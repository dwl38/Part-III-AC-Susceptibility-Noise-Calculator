#========================================================================================================================
# This file is for the sub-menu which allows the user to start the calculation, as well as input the domain resolution
# parameters.
#========================================================================================================================

from typing import Tuple
from collections.abc import Iterable
from .gui_element import GUIElement
from .. import *
from ..material import Material
from ..field import SimpleCoil
import os
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox

#========================================================================================================================
# Class definition

class CalculationSubmenu(GUIElement):

    #--------------------------------------------------------------------------------------------------------------------
    # Class constructor. The parameters are as follows:
    #
    #     - parent:            A Tkinter widget (e.g. frame) which serves as the parent of this sub-menu.
    #     - pos_int_validator: A Tcl-registered lambda, which should check if the input string can be parsed as a
    #                            nonnegative integer (and return True or False accordingly).
    #
    # Note that the CalculationSubmenu will not work until "activated" using the activate() method!
    #

    def __init__(self, parent, pos_int_validator):
        
        self.frame = ttk.LabelFrame(parent, text='Calculation Settings', padding=10)

        self.radius_label = ttk.Label(self.frame, text='Radial resolution (no. of points):')
        self.radius_label.grid(column=0, row=0, sticky=tk.E)
        self.radius_entry_variable = tk.StringVar(value='50')
        self.radius_entry = ttk.Entry(self.frame, textvariable=self.radius_entry_variable, validate='focus', validatecommand=(pos_int_validator, '%P'))
        self.radius_entry.grid(column=1, row=0, sticky=tk.W+tk.E)

        self.length_label = ttk.Label(self.frame, text='Axial resolution (no. of points):')
        self.length_label.grid(column=0, row=1, sticky=tk.E)
        self.length_entry_variable = tk.StringVar(value='50')
        self.length_entry = ttk.Entry(self.frame, textvariable=self.length_entry_variable, validate='focus', validatecommand=(pos_int_validator, '%P'))
        self.length_entry.grid(column=1, row=1, sticky=tk.W+tk.E)

        self.time_label = ttk.Label(self.frame, text='Temporal resolution (no. of points):')
        self.time_label.grid(column=0, row=2, sticky=tk.E)
        self.time_entry_variable = tk.StringVar(value='50')
        self.time_entry = ttk.Entry(self.frame, textvariable=self.time_entry_variable, validate='focus', validatecommand=(pos_int_validator, '%P'))
        self.time_entry.grid(column=1, row=2, sticky=tk.W+tk.E)

        self.button = ttk.Button(self.frame, text='Calculate!')
        self.button.grid(column=0, row=3, columnspan=2, padx=5, pady=5)
        

    #--------------------------------------------------------------------------------------------------------------------
    # The activate() method assigns the calculation routine to the GUI's button, allowing the user to interact with it.
    # The parameters are as follows:
    #
    #     - get_current_parameters: A function, of call signature (None)->(dict), which returns the current configuration
    #                                 of the simulation parameters.
    #     - calculate_voltage:      The function which calculates the simulation itself. Call signature is expected to be
    #                                 (CircuitElement, CircuitElement, CircuitElement, Material, float, float, float,
    #                                 float, complex, int, int, int, IntVar)->(complex).
    #     - pre_calls:              A list of functions, all of call signatures (None)->(None), to be run before starting
    #                                 the simulation.
    #

    def activate(self, get_current_parameters, calculate_voltage, pre_calls = None) -> None:

        # Build the big function
        def run_calculation():
    
            # Run pre-call functions
            if pre_calls is not None and isinstance(pre_calls, Iterable):
                for func in pre_calls:
                    func()

            # Load values from the GUI
            config = get_current_parameters()

            sample_r = Q_(float(config['sample_radius']), config['sample_radius_units']).to('m').magnitude
            sample_l = Q_(float(config['sample_length']), config['sample_length_units']).to('m').magnitude
            sample_z = Q_(float(config['sample_offset']), config['sample_offset_units']).to('m').magnitude
            sample_mat = config['sample_mat']
    
            samplecoil_r = Q_(float(config['samplecoil_radius']), config['samplecoil_radius_units']).to('m').magnitude
            samplecoil_l = Q_(float(config['samplecoil_length']), config['samplecoil_length_units']).to('m').magnitude
            samplecoil_z = Q_(float(config['samplecoil_offset']), config['samplecoil_offset_units']).to('m').magnitude
            samplecoil_t = Q_(float(config['samplecoil_thickness']), config['samplecoil_thickness_units']).to('m').magnitude
            samplecoil_N = int(config['samplecoil_nturns'])
            samplecoil_mat = config['samplecoil_mat']
    
            refcoil_r = Q_(float(config['refcoil_radius']), config['refcoil_radius_units']).to('m').magnitude
            refcoil_l = Q_(float(config['refcoil_length']), config['refcoil_length_units']).to('m').magnitude
            refcoil_z = Q_(float(config['refcoil_offset']), config['refcoil_offset_units']).to('m').magnitude
            refcoil_t = Q_(float(config['refcoil_thickness']), config['refcoil_thickness_units']).to('m').magnitude
            refcoil_N = int(config['refcoil_nturns'])
            refcoil_mat = config['refcoil_mat']
    
            drivecoil_r = Q_(float(config['drivecoil_radius']), config['drivecoil_radius_units']).to('m').magnitude
            drivecoil_l = Q_(float(config['drivecoil_length']), config['drivecoil_length_units']).to('m').magnitude
            drivecoil_t = Q_(float(config['drivecoil_thickness']), config['drivecoil_thickness_units']).to('m').magnitude
            drivecoil_N = int(config['drivecoil_nturns'])
            drivecoil_mat = config['drivecoil_mat']

            ang_freq = float(config['drivecoil_ang_freq'])
            current = Q_(float(config['drivecoil_amp']), config['drivecoil_amp_units']).to('A').magnitude

            npoints_r = int(config['npoints_r'])
            npoints_z = int(config['npoints_z'])
            npoints_t = int(config['npoints_t'])

            # Basic verification; aborts early ('return None') and reports error to user if any values are invalid

            error_message = ''
            if sample_r <= 0.0:
                error_message = 'Sample radius cannot be zero!'
            if sample_l <= 0.0:
                error_message = 'Sample length cannot be zero!'
            if sample_mat == '' or not os.path.isfile(sample_mat):
                error_message = 'Please specify sample material!'
            if samplecoil_r <= 0.0:
                error_message = 'Sample coil radius cannot be zero!'
            if samplecoil_l <= 0.0:
                error_message = 'Sample coil length cannot be zero!'
            if samplecoil_t <= 0.0:
                error_message = 'Sample coil wire thickness cannot be zero!'
            if samplecoil_N <= 0:
                error_message = 'Sample coil must have at least one turn!'
            if samplecoil_mat == '' or not os.path.isfile(samplecoil_mat):
                error_message = 'Please specify sample coil wire material!'
            if refcoil_r <= 0.0:
                error_message = 'Reference coil radius cannot be zero!'
            if refcoil_l <= 0.0:
                error_message = 'Reference coil length cannot be zero!'
            if refcoil_t <= 0.0:
                error_message = 'Reference coil wire thickness cannot be zero!'
            if refcoil_N <= 0:
                error_message = 'Reference coil must have at least one turn!'
            if refcoil_mat == '' or not os.path.isfile(refcoil_mat):
                error_message = 'Please specify reference coil wire material!'
            if drivecoil_r <= 0.0:
                error_message = 'Drive coil radius cannot be zero!'
            if drivecoil_l <= 0.0:
                error_message = 'Drive coil length cannot be zero!'
            if drivecoil_t <= 0.0:
                error_message = 'Drive coil wire thickness cannot be zero!'
            if drivecoil_N <= 0:
                error_message = 'Drive coil must have at least one turn!'
            if drivecoil_mat == '' or not os.path.isfile(drivecoil_mat):
                error_message = 'Please specify drive coil wire material!'
            if npoints_r <= 0:
                error_message = 'No. of radial points cannot be zero!'
            if npoints_z <= 0:
                error_message = 'No. of axial points cannot be zero!'

            if error_message != '':
                print(error_message + '\n')
                tkinter.messagebox.showerror(title='Error', message=error_message)
                return None

            # Convert material filepaths into actual Material objects (and report error if any of these fail)

            try:
                sample_mat = Material.read_from_file(sample_mat)
                samplecoil_mat = Material.read_from_file(samplecoil_mat)
                refcoil_mat = Material.read_from_file(refcoil_mat)
                drivecoil_mat = Material.read_from_file(drivecoil_mat)
            except Exception as e:
                tkinter.messagebox.showerror(title='Error', message='Error occured:\n\n'+str(e)+'\n\nCheck if material file is valid!')
                return None
    
            # Construct Coil objects out of the supplied parameters (and report error if any of these fail)

            try:
                drivecoil = SimpleCoil(drivecoil_r, drivecoil_l, drivecoil_N, drivecoil_mat, drivecoil_t)
                refcoil = SimpleCoil(refcoil_r, refcoil_l, refcoil_N, refcoil_mat, refcoil_t, [0, 0, -1], [0, 0, refcoil_z])
                samplecoil = SimpleCoil(samplecoil_r, samplecoil_l, samplecoil_N, samplecoil_mat, samplecoil_t, None, [0, 0, samplecoil_z])
            except Exception as e:
                tkinter.messagebox.showerror(title='Error', message='Error occured:\n\n'+str(e))
                return None

            # Run the calculation

            result = calculate_voltage(drivecoil, samplecoil, refcoil, sample_mat, sample_r, sample_l, sample_z,
                                       ang_freq, current, npoints_r, npoints_z, npoints_t, None)

            print('\n' + str(result))
            tkinter.messagebox.showinfo(title='Result', message='Result obtained: ' + str(result) + ' V')
            

        # Set the action of the button to the newly-created function
        self.button.configure(command=run_calculation)


    #--------------------------------------------------------------------------------------------------------------------
    # Satisfying GUIElement inheritance requirements

    def grid(self, **kwargs) -> None:
        self.frame.grid(**kwargs)
        
    #--------------------

    def get_configuration(self, prev: dict = None) -> dict:
        output = dict()
        output['npoints_r'] = self.radius_entry_variable.get()
        output['npoints_z'] = self.length_entry_variable.get()
        output['npoints_t'] = self.time_entry_variable.get()

        if prev is None:
            return output
        else:
            prev.update(output)
            return prev
        
    #--------------------

    def set_configuration(self, config: dict) -> Tuple[int, str]:

        result = 0
        err_str = ''
        
        if 'npoints_r' in config:
            var = config['npoints_r']
            if is_nonneg_real_number(var):
                self.radius_entry_variable.set(var)
            else:
                self.radius_entry_variable.set('50')
                result = 1
                err_str += 'Radial resolution invalid\n'
        else:
            self.radius_entry_variable.set('50')
            result = 1
            err_str += 'Missing radial resolution\n'
            
        if 'npoints_z' in config:
            var = config['npoints_z']
            if is_nonneg_real_number(var):
                self.length_entry_variable.set(var)
            else:
                self.length_entry_variable.set('50')
                result = 1
                err_str += 'Axial resolution invalid\n'
        else:
            self.length_entry_variable.set('50')
            result = 1
            err_str += 'Missing axial resolution\n'
            
        if 'npoints_t' in config:
            var = config['npoints_t']
            if is_nonneg_real_number(var):
                self.time_entry_variable.set(var)
            else:
                self.time_entry_variable.set('50')
                result = 1
                err_str += 'Temporal resolution invalid\n'
        else:
            self.time_entry_variable.set('50')
            result = 1
            err_str += 'Missing temporal resolution\n'

        return (result, err_str)

