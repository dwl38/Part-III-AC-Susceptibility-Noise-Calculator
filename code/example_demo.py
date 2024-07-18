#========================================================================================================================
# This is a testing script, which accesses the modules in suscep_calc to perform a few simple calculations.
#------------------------------------------------------------------------------------------------------------------------
# Author's notes:
#
#   - The __init__ for suscep_calc automatically loads Pint in for smart unit conversion. In this script, it is being
#     used to print dimensionfull numbers nicely. Despite the automatic loading, however, the underlying objects/modules
#     within suscep_calc are NOT inherently Pint-friendly; they assume SI units in the values.
#
#   - In Pint's notation, the Q_ class is used to create dimensionfull quantities.
#
#   - See material.py in suscep_calc for an explanation of the material file format.
#
#   - The Coil object fully models a helical coil with finite wire thickness; calculations with this are very slow, as
#     the integral is three-dimensional (integrating over the wire thickness). For most purposes, the SimpleCoil object
#     (which neglects wire thickness) is 99.9% accurate as long as skin effect isn't significant.
#
#========================================================================================================================

import numpy as np
import matplotlib.pyplot as plt

from suscep_calc import *
from suscep_calc.material import Material
from suscep_calc.field import *
from matplotlib.figure import Figure


#------------------------------------------------------------------------------------------------------------------------
# Test: read a material file ("copper.cfg") and see if it can load values from it
#------------------------------------------------------------------------------------------------------------------------

copper_material = Material.read_from_file('data/materials/copper.cfg')
print('Succesfully created copper material')
print(f'Conductivity is {Q_(copper_material.conductivity(), 1/(ureg.ohm*ureg.meter))}.')
print(f'Magnetic susceptibility is {copper_material.magnetic_susceptibility()}.')
print()


#------------------------------------------------------------------------------------------------------------------------
# Test: create a coil and do some calculations with it
#------------------------------------------------------------------------------------------------------------------------

#----------------
# Coil parameters

N_turns = 180
ang_freq = 60 * 2 * np.pi
radius = 0.5
length = 2

#---------------------
# Create a Coil object

#testing_coil = Coil(radius, length, N_turns, copper_material, 0.001)
testing_coil = SimpleCoil(radius, length, N_turns, copper_material, 0.001)
#testing_coil = Loop(radius, copper_material, 0.001, axis=[0.2,0,0.8])
print('Succesfully created coil')

#-----------------------------------------------
# Do some test calculations of simple properties

naive_impedance = VACUUM_PERMEABILITY * (N_turns**2) * np.pi * (Q_(radius, ureg.meter)**2) / Q_(length, ureg.meter)
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


#------------------------------------------------------------------------------------------------------------------------
# Test: calculate an entire H field and plot it
#------------------------------------------------------------------------------------------------------------------------

#------------------------------
# Spatial resolution parameters
N_x = 20
N_z = 35
extent = (-1, 1, -1.8, 1.8)

#----------------------
# Calculate the H field

test_points = np.zeros((N_x * N_x * N_z, 3), dtype=float)
for i, x in enumerate(np.linspace(extent[0], extent[1], N_x)):
    for j, y in enumerate(np.linspace(extent[0], extent[1], N_x)):
        for k, z in enumerate(np.linspace(extent[2], extent[3], N_z)):
            test_points[(N_z * N_x * i) + (N_z * j) + k] = np.array((x, y, z)) # Generate points in space...

test_fields = testing_coil.calculate_H_field(test_points, ang_freq, 1.0)       # ...then calculate the H field at those points

test_fields = np.real(test_fields)                    # Just to convert complex phasors into real numbers so that matplotlib won't complain...
field_strengths = np.linalg.norm(test_fields, axis=1) # Field magnitude
print('Calculation complete')
print()

#-----------------------------------------------------------------------------
# Author's note: this was a test of the VectorField object that got left in...

field = VectorField(test_points, test_fields)

#----------------------
# Plot the H field

# 2D coordinates on the xz plane, for plotting
xpts, ypts = np.meshgrid(np.linspace(extent[0], extent[1], N_x), np.linspace(extent[2], extent[3], N_z))

# Extend those 2D coordinates into 3D (with y=0) since VectorField expects 3D coordinates
pts = np.stack((xpts, np.zeros_like(xpts), ypts), axis=-1)

# Evaluate the VectorField on the xz plane, and convert to real numbers again so that matplotlib won't complain
field_pts = np.real(field(pts))

# Field magnitude on the xz plane
stream_c = np.linalg.norm(field_pts, axis=-1)

# Setting up matplotlib
fig, axs = plt.subplots(1, 2)
stream = axs[0].streamplot(xpts, ypts, field_pts[:,:,0], field_pts[:,:,2], color=stream_c, cmap='autumn')
fig.colorbar(stream.lines, ax=axs[0])
axs[0].set_title('H field of coil (in xz plane)')
axs[0].set_xlabel('x [m]')
axs[0].set_ylabel('z [m]')
intensity = axs[1].imshow(field_pts[:,:,1], origin='lower', extent=extent, aspect='auto', cmap='bwr', interpolation='bicubic')
fig.colorbar(intensity, ax=axs[1])
axs[1].set_title('H field of coil (y component)')
axs[1].set_xlabel('x [m]')
axs[1].set_ylabel('z [m]')
plt.show() # Show


#------------------------------------------------------------------------------------------------------------------------
# Test: calculate the mutual inductance with a small test coil
# Author's note: for some reason, the predicted voltage is way off. I haven't figured out where the error is...
#------------------------------------------------------------------------------------------------------------------------

induction_coil = SimpleCoil(radius/2, length/2, N_turns/2, copper_material, 0.001)
voltage = induction_coil.calculate_induced_voltage(field, ang_freq)
print(f'60Hz AC current of 1A in outer coil produces voltage of {Q_(voltage, ureg.volt)} in inner coil.')


