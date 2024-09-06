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
import tkinter
import tkinter.ttk as ttk
import tkinter.filedialog
import tkinter.messagebox

from suscep_calc import *
from suscep_calc.material import Material
from suscep_calc.field import SimpleCoil, VectorField
from suscep_calc.circuit.circuit_element import CircuitElement

import suscep_calc.gui as gui


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
# Big calculation function (runs the full calculation)

def calculate_voltage(drivecoil: CircuitElement, samplecoil: CircuitElement, refcoil: CircuitElement,
                      sample_mat: Material, sample_r: float, sample_l: float, sample_z: float,
                      ang_freq: float, current: complex,
                      npoints_r: int, npoints_z: int, npoints_t: int,
                      progressbar_window: tkinter.Toplevel = None, progressbar_var: tkinter.IntVar = None) -> complex:
    
    if DEBUG_FLAG:
        print('Function \'calculate_voltage\' launched.')
    if progressbar_window is not None and progressbar_var is not None:
        progressbar_var.set(0)
        progressbar_window.update()

    # Find outer bounds of the system (assuming cylindrical symmetry!)
    system_r = max(samplecoil.radius, refcoil.radius, sample_r)
    system_z1 = min(samplecoil.center[2] - (samplecoil.length/2), refcoil.center[2] - (refcoil.length/2), sample_z - (sample_l/2))
    system_z2 = max(samplecoil.center[2] + (samplecoil.length/2), refcoil.center[2] + (refcoil.length/2), sample_z + (sample_l/2))
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
    if progressbar_window is not None and progressbar_var is not None:
        progressbar_var.set(10)
        progressbar_window.update()
    if DEBUG_FLAG:
        print(f'  - Generated {test_points.shape[0]} test points')

    # Calculate H field
    H_field_flattened = drivecoil.calculate_H_field(test_points, ang_freq, current)
    
    # Update progress bar
    if progressbar_window is not None and progressbar_var is not None:
        progressbar_var.set(40)
        progressbar_window.update()
    if DEBUG_FLAG:
        print(f'  - Calculated H field of drive coil')

    # Calculate B field
    B_field_flattened = np.zeros_like(H_field_flattened, dtype=complex)

    if sample_mat.is_magnetically_linear():
        # Case 1: sample is linear. Then B field is simply permeability times H field, inside and outside the sample.
        # We iterate through all calculated points and check if they are inside the sample cylinder; if inside, multiply
        # by the absolute sample permeability, otherwise if outside multiply by the vacuum permeability.
        sample_permeability = VACUUM_PERMEABILITY_SI * (1 + sample_mat.magnetic_susceptibility())
        for i in range(test_points.shape[0]):
            if (test_points[i, 0] < sample_r) and (abs(test_points[i, 2] - sample_z) < (sample_l / 2)):
                B_field_flattened[i] = sample_permeability * H_field_flattened[i]
            else:
                B_field_flattened[i] = VACUUM_PERMEABILITY_SI * H_field_flattened[i]

    else:
        # Case 2: sample is nonlinear. Then calculation needs to switch to the time domain if calculated points lie
        # inside the sample cylinder.
        for i in range(test_points.shape[0]):
            if (test_points[i, 0] < sample_r) and (abs(test_points[i, 2] - sample_z) < (sample_l / 2)):
                H_field_phasors = [(H_field_flattened[i], ang_freq),]
                B_field_phasors = sample_mat.calculate_B_field_from_H_field(H_field_phasors, npoints_t)
                for phasor in B_field_phasors:
                    if phasor[1] == ang_freq:
                        B_field_flattened[i] = phasor[0]
            else:
                B_field_flattened[i] = VACUUM_PERMEABILITY_SI * H_field_flattened[i]
        
    # Update progress bar
    if progressbar_window is not None and progressbar_var is not None:
        progressbar_var.set(60)
        progressbar_window.update()
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
    if progressbar_window is not None and progressbar_var is not None:
        progressbar_var.set(70)
        progressbar_window.update()
    if DEBUG_FLAG:
        print(f'  - Extrapolated B field around cylindrical symmetry')

    # Calculate the induced voltages in the reference and sample coils
    samplecoil_voltage = samplecoil.calculate_induced_voltage(B_field, ang_freq)
    refcoil_voltage = refcoil.calculate_induced_voltage(B_field, ang_freq)
    
    # Update progress bar
    if progressbar_window is not None and progressbar_var is not None:
        progressbar_var.set(100)
        progressbar_window.update()
    if DEBUG_FLAG:
        print(f'  - Calculated voltages\n')

    return samplecoil_voltage + refcoil_voltage


#========================================================================================================================
# Construct application main window

root = tkinter.Tk()
root.wm_title(PROGRAM_NAME + ' v' + PROGRAM_VERSION)
root.resizable(False, False)
num_validator = root.register(is_real_number)            # Validator for enforcing user input as real number
pos_num_validator = root.register(is_nonneg_real_number) # Validator for enforcing user input as nonnegative real number
pos_int_validator = root.register(is_nonneg_int)         # Validator for enforcing user input as nonnegative integer

frame_main = ttk.Frame(root, padding=10)
frame_main.grid()

#---------------------------------------------
# Construct various sub-menus and GUI elements

drivecoil_submenu = gui.Drivecoil(frame_main, pos_num_validator, pos_int_validator, PROGRAM_DIRECTORY)
drivecoil_submenu.grid(column=0, row=0, padx=5, pady=5)

samplecoil_submenu = gui.Samplecoil(frame_main, num_validator, pos_num_validator, pos_int_validator, PROGRAM_DIRECTORY)
samplecoil_submenu.grid(column=1, row=0, padx=5, pady=5)

refcoil_submenu = gui.Refcoil(frame_main, num_validator, pos_num_validator, pos_int_validator, PROGRAM_DIRECTORY)
refcoil_submenu.grid(column=0, row=1, padx=5, pady=5)

sample_submenu = gui.Sample(frame_main, num_validator, pos_num_validator, pos_int_validator, PROGRAM_DIRECTORY)
sample_submenu.grid(column=1, row=1, padx=5, pady=5)

visualizer = gui.Visualizer(frame_main)
visualizer.grid(column=2, row=0, rowspan=3, padx=5, pady=5, sticky=tkinter.N+tkinter.S)

calculation_submenu = gui.CalculationSubmenu(frame_main, pos_int_validator)
calculation_submenu.grid(column=0, row=2, padx=5, pady=5)

saveload_submenu = gui.FileIO(frame_main, [drivecoil_submenu, samplecoil_submenu, refcoil_submenu,
                               sample_submenu, visualizer, calculation_submenu], PROGRAM_DIRECTORY)
saveload_submenu.grid(column=1, row=2, padx=5, pady=5)

#---------------------------------------------------------
# Define function for extracting parameters from sub-menus

def get_current_parameters() -> dict:
    output = drivecoil_submenu.get_configuration()
    output = samplecoil_submenu.get_configuration(output)
    output = refcoil_submenu.get_configuration(output)
    output = sample_submenu.get_configuration(output)
    output = calculation_submenu.get_configuration(output)
    return output

#------------------
# Activate submenus

visualizer.activate(get_current_parameters)
calculation_submenu.activate(get_current_parameters, calculate_voltage, [visualizer.update_display,])


#========================================================================================================================
# Enter main application loop

tkinter.mainloop()
