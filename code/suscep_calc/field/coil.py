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
    #     - center:         (NDArray) The vector representing the position of the coil's center; defaults to the origin.
    #

    def __init__(self, coil_radius: float, coil_length: float, n_turns: float, material: Material, wire_thickness: float,
                 axis: np.ndarray = None, center: np.ndarray = None):
        
        # Initial assignments
        self.radius = float(coil_radius)
        self.length = float(coil_length)
        self.n_turns = float(n_turns)
        self.material = material
        self.wire_thickness = float(wire_thickness)
        self.wire_radius = self.wire_thickness / 2.0

        self.axis = np.array((0, 0, 1), dtype=float)
        if axis is not None and is_vector(axis):
            unnormed = np.array(axis, dtype=float)
            self.axis = unnormed / np.linalg.norm(unnormed)

        self.center = np.array((0, 0, 0), dtype=float)
        if center is not None and is_vector(center):
            self.center = np.array(center, dtype=float)

        # Assertions
        if self.radius < 0.0:
            raise RuntimeError('Coil radius cannot be negative!')
        if self.length < 0.0:
            raise RuntimeError('Coil length cannot be negative!')
        if self.n_turns < 0.0:
            raise RuntimeError('Number of coil turns cannot be negative!')
        if self.wire_thickness < 0.0:
            raise RuntimeError('Coil wire thickness cannot be negative!')
        if self.wire_radius > self.radius:
            warnings.warn('Coil is too tightly wound - wire intersects itself', RuntimeWarning)
        if (self.n_turns * self.wire_thickness) > self.length:
            warnings.warn('Coil is too tightly packed - wire intersects itself', RuntimeWarning)
        if not self.material.is_ohmic():
            warnings.warn('Coil class currently only supports Ohmic materials!', RuntimeWarning)
            
            
    #--------------------------------------------------------------------------------------------------------------------
    # Calculates the H field at a given position, produced by this Coil given a current.
    #
    #     - pos:      (NDArray) This can be either a vector specifying a position to calculate the H field at, or an
    #                 array of vectors representing the positions to calculate the H field at. The output type of this
    #                 function matches the input type of the pos argument, i.e. it will have the same shape.
    #     - ang_freq: (float) The angular frequency for the AC current passing through the coil; set to zero for DC.
    #     - current:  (complex) The AC current phasor passing through the coil.
    #

    def calculate_H_field(self, pos: np.ndarray, ang_freq: float, current: complex) -> np.ndarray:

        if ang_freq is None or ang_freq == 0.0:
            wave_number = None
            surface_density = current / (np.pi * (self.wire_radius**2))
        else:
            skin_depth = np.sqrt(2 / (ang_freq * self.material.conductivity() *
                         (1.0 + self.material.magnetic_susceptibility()) * VACUUM_PERMEABILITY_SI))
            wave_number = (1 - 1j) / skin_depth
            surface_density = ((current * wave_number * jv(0, wave_number * self.wire_radius)) / 
                               (np.pi * self.wire_thickness * jv(1, wave_number * self.wire_radius)))

        if is_np_vector(pos):
            return self.__point_calc_H_field(pos, surface_density, wave_number)
        elif len(pos.shape) == 2 and is_np_vector(pos[0]):
            result = np.empty_like(pos)
            for i, point in enumerate(pos):
                result[i] = self.__point_calc_H_field(point, surface_density, wave_number)
            return result
        else:
            raise RuntimeError('Input parameter pos is not an acceptable format!')

    #--------------------------------------------------------------------------------------------------------------------
    # "Secret" internal function for calculate_H_field(); performs a single-point calculation for a relative position.

    def __point_calc_H_field(self, rel_pos: np.ndarray, surface_density: complex, wave_number: complex) -> np.ndarray:
        
        # Accuracy parameters
        N_SEGMENTS_THETA = max(2000, 10 * int(self.n_turns)) # Number of helix segments of coil axis
        N_SEGMENTS_RHO = 10                                  # Number of wire-radial segments
        N_SEGMENTS_PHI = 60                                  # Number of wire-azimuthal segments

        # Some convenient definitions
        circumference = 2 * np.pi * self.n_turns * self.radius
        normalization = np.sqrt((circumference**2) + (self.length**2))
        integral_elem = (normalization * self.wire_radius) / (2 * N_SEGMENTS_THETA * N_SEGMENTS_RHO * N_SEGMENTS_PHI)
        result = np.zeros_like(rel_pos, dtype=complex)

        # Integrate over theta
        for theta in np.linspace(-np.pi * self.n_turns, np.pi * self.n_turns, N_SEGMENTS_THETA):

            length_elem = np.array((-circumference * np.sin(theta), circumference * np.cos(theta), self.length)) / normalization
            helix_pos = np.array((np.cos(theta), np.sin(theta), self.length * theta / circumference)) * self.radius
            radial_elem = np.array((np.cos(theta), np.sin(theta), 0.0))
            perp_elem = np.array((self.length * np.sin(theta), -self.length * np.cos(theta), circumference)) / normalization

            # Integrate over rho and phi
            for rho in np.linspace(0, self.wire_radius, N_SEGMENTS_RHO):

                phi = np.linspace(0, 2 * np.pi, N_SEGMENTS_PHI, endpoint=False)
                ang_vecs = np.tensordot(np.cos(phi), radial_elem, axes=0) + np.tensordot(np.sin(phi), perp_elem, axes=0)
                displacements = rel_pos - helix_pos - (rho * ang_vecs)
                cross_products = np.cross(length_elem, displacements)
                distance_cubes = np.power(np.linalg.norm(displacements, axis=1), 3)

                # Current density affected by skin effect for AC (or uniform for DC)
                if wave_number is None:
                    density = surface_density
                else:
                    density = surface_density * jv(0, wave_number * rho) / jv(0, wave_number * self.wire_radius)
                
                result += np.sum((cross_products * density * rho * integral_elem) / distance_cubes[:, np.newaxis], axis=0)

        return result

    #--------------------------------------------------------------------------------------------------------------------
    # Returns the naive impedance of the coil; note that the real part (resistance) does account for skin effect, but the
    # imaginary part (inductance) does not account for any of the realistic effects beyond skin effect!

    def get_impedance(self, ang_freq: float) -> complex:
        
        total_wire_length = np.sqrt((2 * np.pi * self.radius * self.n_turns)**2 + (self.length**2))

        # Calculating impedance per unit length of the wire due to skin effect
        if ang_freq is None or ang_freq == 0.0:
            wire_impedance = (total_wire_length / (self.material.conductivity() * np.pi * (self.wire_radius**2)))
        else:
            skin_depth = np.sqrt(2 / (ang_freq * self.material.conductivity() *
                         (1.0 + self.material.magnetic_susceptibility()) * VACUUM_PERMEABILITY_SI))
            wave_number = (1 - 1j) / skin_depth
            skin_factor = jv(0, wave_number * self.wire_radius) / jv(1, wave_number * self.wire_radius)
            wire_impedance = ((wave_number / (self.material.conductivity() * np.pi * self.wire_thickness)) *
                              skin_factor * total_wire_length)

        # Naive calculation of inductance for an ideal solenoid
        inductance = (VACUUM_PERMEABILITY_SI * (self.n_turns**2) * np.pi * (self.radius**2) / self.length)

        return (wire_impedance + (1j * ang_freq * inductance))

    #--------------------------------------------------------------------------------------------------------------------
    # Satisfying CircuitElement inheritance requirements

    def is_ohmic(self) -> bool:
        return True

    def get_voltage(self, ang_freq: float, current: complex) -> complex:
        pass

    def get_diff_impedance(self, ang_freq: float, current: complex) -> complex:
        pass