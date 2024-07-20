#========================================================================================================================
# This is the program main; the application is executed from this script.
#------------------------------------------------------------------------------------------------------------------------
# Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna
# aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
# Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint
# occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
#========================================================================================================================

import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
import tkinter
import tkinter.ttk as ttk
import tkinter.filedialog
import tkinter.messagebox

from suscep_calc import *
from suscep_calc.material import Material
from suscep_calc.field import SimpleCoil, VectorField
from suscep_calc.circuit.circuit_element import CircuitElement


#========================================================================================================================
# Check for debug mode via command-line arguments

argparser = argparse.ArgumentParser(description=PROGRAM_DESCRIPTION, add_help=False)
argparser.add_argument('-d', '--debug', action='store_true', help='Run in debug mode')
argparser.add_argument('-h', '--help', action='help', help='Shows this help message and exits')
argparser.add_argument('--version', action='version', help='Shows the version number and exits',
                       version=(PROGRAM_NAME + ' v' + PROGRAM_VERSION))

program_args = argparser.parse_args()
DEBUG_FLAG = program_args.debug

if DEBUG_FLAG:
    print('Program launched in debug mode!\n')
    

#========================================================================================================================
# Create cache for future read-writes

PROGRAM_DIRECTORY = os.getcwd()
#CACHE_DIRECTORY = os.path.join(PROGRAM_DIRECTORY, '._cache')
#if not os.path.isdir(CACHE_DIRECTORY):
#    os.mkdir(CACHE_DIRECTORY)


#========================================================================================================================
# Utility functions

def is_num(x) -> bool:
    try:
        float(x)
        return True
    except:
        return False

def is_pos_num(x) -> bool:
    try:
        return float(x) >= 0.0
    except:
        return False
    
def is_pos_int(x) -> bool:
    try:
        return int(x) >= 0
    except:
        return False
    

#========================================================================================================================
# Big calculation function (runs the full calculation)

def calculate_voltage(drivecoil: CircuitElement, samplecoil: CircuitElement, refcoil: CircuitElement,
                      sample_mat: Material, sample_r: float, sample_l: float, sample_z: float,
                      ang_freq: float, current: complex,
                      npoints_r: int, npoints_z: int, npoints_t: int,
                      progressbar_var: tkinter.IntVar = None) -> complex:
    
    if DEBUG_FLAG:
        print('Function \'calculate_voltage\' launched.')
    if progressbar_var is not None:
        progressbar_var.set(0)

    # Find outer bounds of the system (assuming cylindrical symmetry!)
    system_r = max(drivecoil.radius, samplecoil.radius, refcoil.radius, sample_r)
    system_z1 = min(drivecoil.center[2] - (drivecoil.length / 2), samplecoil.center[2] - (samplecoil.length / 2),
                    refcoil.center[2] - (refcoil.length / 2), sample_z - (sample_l / 2))
    system_z2 = max(drivecoil.center[2] + (drivecoil.length / 2), samplecoil.center[2] + (samplecoil.length / 2),
                    refcoil.center[2] + (refcoil.length / 2), sample_z + (sample_l / 2))
    system_center_z = (system_z2 + system_z1) / 2

    system_r = system_r * 1.02                                           # Pad system size radially by 2%
    system_z1 = system_center_z - ((system_center_z - system_z1) * 1.02) # Pad system size axially by 2%
    system_z2 = system_center_z - ((system_center_z - system_z2) * 1.02) # Pad system size axially by 2%
    
    if DEBUG_FLAG:
        print(f'  - System size is {system_r}m radially, and from {system_z1}m to {system_z2}m axially')

    # Assemble grid of points to calculate fields on
    test_points = np.zeros((npoints_r * npoints_z, 3), dtype=float)
    for i, x in enumerate(np.linspace(0.5 * system_r / npoints_r, system_r, npoints_r)):
        for j, z in enumerate(np.linspace(system_z1, system_z2, npoints_z)):
            test_points[(npoints_z * i) + j] = np.array((x, 0.0, z))

    # Update progress bar
    if progressbar_var is not None:
        progressbar_var.set(10)
    if DEBUG_FLAG:
        print(f'  - Generated {test_points.shape[0]} test points')

    # Calculate H field
    H_field_flattened = drivecoil.calculate_H_field(test_points, ang_freq, current)
    
    # Update progress bar
    if progressbar_var is not None:
        progressbar_var.set(30)
    if DEBUG_FLAG:
        print(f'  - Calculated H field of drive coil')

    # Calculate B field
    B_field_flattened = np.zeros_like(H_field_flattened, dtype=complex)

    if sample_mat.is_magnetically_linear():
        # Case 1: sample is linear. Then B field is simply permeability times H field, inside and outside the sample.
        # We iterate through all calculated points and check if they are inside the sample cylinder; if inside, multiply by
        # the absolute sample permeability, otherwise if outside multiply by the vacuum permeability.
        sample_permeability = VACUUM_PERMEABILITY_SI * (1 + sample_mat.magnetic_susceptibility())
        for i in range(test_points.shape[0]):
            if (test_points[i, 0] < sample_r) and (abs(test_points[i, 2] - sample_z) < (sample_l / 2)):
                B_field_flattened[i] = sample_permeability * H_field_flattened[i]
            else:
                B_field_flattened[i] = VACUUM_PERMEABILITY_SI * H_field_flattened[i]

    else:
        # Case 2: sample is nonlinear. Then calculation needs to switch to the time domain.
        B_field_flattened = np.zeros_like(H_field_flattened, dtype=complex) # TODO
        
    # Update progress bar
    if progressbar_var is not None:
        progressbar_var.set(50)
    if DEBUG_FLAG:
        print(f'  - Calculated B field of system')

    # Convert calculated B field from numpy array to VectorField object; but first, need to 'rotate' calculated field and
    # test points around the axis (assuming cylindrical symmetry) in order to generate a full 3D domain, otherwise the
    # VectorField interpolator will not work
    N_THETA = 20
    rotated_points = np.zeros((N_THETA, npoints_r * npoints_z, 3), dtype=float)
    rotated_B_field = np.zeros((N_THETA, npoints_r * npoints_z, 3), dtype=complex)
    for t, theta in enumerate(np.linspace(0, 2 * np.pi, N_THETA, endpoint=False)):
        rot_mat = np.array(((np.cos(theta), -np.sin(theta), 0), (np.sin(theta), np.cos(theta), 0), (0, 0, 1)))
        rotated_points[t] = np.einsum('kj,ij->ik', rot_mat, test_points)
        rotated_B_field[t] = np.einsum('kj,ij->ik', rot_mat, B_field_flattened)
    rotated_points = rotated_points.reshape(-1, rotated_points.shape[-1])
    rotated_B_field = rotated_B_field.reshape(-1, rotated_B_field.shape[-1])
    B_field = VectorField(rotated_points, rotated_B_field)
    
    # Update progress bar
    if progressbar_var is not None:
        progressbar_var.set(60)
    if DEBUG_FLAG:
        print(f'  - Extrapolated B field around cylindrical symmetry')

    # Calculate the induced voltages in the reference and sample coils
    samplecoil_voltage = samplecoil.calculate_induced_voltage(B_field, ang_freq)
    refcoil_voltage = refcoil.calculate_induced_voltage(B_field, ang_freq)
    
    # Update progress bar
    if progressbar_var is not None:
        progressbar_var.set(100)
    if DEBUG_FLAG:
        print(f'  - Calculated voltages\n')

    return samplecoil_voltage + refcoil_voltage


#========================================================================================================================
# Construct application main window

root = tkinter.Tk()
root.wm_title(PROGRAM_NAME + ' v' + PROGRAM_VERSION)
root.resizable(False, False)
num_validator = root.register(is_pos_num) # Validator for enforcing user input as nonnegative real numbers
int_validator = root.register(is_pos_int) # Validator for enforcing user input as nonnegative integers

frame_main = ttk.Frame(root, padding=10)
frame_main.grid()

#------------------------------------------------------------------------------------------------------------------------
# Construct submenu for drive coil

frame_drivecoil = ttk.LabelFrame(frame_main, text='Drive Coil Parameters', padding=10)
frame_drivecoil.grid(column=0, row=0, padx=5, pady=5)

drivecoil_radius_label = ttk.Label(frame_drivecoil, text='Nominal coil radius:')
drivecoil_radius_label.grid(column=0, row=0, sticky=tkinter.E)
drivecoil_radius_entry_variable = tkinter.StringVar(value='0.0')
drivecoil_radius_entry = ttk.Entry(frame_drivecoil, textvariable=drivecoil_radius_entry_variable, validate='all', validatecommand=(num_validator, '%P'))
drivecoil_radius_entry.grid(column=1, row=0, sticky=tkinter.W+tkinter.E)
drivecoil_radius_units_variable = tkinter.StringVar(value='m')
drivecoil_radius_units = ttk.Combobox(frame_drivecoil, textvariable=drivecoil_radius_units_variable, values=LENGTH_UNITS, width=5)
drivecoil_radius_units.grid(column=2, row=0, sticky=tkinter.W+tkinter.E)
drivecoil_radius_units.state(['!disabled', 'readonly'])

drivecoil_length_label = ttk.Label(frame_drivecoil, text='Coil length:')
drivecoil_length_label.grid(column=0, row=1, sticky=tkinter.E)
drivecoil_length_entry_variable = tkinter.StringVar(value='0.0')
drivecoil_length_entry = ttk.Entry(frame_drivecoil, textvariable=drivecoil_length_entry_variable, validate='all', validatecommand=(num_validator, '%P'))
drivecoil_length_entry.grid(column=1, row=1, sticky=tkinter.W+tkinter.E)
drivecoil_length_units_variable = tkinter.StringVar(value='m')
drivecoil_length_units = ttk.Combobox(frame_drivecoil, textvariable=drivecoil_length_units_variable, values=LENGTH_UNITS, width=5)
drivecoil_length_units.grid(column=2, row=1, sticky=tkinter.W+tkinter.E)
drivecoil_length_units.state(['!disabled', 'readonly'])

drivecoil_nturns_label = ttk.Label(frame_drivecoil, text='Number of turns:')
drivecoil_nturns_label.grid(column=0, row=2, sticky=tkinter.E)
drivecoil_nturns_entry_variable = tkinter.StringVar(value='0')
drivecoil_nturns_entry = ttk.Entry(frame_drivecoil, textvariable=drivecoil_nturns_entry_variable, validate='all', validatecommand=(int_validator, '%P'))
drivecoil_nturns_entry.grid(column=1, row=2, sticky=tkinter.W+tkinter.E)

drivecoil_thickness_label = ttk.Label(frame_drivecoil, text='Wire thickness:')
drivecoil_thickness_label.grid(column=0, row=3, sticky=tkinter.E)
drivecoil_thickness_entry_variable = tkinter.StringVar(value='0.0')
drivecoil_thickness_entry = ttk.Entry(frame_drivecoil, textvariable=drivecoil_thickness_entry_variable, validate='all', validatecommand=(num_validator, '%P'))
drivecoil_thickness_entry.grid(column=1, row=3, sticky=tkinter.W+tkinter.E)
drivecoil_thickness_units_variable = tkinter.StringVar(value='mm')
drivecoil_thickness_units = ttk.Combobox(frame_drivecoil, textvariable=drivecoil_thickness_units_variable, values=LENGTH_UNITS, width=5)
drivecoil_thickness_units.grid(column=2, row=3, sticky=tkinter.W+tkinter.E)
drivecoil_thickness_units.state(['!disabled', 'readonly'])

drivecoil_material_label = ttk.Label(frame_drivecoil, text='Wire material:')
drivecoil_material_label.grid(column=0, row=4, sticky=tkinter.E)
drivecoil_material_entry_variable = tkinter.StringVar(value='')
drivecoil_material_entry = ttk.Entry(frame_drivecoil, textvariable=drivecoil_material_entry_variable)
drivecoil_material_entry.grid(column=1, row=4, columnspan=2, sticky=tkinter.W+tkinter.E)
drivecoil_material_entry.state(['readonly'])
def drivecoil_material_button_action():
    filename = tkinter.filedialog.askopenfilename(initialdir=PROGRAM_DIRECTORY, filetypes=(('Config file', '*.cfg'), ('All files', '*.*')))
    if filename is not None:
        drivecoil_material_entry_variable.set(filename)
drivecoil_material_button = ttk.Button(frame_drivecoil, text='Open...', command=drivecoil_material_button_action)
drivecoil_material_button.grid(column=3, row=4, sticky=tkinter.W+tkinter.E)

drivecoil_freq_label = ttk.Label(frame_drivecoil, text='Frequency:')
drivecoil_freq_label.grid(column=0, row=5, sticky=tkinter.E)
drivecoil_freq_entry_variable = tkinter.StringVar(value='0.0')
drivecoil_freq_entry = ttk.Entry(frame_drivecoil, textvariable=drivecoil_freq_entry_variable, validate='all', validatecommand=(num_validator, '%P'))
drivecoil_freq_entry.grid(column=1, row=5, sticky=tkinter.W+tkinter.E)
drivecoil_freq_units_variable = tkinter.StringVar(value='Hz')
drivecoil_freq_units = ttk.Combobox(frame_drivecoil, textvariable=drivecoil_freq_units_variable, values=FREQ_UNITS, width=5)
drivecoil_freq_units.grid(column=2, row=5, sticky=tkinter.W+tkinter.E)
drivecoil_freq_units.state(['!disabled', 'readonly'])

drivecoil_amp_label = ttk.Label(frame_drivecoil, text='Current:')
drivecoil_amp_label.grid(column=0, row=6, sticky=tkinter.E)
drivecoil_amp_entry_variable = tkinter.StringVar(value='0.0')
drivecoil_amp_entry = ttk.Entry(frame_drivecoil, textvariable=drivecoil_amp_entry_variable, validate='all', validatecommand=(num_validator, '%P'))
drivecoil_amp_entry.grid(column=1, row=6, sticky=tkinter.W+tkinter.E)
drivecoil_amp_units_variable = tkinter.StringVar(value='A')
drivecoil_amp_units = ttk.Combobox(frame_drivecoil, textvariable=drivecoil_amp_units_variable, values=CURRENT_UNITS, width=5)
drivecoil_amp_units.grid(column=2, row=6, sticky=tkinter.W+tkinter.E)
drivecoil_amp_units.state(['!disabled', 'readonly'])
drivecoil_amp_type_variable = tkinter.StringVar(value='pkpk')
drivecoil_amp_type = ttk.Combobox(frame_drivecoil, textvariable=drivecoil_amp_type_variable, values=('pkpk', 'rms'), width=5)
drivecoil_amp_type.grid(column=3, row=6, sticky=tkinter.W+tkinter.E)
drivecoil_amp_type.state(['!disabled', 'readonly'])

#------------------------------------------------------------------------------------------------------------------------
# Construct submenu for sample coil

frame_samplecoil = ttk.LabelFrame(frame_main, text='Sample Coil Parameters', padding=10)
frame_samplecoil.grid(column=1, row=0, padx=5, pady=5)

samplecoil_radius_label = ttk.Label(frame_samplecoil, text='Nominal coil radius:')
samplecoil_radius_label.grid(column=0, row=0, sticky=tkinter.E)
samplecoil_radius_entry_variable = tkinter.StringVar(value='0.0')
samplecoil_radius_entry = ttk.Entry(frame_samplecoil, textvariable=samplecoil_radius_entry_variable, validate='all', validatecommand=(num_validator, '%P'))
samplecoil_radius_entry.grid(column=1, row=0, sticky=tkinter.W+tkinter.E)
samplecoil_radius_units_variable = tkinter.StringVar(value='m')
samplecoil_radius_units = ttk.Combobox(frame_samplecoil, textvariable=samplecoil_radius_units_variable, values=LENGTH_UNITS, width=5)
samplecoil_radius_units.grid(column=2, row=0, sticky=tkinter.W+tkinter.E)
samplecoil_radius_units.state(['!disabled', 'readonly'])

samplecoil_length_label = ttk.Label(frame_samplecoil, text='Coil length:')
samplecoil_length_label.grid(column=0, row=1, sticky=tkinter.E)
samplecoil_length_entry_variable = tkinter.StringVar(value='0.0')
samplecoil_length_entry = ttk.Entry(frame_samplecoil, textvariable=samplecoil_length_entry_variable, validate='all', validatecommand=(num_validator, '%P'))
samplecoil_length_entry.grid(column=1, row=1, sticky=tkinter.W+tkinter.E)
samplecoil_length_units_variable = tkinter.StringVar(value='m')
samplecoil_length_units = ttk.Combobox(frame_samplecoil, textvariable=samplecoil_length_units_variable, values=LENGTH_UNITS, width=5)
samplecoil_length_units.grid(column=2, row=1, sticky=tkinter.W+tkinter.E)
samplecoil_length_units.state(['!disabled', 'readonly'])

samplecoil_nturns_label = ttk.Label(frame_samplecoil, text='Number of turns:')
samplecoil_nturns_label.grid(column=0, row=2, sticky=tkinter.E)
samplecoil_nturns_entry_variable = tkinter.StringVar(value='0')
samplecoil_nturns_entry = ttk.Entry(frame_samplecoil, textvariable=samplecoil_nturns_entry_variable, validate='all', validatecommand=(int_validator, '%P'))
samplecoil_nturns_entry.grid(column=1, row=2, sticky=tkinter.W+tkinter.E)

samplecoil_thickness_label = ttk.Label(frame_samplecoil, text='Wire thickness:')
samplecoil_thickness_label.grid(column=0, row=3, sticky=tkinter.E)
samplecoil_thickness_entry_variable = tkinter.StringVar(value='0.0')
samplecoil_thickness_entry = ttk.Entry(frame_samplecoil, textvariable=samplecoil_thickness_entry_variable, validate='all', validatecommand=(num_validator, '%P'))
samplecoil_thickness_entry.grid(column=1, row=3, sticky=tkinter.W+tkinter.E)
samplecoil_thickness_units_variable = tkinter.StringVar(value='mm')
samplecoil_thickness_units = ttk.Combobox(frame_samplecoil, textvariable=samplecoil_thickness_units_variable, values=LENGTH_UNITS, width=5)
samplecoil_thickness_units.grid(column=2, row=3, sticky=tkinter.W+tkinter.E)
samplecoil_thickness_units.state(['!disabled', 'readonly'])

samplecoil_material_label = ttk.Label(frame_samplecoil, text='Wire material:')
samplecoil_material_label.grid(column=0, row=4, sticky=tkinter.E)
samplecoil_material_entry_variable = tkinter.StringVar(value='')
samplecoil_material_entry = ttk.Entry(frame_samplecoil, textvariable=samplecoil_material_entry_variable)
samplecoil_material_entry.grid(column=1, row=4, columnspan=2, sticky=tkinter.W+tkinter.E)
samplecoil_material_entry.state(['readonly'])
def samplecoil_material_button_action():
    filename = tkinter.filedialog.askopenfilename(initialdir=PROGRAM_DIRECTORY, filetypes=(('Config file', '*.cfg'), ('All files', '*.*')))
    if filename is not None:
        samplecoil_material_entry_variable.set(filename)
samplecoil_material_button = ttk.Button(frame_samplecoil, text='Open...', command=samplecoil_material_button_action)
samplecoil_material_button.grid(column=3, row=4, sticky=tkinter.W+tkinter.E)

samplecoil_offset_label = ttk.Label(frame_samplecoil, text='Offset along axis:')
samplecoil_offset_label.grid(column=0, row=5, sticky=tkinter.E)
samplecoil_offset_entry_variable = tkinter.StringVar(value='0.0')
samplecoil_offset_entry = ttk.Entry(frame_samplecoil, textvariable=samplecoil_offset_entry_variable, validate='all', validatecommand=(root.register(is_num), '%P'))
samplecoil_offset_entry.grid(column=1, row=5, sticky=tkinter.W+tkinter.E)
samplecoil_offset_units_variable = tkinter.StringVar(value='m')
samplecoil_offset_units = ttk.Combobox(frame_samplecoil, textvariable=samplecoil_length_units_variable, values=LENGTH_UNITS, width=5)
samplecoil_offset_units.grid(column=2, row=5, sticky=tkinter.W+tkinter.E)
samplecoil_offset_units.state(['!disabled', 'readonly'])

#------------------------------------------------------------------------------------------------------------------------
# Construct submenu for reference coil

frame_refcoil = ttk.LabelFrame(frame_main, text='Reference Coil Parameters', padding=10)
frame_refcoil.grid(column=0, row=1, padx=5, pady=5)

refcoil_radius_label = ttk.Label(frame_refcoil, text='Nominal coil radius:')
refcoil_radius_label.grid(column=0, row=0, sticky=tkinter.E)
refcoil_radius_entry_variable = tkinter.StringVar(value='0.0')
refcoil_radius_entry = ttk.Entry(frame_refcoil, textvariable=refcoil_radius_entry_variable, validate='all', validatecommand=(num_validator, '%P'))
refcoil_radius_entry.grid(column=1, row=0, sticky=tkinter.W+tkinter.E)
refcoil_radius_units_variable = tkinter.StringVar(value='m')
refcoil_radius_units = ttk.Combobox(frame_refcoil, textvariable=refcoil_radius_units_variable, values=LENGTH_UNITS, width=5)
refcoil_radius_units.grid(column=2, row=0, sticky=tkinter.W+tkinter.E)
refcoil_radius_units.state(['!disabled', 'readonly'])

refcoil_length_label = ttk.Label(frame_refcoil, text='Coil length:')
refcoil_length_label.grid(column=0, row=1, sticky=tkinter.E)
refcoil_length_entry_variable = tkinter.StringVar(value='0.0')
refcoil_length_entry = ttk.Entry(frame_refcoil, textvariable=refcoil_length_entry_variable, validate='all', validatecommand=(num_validator, '%P'))
refcoil_length_entry.grid(column=1, row=1, sticky=tkinter.W+tkinter.E)
refcoil_length_units_variable = tkinter.StringVar(value='m')
refcoil_length_units = ttk.Combobox(frame_refcoil, textvariable=refcoil_length_units_variable, values=LENGTH_UNITS, width=5)
refcoil_length_units.grid(column=2, row=1, sticky=tkinter.W+tkinter.E)
refcoil_length_units.state(['!disabled', 'readonly'])

refcoil_nturns_label = ttk.Label(frame_refcoil, text='Number of turns:')
refcoil_nturns_label.grid(column=0, row=2, sticky=tkinter.E)
refcoil_nturns_entry_variable = tkinter.StringVar(value='0')
refcoil_nturns_entry = ttk.Entry(frame_refcoil, textvariable=refcoil_nturns_entry_variable, validate='all', validatecommand=(int_validator, '%P'))
refcoil_nturns_entry.grid(column=1, row=2, sticky=tkinter.W+tkinter.E)

refcoil_thickness_label = ttk.Label(frame_refcoil, text='Wire thickness:')
refcoil_thickness_label.grid(column=0, row=3, sticky=tkinter.E)
refcoil_thickness_entry_variable = tkinter.StringVar(value='0.0')
refcoil_thickness_entry = ttk.Entry(frame_refcoil, textvariable=refcoil_thickness_entry_variable, validate='all', validatecommand=(num_validator, '%P'))
refcoil_thickness_entry.grid(column=1, row=3, sticky=tkinter.W+tkinter.E)
refcoil_thickness_units_variable = tkinter.StringVar(value='mm')
refcoil_thickness_units = ttk.Combobox(frame_refcoil, textvariable=refcoil_thickness_units_variable, values=LENGTH_UNITS, width=5)
refcoil_thickness_units.grid(column=2, row=3, sticky=tkinter.W+tkinter.E)
refcoil_thickness_units.state(['!disabled', 'readonly'])

refcoil_material_label = ttk.Label(frame_refcoil, text='Wire material:')
refcoil_material_label.grid(column=0, row=4, sticky=tkinter.E)
refcoil_material_entry_variable = tkinter.StringVar(value='')
refcoil_material_entry = ttk.Entry(frame_refcoil, textvariable=refcoil_material_entry_variable)
refcoil_material_entry.grid(column=1, row=4, columnspan=2, sticky=tkinter.W+tkinter.E)
refcoil_material_entry.state(['readonly'])
def refcoil_material_button_action():
    filename = tkinter.filedialog.askopenfilename(initialdir=PROGRAM_DIRECTORY, filetypes=(('Config file', '*.cfg'), ('All files', '*.*')))
    if filename is not None:
        refcoil_material_entry_variable.set(filename)
refcoil_material_button = ttk.Button(frame_refcoil, text='Open...', command=refcoil_material_button_action)
refcoil_material_button.grid(column=3, row=4, sticky=tkinter.W+tkinter.E)

refcoil_offset_label = ttk.Label(frame_refcoil, text='Offset along axis:')
refcoil_offset_label.grid(column=0, row=5, sticky=tkinter.E)
refcoil_offset_entry_variable = tkinter.StringVar(value='0.0')
refcoil_offset_entry = ttk.Entry(frame_refcoil, textvariable=refcoil_offset_entry_variable, validate='all', validatecommand=(root.register(is_num), '%P'))
refcoil_offset_entry.grid(column=1, row=5, sticky=tkinter.W+tkinter.E)
refcoil_offset_units_variable = tkinter.StringVar(value='m')
refcoil_offset_units = ttk.Combobox(frame_refcoil, textvariable=refcoil_length_units_variable, values=LENGTH_UNITS, width=5)
refcoil_offset_units.grid(column=2, row=5, sticky=tkinter.W+tkinter.E)
refcoil_offset_units.state(['!disabled', 'readonly'])

#------------------------------------------------------------------------------------------------------------------------
# Construct submenu for sample

frame_sample = ttk.LabelFrame(frame_main, text='Test Sample', padding=10)
frame_sample.grid(column=1, row=1, padx=5, pady=5)

sample_radius_label = ttk.Label(frame_sample, text='Cylinder radius:')
sample_radius_label.grid(column=0, row=0, sticky=tkinter.E)
sample_radius_entry_variable = tkinter.StringVar(value='0.0')
sample_radius_entry = ttk.Entry(frame_sample, textvariable=sample_radius_entry_variable, validate='all', validatecommand=(num_validator, '%P'))
sample_radius_entry.grid(column=1, row=0, sticky=tkinter.W+tkinter.E)
sample_radius_units_variable = tkinter.StringVar(value='m')
sample_radius_units = ttk.Combobox(frame_sample, textvariable=sample_radius_units_variable, values=LENGTH_UNITS, width=5)
sample_radius_units.grid(column=2, row=0, sticky=tkinter.W+tkinter.E)
sample_radius_units.state(['!disabled', 'readonly'])

sample_length_label = ttk.Label(frame_sample, text='Cylinder length:')
sample_length_label.grid(column=0, row=1, sticky=tkinter.E)
sample_length_entry_variable = tkinter.StringVar(value='0.0')
sample_length_entry = ttk.Entry(frame_sample, textvariable=sample_length_entry_variable, validate='all', validatecommand=(num_validator, '%P'))
sample_length_entry.grid(column=1, row=1, sticky=tkinter.W+tkinter.E)
sample_length_units_variable = tkinter.StringVar(value='m')
sample_length_units = ttk.Combobox(frame_sample, textvariable=sample_length_units_variable, values=LENGTH_UNITS, width=5)
sample_length_units.grid(column=2, row=1, sticky=tkinter.W+tkinter.E)
sample_length_units.state(['!disabled', 'readonly'])

sample_material_label = ttk.Label(frame_sample, text='Material:')
sample_material_label.grid(column=0, row=2, sticky=tkinter.E)
sample_material_entry_variable = tkinter.StringVar(value='')
sample_material_entry = ttk.Entry(frame_sample, textvariable=sample_material_entry_variable)
sample_material_entry.grid(column=1, row=2, columnspan=2, sticky=tkinter.W+tkinter.E)
sample_material_entry.state(['readonly'])
def sample_material_button_action():
    filename = tkinter.filedialog.askopenfilename(initialdir=PROGRAM_DIRECTORY, filetypes=(('Config file', '*.cfg'), ('All files', '*.*')))
    if filename is not None:
        sample_material_entry_variable.set(filename)
sample_material_button = ttk.Button(frame_sample, text='Open...', command=sample_material_button_action)
sample_material_button.grid(column=3, row=2, sticky=tkinter.W+tkinter.E)

sample_offset_label = ttk.Label(frame_sample, text='Offset along axis:')
sample_offset_label.grid(column=0, row=3, sticky=tkinter.E)
sample_offset_entry_variable = tkinter.StringVar(value='0.0')
sample_offset_entry = ttk.Entry(frame_sample, textvariable=sample_offset_entry_variable, validate='all', validatecommand=(root.register(is_num), '%P'))
sample_offset_entry.grid(column=1, row=3, sticky=tkinter.W+tkinter.E)
sample_offset_units_variable = tkinter.StringVar(value='m')
sample_offset_units = ttk.Combobox(frame_sample, textvariable=sample_length_units_variable, values=LENGTH_UNITS, width=5)
sample_offset_units.grid(column=2, row=3, sticky=tkinter.W+tkinter.E)
sample_offset_units.state(['!disabled', 'readonly'])

#------------------------------------------------------------------------------------------------------------------------
# Construct display for the entered geometries

frame_display = ttk.LabelFrame(frame_main, text='Visualizer', padding=10)
frame_display.grid(column=2, row=0, rowspan=3, padx=5, pady=5, sticky=tkinter.N+tkinter.S)

display_width = 250
display_height = 400

display_canvas = tkinter.Canvas(frame_display, bg='#fff', width=display_width, height=display_height)
display_canvas.grid(column=0, row=0)

# Define the display's update function
def update_display():
    
    # Find all of the physical parameters (standardized to units of meters)...

    sample_r = Q_(float(sample_radius_entry_variable.get()), sample_radius_units_variable.get()).to('m').magnitude
    sample_l = Q_(float(sample_length_entry_variable.get()), sample_length_units_variable.get()).to('m').magnitude
    sample_z = Q_(float(sample_offset_entry_variable.get()), sample_offset_units_variable.get()).to('m').magnitude
    sample_z1 = sample_z - (sample_l/2)
    sample_z2 = sample_z + (sample_l/2)
    
    samplecoil_r = Q_(float(samplecoil_radius_entry_variable.get()), samplecoil_radius_units_variable.get()).to('m').magnitude
    samplecoil_l = Q_(float(samplecoil_length_entry_variable.get()), samplecoil_length_units_variable.get()).to('m').magnitude
    samplecoil_z = Q_(float(samplecoil_offset_entry_variable.get()), samplecoil_offset_units_variable.get()).to('m').magnitude
    samplecoil_z1 = samplecoil_z - (samplecoil_l/2)
    samplecoil_z2 = samplecoil_z + (samplecoil_l/2)
    
    refcoil_r = Q_(float(refcoil_radius_entry_variable.get()), refcoil_radius_units_variable.get()).to('m').magnitude
    refcoil_l = Q_(float(refcoil_length_entry_variable.get()), refcoil_length_units_variable.get()).to('m').magnitude
    refcoil_z = Q_(float(refcoil_offset_entry_variable.get()), refcoil_offset_units_variable.get()).to('m').magnitude
    refcoil_z1 = refcoil_z - (refcoil_l/2)
    refcoil_z2 = refcoil_z + (refcoil_l/2)
    
    drivecoil_r = Q_(float(drivecoil_radius_entry_variable.get()), drivecoil_radius_units_variable.get()).to('m').magnitude
    drivecoil_l = Q_(float(drivecoil_length_entry_variable.get()), drivecoil_length_units_variable.get()).to('m').magnitude
    drivecoil_z1 = -(drivecoil_l/2)
    drivecoil_z2 = (drivecoil_l/2)

    system_r = max(sample_r, samplecoil_r, refcoil_r, drivecoil_r)      # Largest r coordinate to draw
    system_z1 = min(sample_z1, samplecoil_z1, refcoil_z1, drivecoil_z1) # Most negative z coordinate to draw
    system_z2 = max(sample_z2, samplecoil_z2, refcoil_z2, drivecoil_z2) # Most positive z coordinate to draw

    if (system_r == 0.0) or (system_z1 == system_z2):                   # Abort routine early if system size is zero
        return None

    # Calculate scaling factor for nice display (with 5% margins on each side of the display)
    scale_r = display_width / (2.4 * system_r)
    scale_z = display_height / (1.1 * (system_z2 - system_z1))
    offset_r = display_width / 2
    offset_z = (display_height / 2) + (scale_z * ((system_z2 + system_z1) / 2))

    # Reset display
    display_canvas.delete('resettable') # Deletes all objects on the canvas with the "resettable" tag

    # Draw items onto screen
    display_canvas.create_rectangle(offset_r - (scale_r * drivecoil_r), offset_z - (scale_z * drivecoil_z1),
                                    offset_r + (scale_r * drivecoil_r), offset_z - (scale_z * drivecoil_z2),
                                    width=0, fill='#ccc', tags='resettable')
    display_canvas.create_rectangle(offset_r - (scale_r * refcoil_r), offset_z - (scale_z * refcoil_z1),
                                    offset_r + (scale_r * refcoil_r), offset_z - (scale_z * refcoil_z2),
                                    width=0, fill='#090', tags='resettable')
    display_canvas.create_rectangle(offset_r - (scale_r * samplecoil_r), offset_z - (scale_z * samplecoil_z1),
                                    offset_r + (scale_r * samplecoil_r), offset_z - (scale_z * samplecoil_z2),
                                    width=0, fill='#b00', tags='resettable')
    display_canvas.create_rectangle(offset_r - (scale_r * sample_r), offset_z - (scale_z * sample_z1),
                                    offset_r + (scale_r * sample_r), offset_z - (scale_z * sample_z2),
                                    width=0, fill='#99b', stipple='gray75', tags='resettable')

ttk.Button(frame_display, text='Update', command=update_display).grid(column=0, row=1, padx=5, pady=5, sticky=tkinter.S)

#------------------------------------------------------------------------------------------------------------------------
# Construct submenu for running calculation

frame_calculate = ttk.LabelFrame(frame_main, text='Calculation Settings', padding=10)
frame_calculate.grid(column=0, row=2, columnspan=2, padx=5, pady=5)

domain_radius_label = ttk.Label(frame_calculate, text='Radial resolution (no. of points):')
domain_radius_label.grid(column=0, row=0, sticky=tkinter.E)
domain_radius_entry_variable = tkinter.StringVar(value='50')
domain_radius_entry = ttk.Entry(frame_calculate, textvariable=domain_radius_entry_variable, validate='all', validatecommand=(int_validator, '%P'))
domain_radius_entry.grid(column=1, row=0, sticky=tkinter.W+tkinter.E)

domain_length_label = ttk.Label(frame_calculate, text='Axial resolution (no. of points):')
domain_length_label.grid(column=0, row=1, sticky=tkinter.E)
domain_length_entry_variable = tkinter.StringVar(value='50')
domain_length_entry = ttk.Entry(frame_calculate, textvariable=domain_length_entry_variable, validate='all', validatecommand=(int_validator, '%P'))
domain_length_entry.grid(column=1, row=1, sticky=tkinter.W+tkinter.E)

domain_time_label = ttk.Label(frame_calculate, text='Temporal resolution (no. of points):')
domain_time_label.grid(column=0, row=2, sticky=tkinter.E)
domain_time_entry_variable = tkinter.StringVar(value='50')
domain_time_entry = ttk.Entry(frame_calculate, textvariable=domain_time_entry_variable, validate='all', validatecommand=(int_validator, '%P'))
domain_time_entry.grid(column=1, row=2, sticky=tkinter.W+tkinter.E)

def run_calculation():
    
    update_display() # Update the visualizer

    # Load values from the GUI

    sample_r = Q_(float(sample_radius_entry_variable.get()), sample_radius_units_variable.get()).to('m').magnitude
    sample_l = Q_(float(sample_length_entry_variable.get()), sample_length_units_variable.get()).to('m').magnitude
    sample_z = Q_(float(sample_offset_entry_variable.get()), sample_offset_units_variable.get()).to('m').magnitude
    sample_mat = sample_material_entry_variable.get()
    
    samplecoil_r = Q_(float(samplecoil_radius_entry_variable.get()), samplecoil_radius_units_variable.get()).to('m').magnitude
    samplecoil_l = Q_(float(samplecoil_length_entry_variable.get()), samplecoil_length_units_variable.get()).to('m').magnitude
    samplecoil_z = Q_(float(samplecoil_offset_entry_variable.get()), samplecoil_offset_units_variable.get()).to('m').magnitude
    samplecoil_t = Q_(float(samplecoil_thickness_entry_variable.get()), samplecoil_thickness_units_variable.get()).to('m').magnitude
    samplecoil_N = int(samplecoil_nturns_entry_variable.get())
    samplecoil_mat = samplecoil_material_entry_variable.get()
    
    refcoil_r = Q_(float(refcoil_radius_entry_variable.get()), refcoil_radius_units_variable.get()).to('m').magnitude
    refcoil_l = Q_(float(refcoil_length_entry_variable.get()), refcoil_length_units_variable.get()).to('m').magnitude
    refcoil_z = Q_(float(refcoil_offset_entry_variable.get()), refcoil_offset_units_variable.get()).to('m').magnitude
    refcoil_t = Q_(float(refcoil_thickness_entry_variable.get()), refcoil_thickness_units_variable.get()).to('m').magnitude
    refcoil_N = int(refcoil_nturns_entry_variable.get())
    refcoil_mat = refcoil_material_entry_variable.get()
    
    drivecoil_r = Q_(float(drivecoil_radius_entry_variable.get()), drivecoil_radius_units_variable.get()).to('m').magnitude
    drivecoil_l = Q_(float(drivecoil_length_entry_variable.get()), drivecoil_length_units_variable.get()).to('m').magnitude
    drivecoil_t = Q_(float(drivecoil_thickness_entry_variable.get()), drivecoil_thickness_units_variable.get()).to('m').magnitude
    drivecoil_N = int(drivecoil_nturns_entry_variable.get())
    drivecoil_mat = drivecoil_material_entry_variable.get()

    ang_freq = float(drivecoil_freq_entry_variable.get())
    if drivecoil_freq_units_variable.get() == 'Hz':
        ang_freq *= (2 * np.pi)     # 1 Hz = 2pi rad/s
    elif drivecoil_freq_units_variable.get() == 'rpm':
        ang_freq *= (np.pi / 30)    # 1 rpm = pi/30 rad/s
    
    current = float(drivecoil_amp_entry_variable.get())
    if drivecoil_amp_type_variable.get() == 'rms':
        current *= np.sqrt(2)

    npoints_r = int(domain_radius_entry_variable.get())
    npoints_z = int(domain_length_entry_variable.get())
    npoints_t = int(domain_time_entry_variable.get())

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
        if DEBUG_FLAG:
            print(str(e) + '\n')
        tkinter.messagebox.showerror(title='Error', message='Error occured:\n\n'+str(e)+'\n\nCheck if material file is valid!')
        return None
    
    # Construct Coil objects out of the supplied parameters (and report error if any of these fail)

    try:
        drivecoil = SimpleCoil(drivecoil_r, drivecoil_l, drivecoil_N, drivecoil_mat, drivecoil_t)
        refcoil = SimpleCoil(refcoil_r, refcoil_l, refcoil_N, refcoil_mat, refcoil_t, [0, 0, -1], [0, 0, refcoil_z])
        samplecoil = SimpleCoil(samplecoil_r, samplecoil_l, samplecoil_N, samplecoil_mat, samplecoil_t, None, [0, 0, samplecoil_z])
    except Exception as e:
        if DEBUG_FLAG:
            print(str(e) + '\n')
        tkinter.messagebox.showerror(title='Error', message='Error occured:\n\n'+str(e))
        return None

    # Run the calculation

    result = calculate_voltage(drivecoil, samplecoil, refcoil, sample_mat, sample_r, sample_l, sample_z,
                               ang_freq, current, npoints_r, npoints_z, npoints_t, None)

    print('\n' + str(result))
    tkinter.messagebox.showinfo(title='Result', message='Result obtained: ' + str(result) + ' V')

ttk.Button(frame_calculate, text='Calculate!', command=run_calculation).grid(column=0, row=3, columnspan=2, padx=5, pady=5)


#========================================================================================================================
# Enter main application loop

tkinter.mainloop()
