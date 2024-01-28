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
import pandas as pd
import tkinter
import tkinter.ttk as ttk

from suscep_calc import *
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

#========================================================================================================================
# Construct application main window

root = tkinter.Tk()
root.wm_title(PROGRAM_NAME + ' v' + PROGRAM_VERSION)

fig = Figure(figsize=(5,4), dpi=100)
t = np.arange(0, 3, 0.01)
axes = fig.add_subplot()
line, = axes.plot(t, 2 * np.sin(2 * np.pi * t))
axes.set_xlabel('time [s]')
axes.set_ylabel('f(t)')

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()

toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()

canvas.mpl_connect('key_press_event', lambda event: print(f'Key pressed: {event.key}'))
canvas.mpl_connect('key_press_event', key_press_handler)

button_quit = ttk.Button(master=root, text='Quit', command=root.destroy)

def update_frequency(new_val):
    f = float(new_val)
    line.set_data(t, 2 * np.sin(2 * np.pi * f * t))
    canvas.draw()

slider_update = ttk.Scale(root, from_=1, to=5, orient=tkinter.HORIZONTAL, command=update_frequency, name='freq [Hz]')

button_quit.pack(side=tkinter.BOTTOM)
slider_update.pack(side=tkinter.BOTTOM)
toolbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)

#========================================================================================================================
# Enter main application loop

tkinter.mainloop()
