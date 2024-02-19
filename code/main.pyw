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
from suscep_calc.field import *
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

copper_material = Material.read_from_file('data/materials/copper.cfg')
print('Succesfully created copper material')
print(f'Conductivity is {Q_(copper_material.conductivity(), 1/(ureg.ohm*ureg.meter))}.')
print(f'Magnetic susceptibility is {copper_material.magnetic_susceptibility()}.')
print()

N_turns = 180
ang_freq = 60 * 2 * np.pi
radius = 0.5
length = 2
#testing_coil = Coil(radius, length, N_turns, copper_material, 0.001)
testing_coil = SimpleCoil(radius, length, N_turns, copper_material, 0.001, axis=[0.2, 0, 0.7])
#testing_coil = Loop(radius, copper_material, 0.001, axis=[0.2,0,0.8])
naive_impedance = VACUUM_PERMEABILITY * (N_turns**2) * np.pi * (Q_(radius, ureg.meter)**2) / Q_(length, ureg.meter)
print('Succesfully created coil')
print(f'Theoretical impedance is {(1j * Q_(ang_freq, ureg.hertz) * naive_impedance).to("ohm")}.')
print(f'Coil impedance is {Q_(testing_coil.get_impedance(ang_freq), ureg.ohm)}.')
print()
print(f'In theory 1A produces H field of {Q_(N_turns / length, ureg.ampere/ureg.meter)}.')
#print(f'In theory 1A produces H field of {Q_(1 / (2 * radius), ureg.ampere/ureg.meter)}.')
field = testing_coil.calculate_H_field(np.array((0, 0, 0)), None, 1.0)
print(f'DC current of 1A produces H field of {Q_(field, ureg.ampere/ureg.meter)}.')
field = testing_coil.calculate_H_field(np.array((0, 0, 0)), 1200 * np.pi, 1.0)
print(f'600Hz AC current of 1A produces H field of {Q_(field, ureg.ampere/ureg.meter)}.')
print()

N_x = 20
N_z = 35
extent = (-1, 1, -1.8, 1.8)
test_points = np.zeros((N_x * N_x * N_z, 3), dtype=float)
for i, x in enumerate(np.linspace(extent[0], extent[1], N_x)):
    for j, y in enumerate(np.linspace(extent[0], extent[1], N_x)):
        for k, z in enumerate(np.linspace(extent[2], extent[3], N_z)):
            test_points[(N_z * N_x * i) + (N_z * j) + k] = np.array((x, y, z))
test_fields = testing_coil.calculate_H_field(test_points, ang_freq, 1.0)
test_fields = np.real(test_fields)
field_strengths = np.linalg.norm(test_fields, axis=1)
print('Calculation complete')
print()

field = VACUUM_PERMEABILITY_SI * VectorField(test_points, test_fields)

xpts, ypts = np.meshgrid(np.linspace(extent[0], extent[1], N_x), np.linspace(extent[2], extent[3], N_z))
pts = np.stack((xpts, np.zeros_like(xpts), ypts), axis=-1)
field_pts = np.real(field(pts))
stream_c = np.linalg.norm(field_pts, axis=-1)

fig, axs = plt.subplots(1, 2)
stream = axs[0].streamplot(xpts, ypts, field_pts[:,:,0], field_pts[:,:,2], color=stream_c, cmap='autumn')
fig.colorbar(stream.lines, ax=axs[0])
axs[0].set_title('B field of coil (in xz plane)')
axs[0].set_xlabel('x [m]')
axs[0].set_ylabel('z [m]')

intensity = axs[1].imshow(field_pts[:,:,1], origin='lower', extent=extent, aspect='auto', cmap='bwr', interpolation='bicubic')
fig.colorbar(intensity, ax=axs[1])
axs[1].set_title('B field of coil (y component)')
axs[1].set_xlabel('x [m]')
axs[1].set_ylabel('z [m]')
plt.show()

induction_coil = SimpleCoil(radius/2, length/2, N_turns/2, copper_material, 0.001)
voltage = induction_coil.calculate_induced_voltage(field, ang_freq)
print(f'60Hz AC current of 1A in outer coil produces voltage of {Q_(voltage, ureg.volt)} in inner coil.')
print()
voltage = testing_coil.calculate_induced_voltage(field, ang_freq)
print(f'Outer coil self-induced voltage is {Q_(voltage, ureg.volt)} according to integral.')
print(f'Expected {Q_(-testing_coil.get_impedance(ang_freq), ureg.volt)}.')
print()
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
