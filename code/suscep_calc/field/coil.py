#========================================================================================================================
# The Coil class is a model of a helical solenoid made of an Ohmic material, taking into account realistic effects like
# finite wire thickness and helical 'twist' of the coil.
#------------------------------------------------------------------------------------------------------------------------
# The direction of winding is always assumed to be 'right-handed' wrt the axis. The helicity is taken to be uniform
# throughout the coil.
#========================================================================================================================

from .. import *
from ..material import Material
from ..circuit.circuit_element import CircuitElement
import numpy as np
from scipy.special import jv
import warnings

#========================================================================================================================
# Class definition

class Coil(CircuitElement):

    #--------------------------------------------------------------------------------------------------------------------
    # Class constructor for a new Coil. The parameters are as follows:
    #
    #     - coil_radius:    (float) The radius of the coil.
    #     - coil_length:    (float) The end-to-end length of the coil.
    #     - n_turns:        (float) The total number of turns in the coil; it can be fractional for partial turns.
    #     - material:       (Material) The material of the wire; it should be Ohmic.
    #     - wire_thickness: (float) The diameter of the wire.
    #     - axis:           (NDArray) The vector representing the axis of the coil; defaults to the z-axis.
    #

    def __init__(self, coil_radius: float, coil_length: float, n_turns: float, material: Material, wire_thickness: float,
                 axis: np.ndarray = None):
        
        # Initial assignments
        self.radius = coil_radius
        self.length = coil_length
        self.n_turns = n_turns
        self.material = material
        self.wire_thickness = wire_thickness
        self.axis = np.array((0, 0, 1), dtype=float)
        if axis is not None and is_vector(axis):
            unnormed = np.array(axis, dtype=float)
            self.axis = unnormed / np.linalg.norm(unnormed)

        # Assertions
        if self.radius < 0.0:
            raise RuntimeError('Coil radius cannot be negative!')
        if self.length < 0.0:
            raise RuntimeError('Coil length cannot be negative!')
        if self.n_turns < 0.0:
            raise RuntimeError('Number of coil turns cannot be negative!')
        if self.wire_thickness < 0.0:
            raise RuntimeError('Coil wire thickness cannot be negative!')
        if self.wire_thickness > (2 * self.radius):
            warnings.warn('Coil is too tightly wound - wire intersects itself', RuntimeWarning)
        if (self.n_turns * self.wire_thickness) > self.length:
            warnings.warn('Coil is too tightly packed - wire intersects itself', RuntimeWarning)
        if not self.material.is_ohmic():
            warnings.warn('Coil class currently only supports Ohmic materials!', RuntimeWarning)
            
    #--------------------------------------------------------------------------------------------------------------------
    # Returns the naive impedance of the coil; note that the real part (resistance) does account for skin effect, but the
    # imaginary part (inductance) does not account for any of the realistic effects beyond skin effect!

    def get_impedance(self, ang_freq: float) -> complex:
        
        total_wire_length = np.sqrt((2 * np.pi * self.radius * self.n_turns)**2 + (self.length**2))

        # Calculating impedance per unit length of the wire due to skin effect
        if ang_freq is None or ang_freq == 0.0:
            wire_impedance = ((4.0 * total_wire_length) / (self.material.conductivity() * np.pi * (self.wire_thickness**2)))
        else:
            skin_depth = np.sqrt(2 / (ang_freq * self.material.conductivity() *
                         (1.0 + self.material.magnetic_susceptibility()) * VACUUM_PERMEABILITY.to_base_units().magnitude))
            wave_number = (1 - 1j) / skin_depth
            wave_phase = wave_number * self.wire_thickness / 2
            skin_factor = jv(0, wave_phase) / jv(1, wave_phase)
            wire_impedance = ((wave_number / (self.material.conductivity() * np.pi * self.wire_thickness)) *
                              skin_factor * total_wire_length)

        # Naive calculation of inductance for an ideal solenoid
        inductance = (VACUUM_PERMEABILITY.to_base_units().magnitude * (self.n_turns**2) *
                      np.pi * (self.radius**2) / self.length)

        return (wire_impedance + (1j * ang_freq * inductance))

    #--------------------------------------------------------------------------------------------------------------------
    # Satisfying CircuitElement inheritance requirements

    def is_ohmic(self) -> bool:
        return True

    def get_voltage(self, ang_freq: float, current: complex) -> complex:
        pass

    def get_diff_impedance(self, ang_freq: float, current: complex) -> complex:
        pass