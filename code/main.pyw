#========================================================================================================================
# This is the program main; the application is executed from this script.
#------------------------------------------------------------------------------------------------------------------------
# Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna
# aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
# Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint
# occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
#========================================================================================================================

import argparse
import numpy as np
import matplotlib.pyplot as plt
import tkinter
import tkinter.ttk as ttk

from suscep_calc import *
from suscep_calc.material import Material
from suscep_calc.field.coil import Coil
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

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
# Testing, to be removed!!!

print("Hello world!")

length = 10 * ureg.meter
time = 0.5 * ureg.seconds
print(length / time)
print(VACUUM_PERMITTIVITY)

k = 1 / (4 * np.pi * VACUUM_PERMITTIVITY)

print(k.to('newton*meter**2/coulomb**2'))
print()

print('1/sqrt(eu) = ', (1/np.sqrt(VACUUM_PERMITTIVITY * VACUUM_PERMEABILITY)))
print('c = ', SPEED_OF_LIGHT)
print('Difference: ', (1/np.sqrt(VACUUM_PERMITTIVITY * VACUUM_PERMEABILITY)) - SPEED_OF_LIGHT)
print()
print()

print('-' * 20)
print('Now testing my code...')
print()

copper_material = Material.read_from_file('data/materials/copper.cfg')
print('Succesfully created copper material')
print(f'Conductivity is {Q_(copper_material.conductivity(), 1/(ureg.ohm*ureg.meter))}.')
print(f'Magnetic susceptibility is {copper_material.magnetic_susceptibility()}.')
print()

N_turns = 1000
ang_freq = 60 * 2 * np.pi
testing_coil = Coil(0.5, 10, N_turns, copper_material, 0.001)
naive_impedance = VACUUM_PERMEABILITY * (N_turns**2) * np.pi * (Q_(0.5, ureg.meter)**2) / Q_(10, ureg.meter)
print('Succesfully created coil')
print(f'Theoretical impedance is {(1j * Q_(ang_freq, ureg.hertz) * naive_impedance).to("ohm")}.')
print(f'Coil impedance is {Q_(testing_coil.get_impedance(ang_freq), ureg.ohm)}.')
print()
print(f'In theory 1A produces H field of {Q_(N_turns / 10, ureg.ampere/ureg.meter)}.')
field = testing_coil.calculate_H_field(np.array((0, 0, 0)), None, 1.0)
print(f'DC current of 1A produces H field of {Q_(field, ureg.ampere/ureg.meter)}.')
field = testing_coil.calculate_H_field(np.array((0, 0, 0)), 1200 * np.pi, 1.0)
print(f'600Hz AC current of 1A produces H field of {Q_(field, ureg.ampere/ureg.meter)}.')
print()

N_x = 10
N_z = 15
test_points = np.empty((N_x * N_z, 3), dtype=float)
for i, x in enumerate(np.linspace(-0.6, 0.6, N_x)):
    for j, z in enumerate(np.linspace(-7, 7, N_z)):
        test_points[N_x * i + j] = np.array((x, 0, z))
test_fields = testing_coil.calculate_H_field(test_points, None, 1.0)
test_fields = np.abs(test_fields)
print('Calculation complete')
print()

plt.quiver(test_points[:,0], test_points[:,2], test_fields[:,0], test_fields[:,2])
plt.title('H field of coil')
plt.xlabel('x [m]')
plt.ylabel('z [m]')
plt.show()
quit()

#========================================================================================================================
# Construct application main window

root = tkinter.Tk()
root.wm_title(PROGRAM_NAME + ' v' + PROGRAM_VERSION)

fig = Figure(figsize=(5,4), dpi=100)
axes = fig.add_subplot()
line, = axes.quiver(test_points[:,0], test_points[:,2], test_fields[:,0], test_fields[:,2])
axes.set_xlabel('x')
axes.set_ylabel('z')

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()

toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()

canvas.mpl_connect('key_press_event', lambda event: print(f'Key pressed: {event.key}'))
canvas.mpl_connect('key_press_event', key_press_handler)

button_quit = ttk.Button(master=root, text='Quit', command=root.destroy)
"""
def update_frequency(new_val):
    f = float(new_val)
    line.set_data(t, 2 * np.sin(2 * np.pi * f * t))
    canvas.draw()

slider_update = ttk.Scale(root, from_=1, to=5, orient=tkinter.HORIZONTAL, command=update_frequency, name='freq [Hz]')
"""
button_quit.pack(side=tkinter.BOTTOM)
#slider_update.pack(side=tkinter.BOTTOM)
toolbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)

#========================================================================================================================
# Enter main application loop

tkinter.mainloop()
