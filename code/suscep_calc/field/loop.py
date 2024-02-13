#========================================================================================================================
# The Loop class is a model of the simplest magnetic field producing device: a simple wire loop made of an Ohmic
# material. The wire is modelled as being uniform and infinitesimally thin.
#------------------------------------------------------------------------------------------------------------------------
# The direction of winding is always assumed to be 'right-handed' wrt the axis.
#========================================================================================================================

from .. import *
from ..material import Material
from ..circuit.circuit_element import CircuitElement
from .vector_field import VectorField
import numpy as np
import warnings

#========================================================================================================================
# Class definition

class Loop(CircuitElement):

    #--------------------------------------------------------------------------------------------------------------------
    # Class constructor for a new Loop. The parameters are as follows:
    #
    #     - radius:         (float) The radius of the coil.
    #     - material:       (Material) The material of the wire; it should be Ohmic.
    #     - wire_thickness: (float) The diameter of the wire.
    #     - axis:           (NDArray) The vector representing the axis of the loop; defaults to the z-axis.
    #     - center:         (NDArray) The vector representing the position of the loop's center; defaults to the origin.
    #

    def __init__(self, radius: float, material: Material, wire_thickness: float,
                 axis: np.ndarray = None, center: np.ndarray = None):
        
        # Initial assignments
        self.radius = float(radius)
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
        if self.wire_thickness < 0.0:
            raise RuntimeError('Coil wire thickness cannot be negative!')
        if self.wire_radius > self.radius:
            warnings.warn('Loop is too tightly wound - wire intersects itself', RuntimeWarning)
        if not self.material.is_ohmic():
            warnings.warn('Coil class currently only supports Ohmic materials!', RuntimeWarning)
            
            
    #--------------------------------------------------------------------------------------------------------------------
    # Calculates the H field at a given position, produced by this Loop given a current.
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
        N_SEGMENTS_THETA = 200

        # Calculate integral over theta
        integral_elem = (current) / (4 * N_SEGMENTS_THETA)
        theta = np.linspace(-np.pi, np.pi, N_SEGMENTS_THETA, endpoint = False)                              # Shape is (N_theta)
        et_vec = np.stack((-np.sin(theta), np.cos(theta), np.zeros_like(theta)), axis=-1)                   # Shape is (N_theta)
        wire_pos = self.radius * np.array((np.cos(theta), np.sin(theta), np.zeros_like(theta))).transpose() # Shape is (N_theta, 3)
        displacements = rel_pos - wire_pos                                                                  # Shape is (N_theta, 3)
        cross_products = np.cross(et_vec, displacements)                                                    # Shape is (N_theta, 3)
        distance_inv_cubes = np.power(np.linalg.norm(displacements, axis=1), -3)                            # Shape is (N_theta)
        return np.sum(cross_products * distance_inv_cubes[:, np.newaxis], axis=0) * integral_elem

    #--------------------------------------------------------------------------------------------------------------------
    # Calculates the AC voltage phasor induced in this Loop, given a B (phasor) field and its frequency.
    #
    #     - B_field:  (VectorField) The B field, as a C3 vector phasor, at all locations in space. Importantly, this loop
    #                 must be fully contained within the convex hull of the VectorField's data points!
    #     - ang_freq: (float) The angular frequency for the AC field passing through the coil; set to zero for DC.
    #

    def calculate_induced_voltage(self, B_field: VectorField, ang_freq: float) -> complex:

        if ang_freq is None or ang_freq == 0.0:
            return 0.0

        # Accuracy parameters
        N_SEGMENTS_RHO = 20
        N_SEGMENTS_PHI = 65

        # Generate a non-uniform distribution of rho values to integrate over
        rho_sqs = np.linspace(0, (self.wire_radius**2), N_SEGMENTS_RHO)
        rho = np.sqrt(rho_sqs)

        # Generate a uniform distribution of phi values to integrate over
        phi = np.linspace(0, 2 * np.pi, N_SEGMENTS_PHI, endpoint=False)

        # Generate plane vectors for plane of loop
        if np.allclose(self.axis, [0, 0, 1]):
            ex = np.array((1, 0, 0))
            ey = np.array((0, 1, 0))
        elif np.allclose(self.axis, [0, 0, -1]):
            ex = np.array((1, 0, 0))
            ey = np.array((0, -1, 0))
        else:
            ex = np.cross(self.axis, [0, 0, 1])
            ex = ex / np.linalg.norm(ex)
            ey = np.cross(self.axis, ex)

        # Calculate position of loop area element for each value of rho, phi
        ang_vecs = np.tensordot(np.cos(phi), ex, axes=0) + np.tensordot(np.sin(phi), ey, axes=0) # Shape is (N_phi, 3)
        area_elem_pos = self.center + np.tensordot(rho, ang_vecs, axes=0)                        # Shape is (N_rho, N_phi, 3)

        # Get projection of B field and integrate over phi
        flux_elems = np.dot(B_field(area_elem_pos), self.axis)                                      # Shape is (N_rho, N_phi)
        integrands = np.sum(flux_elems * rho[:, np.newaxis], axis=1) * (2 * np.pi / N_SEGMENTS_PHI) # Shape is (N_rho)

        # Integrate over rho
        return (-1j * ang_freq) * np.trapz(integrands, rho, axis=0)

    #--------------------------------------------------------------------------------------------------------------------
    # Returns the impedance of the coil based on naive calculations

    def get_impedance(self, ang_freq: float) -> complex:
        
        circumference = 2 * np.pi * self.radius

        # Naive calculation of resistance for Ohmic wire
        resistance = (circumference / (self.material.conductivity() * np.pi * (self.wire_radius**2)))

        # Naive approximation of inductance for a wire loop
        inductance = (VACUUM_PERMEABILITY_SI * self.radius * (np.log(8 * self.radius / self.wire_radius) - 2))

        return (resistance + (1j * ang_freq * inductance))

    #--------------------------------------------------------------------------------------------------------------------
    # Satisfying CircuitElement inheritance requirements

    def is_ohmic(self) -> bool:
        return True

    def get_voltage(self, ang_freq: float, current: complex) -> complex:
        pass

    def get_diff_impedance(self, ang_freq: float, current: complex) -> complex:
        pass

