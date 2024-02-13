#========================================================================================================================
# The SimpleCoil class is a model of a helical solenoid made of an Ohmic material. The wire is modelled as being uniform
# and infinitesimally thin; the only 'realistic' effect implemented is the helical 'twist' of the coil.
#------------------------------------------------------------------------------------------------------------------------
# The direction of winding is always assumed to be 'right-handed' wrt the axis. The helicity is taken to be uniform
# throughout the coil.
#========================================================================================================================

from .. import *
from ..material import Material
from ..circuit.circuit_element import CircuitElement
import numpy as np
import warnings

#========================================================================================================================
# Class definition

class SimpleCoil(CircuitElement):

    #--------------------------------------------------------------------------------------------------------------------
    # Class constructor for a new SimpleCoil. The parameters are as follows:
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
    # Calculates the H field at a given position, produced by this SimpleCoil given a current.
    #
    #     - pos:      (NDArray) This can be either a vector specifying a position to calculate the H field at, or an
    #                 array of vectors representing the positions to calculate the H field at. The output type of this
    #                 function matches the input type of the pos argument, i.e. it will have the same shape.
    #     - ang_freq: (float) The angular frequency for the AC current passing through the coil; set to zero for DC.
    #     - current:  (complex) The AC current phasor passing through the coil.
    #

    def calculate_H_field(self, pos: np.ndarray, ang_freq: float, current: complex) -> np.ndarray:

        if np.allclose(self.axis, [0, 0, 1]):
            rot_mat = np.eye(3)
        elif np.allclose(self.axis, [0, 0, -1]):
            rot_mat = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])
        else:
            rot_axis = np.cross(self.axis, [0, 0, 1])
            theta = np.arcsin(np.linalg.norm(rot_axis))
            rot_axis = rot_axis / np.linalg.norm(rot_axis)
            rot_mat = np.eye(3) * np.cos(theta)
            rot_mat += np.cross(np.eye(3), rot_axis) * np.sin(theta)
            rot_mat += np.tensordot(rot_axis, rot_axis, axes=0) * (1 - np.cos(theta))
        inv_rot_mat = np.transpose(rot_mat)

        if is_np_vector(pos):
            return np.dot(inv_rot_mat, self.__point_calc_H_field(np.dot(rot_mat, pos - self.center), current))
        elif len(pos.shape) == 2 and is_np_vector(pos[0]):
            result = np.empty_like(pos)
            for i, point in enumerate(pos):
                result[i] = np.dot(inv_rot_mat, self.__point_calc_H_field(np.dot(rot_mat, point - self.center), current))
            return result
        else:
            raise RuntimeError('Input parameter pos is not an acceptable format!')

    #--------------------------------------------------------------------------------------------------------------------
    # "Secret" internal function for calculate_H_field(); performs a single-point calculation for a relative position.

    def __point_calc_H_field(self, rel_pos: np.ndarray, current: complex) -> np.ndarray:
        
        # Accuracy parameters
        N_SEGMENTS_THETA = max(20000, 200 * int(self.n_turns)) # Number of helix segments of coil axis

        # Some convenient scalars
        circumference = 2 * np.pi * self.n_turns * self.radius
        normalization = np.sqrt((circumference**2) + (self.length**2))
        circum_grad = circumference / normalization
        length_grad = self.length / normalization
        helicity = self.length / circumference
        integral_elem = (current * self.n_turns) / (4 * N_SEGMENTS_THETA)

        # Generate a uniform distribution of theta values to integrate over
        theta = np.linspace(-np.pi * self.n_turns, np.pi * self.n_turns, N_SEGMENTS_THETA, endpoint = False)

        # Generate tangent vector corresponding to theta
        et_vec = np.stack((-circum_grad * np.sin(theta), circum_grad * np.cos(theta), np.full_like(theta, length_grad)), axis=-1)

        # Calculate position of wire volume element for each value of rho, phi
        wire_pos = self.radius * np.array((np.cos(theta), np.sin(theta), helicity * theta)).transpose() # Shape is (N_theta, 3)

        # Calculate the integrand
        displacements = rel_pos - wire_pos                                       # Shape is (N_theta, 3)
        cross_products = np.cross(et_vec, displacements)                         # Shape is (N_theta, 3)
        distance_inv_cubes = np.power(np.linalg.norm(displacements, axis=1), -3) # Shape is (N_theta)
        
        # Integrate over theta
        return np.sum(cross_products * distance_inv_cubes[:, np.newaxis], axis=0) * integral_elem

    #--------------------------------------------------------------------------------------------------------------------
    # Returns the impedance of the coil based on naive calculations

    def get_impedance(self, ang_freq: float) -> complex:
        
        total_wire_length = np.sqrt((2 * np.pi * self.radius * self.n_turns)**2 + (self.length**2))

        # Naive calculation of resistance for Ohmic wire
        resistance = (total_wire_length / (self.material.conductivity() * np.pi * (self.wire_radius**2)))

        # Naive calculation of inductance for an ideal solenoid
        inductance = (VACUUM_PERMEABILITY_SI * (self.n_turns**2) * np.pi * (self.radius**2) / self.length)

        return (resistance + (1j * ang_freq * inductance))

    #--------------------------------------------------------------------------------------------------------------------
    # Satisfying CircuitElement inheritance requirements

    def is_ohmic(self) -> bool:
        return True

    def get_voltage(self, ang_freq: float, current: complex) -> complex:
        pass

    def get_diff_impedance(self, ang_freq: float, current: complex) -> complex:
        pass
