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
        N_SEGMENTS_THETA = max(3000, 30 * int(self.n_turns)) # Number of helix segments of coil axis
        N_SEGMENTS_RHO = 15                                  # Number of wire-radial segments
        N_SEGMENTS_PHI = 60                                  # Number of wire-azimuthal segments

        # Some convenient scalars
        circumference = 2 * np.pi * self.n_turns * self.radius
        normalization = np.sqrt((circumference**2) + (self.length**2))
        circum_grad = circumference / normalization
        length_grad = self.length / normalization
        helicity = self.length / circumference
        integral_elem = normalization / (2 * N_SEGMENTS_THETA * N_SEGMENTS_PHI)

        # Generate a uniform distribution of theta values to integrate over
        theta = np.linspace(-np.pi * self.n_turns, np.pi * self.n_turns, N_SEGMENTS_THETA, endpoint = False)

        # Generate a non-uniform distribution of rho values to integrate over
        rho_sqs = np.linspace(0, (self.wire_radius**2), N_SEGMENTS_RHO)
        rho = np.sqrt(rho_sqs)

        # Generate a uniform distribution of phi values to integrate over
        phi = np.linspace(0, 2 * np.pi, N_SEGMENTS_PHI, endpoint=False)

        # Generate tangent vectors corresponding to theta
        et_vec = np.stack((-circum_grad * np.sin(theta), circum_grad * np.cos(theta), np.full_like(theta, length_grad)), axis=-1)
        er_vec = np.stack((np.cos(theta), np.sin(theta), np.zeros_like(theta)), axis=-1)
        ez_vec = np.stack((length_grad * np.sin(theta), -length_grad * np.cos(theta), np.full_like(theta, circum_grad)), axis=-1)

        # Calculate position of wire volume element for each value of rho, phi
        helix_pos = self.radius * np.array((np.cos(theta), np.sin(theta), helicity * theta)).transpose() # Shape is (N_theta, 3)
        ang_vecs = np.tensordot(np.cos(phi), er_vec, axes=0) + np.tensordot(np.sin(phi), ez_vec, axes=0) # Shape is (N_phi, N_theta, 3)
        wire_pos = helix_pos + np.tensordot(rho, ang_vecs, axes=0)                                       # Shape is (N_rho, N_phi, N_theta, 3)

        # Calculate current density, which is uniform for DC and affected by skin effect for AC
        if wave_number is None:
            density = np.full_like(rho, surface_density)
        else:
            density = surface_density * jv(0, wave_number * rho) / jv(0, wave_number * self.wire_radius)

        # Calculate the integrand
        displacements = rel_pos - wire_pos                                       # Shape is (N_rho, N_phi, N_theta, 3)
        cross_products = np.cross(et_vec, displacements)                         # Shape is (N_rho, N_phi, N_theta, 3)
        distance_inv_cubes = np.power(np.linalg.norm(displacements, axis=3), -3) # Shape is (N_rho, N_phi, N_theta)
            
        # Integrate over theta and phi
        integrands = np.einsum('ijkl,i,i,ijk->il', cross_products, density, rho, distance_inv_cubes, optimize=True) * integral_elem
        
        # Integrate over rho
        return np.trapz(integrands, rho, axis=0)

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