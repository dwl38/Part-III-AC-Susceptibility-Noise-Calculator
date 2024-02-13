#========================================================================================================================
# The VectorField class is a model of a continuous 3D complex vector field, i.e. a map from R3 to C3. The class itself is
# really just a fancy wrapper for scipy's built-in interpolator, but with additional functions for saving/loading from a
# file, and a standardized interface for passing values between objects.
#------------------------------------------------------------------------------------------------------------------------
# The VectorField object internally stores a set of 'data points', where each data point represents the value of the C3
# field at given R3 positions. The interpolation used is piecewise linear: to calculate the field at an arbitrary point
# within the convex hull, a linear barycentric interpolation between the four nearest data points is obtained (these
# nearest neighbours being easily obtainable by pre-triangulating the R3 space into a Delaunay mesh). Note that positions
# outside the convex hull of the data points cannot be calculated!
#========================================================================================================================

from .. import *
from collections.abc import Iterable
import numpy as np
from scipy.interpolate import LinearNDInterpolator
import warnings

#========================================================================================================================
# Class definition

class VectorField:

    #--------------------------------------------------------------------------------------------------------------------
    # Class constructor for a new VectorField. The parameters are as follows:
    #
    #     - init_points:    (NDArray) If specified, this is either a NDArray of shape (N, 3) or an iterable of NDArrays
    #                       of shape (3) of real numbers, which gives the positions of the initial data points.
    #     - init_values:    (NDArray) This must match the shape of init_points (except that it may contain complex
    #                       numbers rather than strictly real), and give the values of the initial data points.
    #

    def __init__(self, init_points: np.ndarray | Iterable[np.ndarray] | None = None,
                 init_values: np.ndarray | Iterable[np.ndarray] | None = None):

        # Class attributes
        self.points = None
        self.values = None
        self.interp = None

        # If initial points are provided, initialize them
        if init_points is not None and init_values is not None:
            self.add_data_points(init_points, init_values)
            if self.points.shape[1] != 3:
                warnings.warn(f'Created VectorField in {self.points.shape[1]}D space, which may give unintended behaviour.')

        # Error catching
        elif init_points is None and init_values is not None:
            raise RuntimeError('init_values specified without init_points!')
        else:
            raise RuntimeError('init_points specified without init_values!')
        
    #--------------------------------------------------------------------------------------------------------------------
    # Calculates the value of the VectorField at a point or list of points xi.

    def __call__(self, xi):
        if self.interp is None:
            raise RuntimeError('VectorField has no data points to interpolate from!')
        return self.interp(xi)
    
    #--------------------------------------------------------------------------------------------------------------------
    # Adds new data points to the interpolator; note that this process is expensive as it reconstructs the interpolator,
    # so gather all data points first before adding to a VectorField!
    #
    #     - points:    (NDArray) This is either a NDArray of shape (N, 3) or an iterable of NDArrays of shape (3) of real
    #                  numbers, which gives the positions of the new data points.
    #     - values:    (NDArray) This must match the shape of init_points (except that it may contain complex numbers
    #                  rather than strictly real), and give the values of the new data points.
    #

    def add_data_points(self, points: np.ndarray | Iterable[np.ndarray], values: np.ndarray | Iterable[np.ndarray]) -> None:

        # Force inputs into correct format
        new_points = np.atleast_2d(np.array(points, dtype=float))
        new_values = np.atleast_2d(np.array(values, dtype=complex))

        # Error catching
        if len(new_points.shape) != 2:
            raise RuntimeError(f'Data point coordinates must have shape (N, 3), not {new_points.shape}!')
        if len(new_values.shape) != 2:
            raise RuntimeError(f'Data point values must have shape (N, 3), not {new_values.shape}D!')
        if new_points.shape[0] != new_values.shape[0]:
            raise RuntimeError('Number of data points do not match in init_points and init_values!')

        # Append inputs to existing data points, or save them as data points if none previously exist
        if self.interp is None:
            self.points = new_points
            self.values = new_values
        else:
            self.points = np.append(self.points, new_points, axis=0)
            self.values = np.append(self.values, new_values, axis=0)

        # Ensure that all data points are unique wrt positions (no repeats allowed)
        self.points, indices = np.unique(self.points, return_index=True, axis=0)
        self.values = self.values[indices]

        # Construct the interpolator
        self.interp = LinearNDInterpolator(self.points, self.values)
    
    #--------------------------------------------------------------------------------------------------------------------
    # Loads a VectorField from a file.

    @classmethod
    def read_from_file(cls, input_file):
        loaded = np.load(input_file)
        if 'pts' not in loaded or 'val' not in loaded:
            raise RuntimeError(f'Error: could not read VectorField from {input_file}!')
        return cls(loaded['pts'], loaded['val'])
    
    #--------------------------------------------------------------------------------------------------------------------
    # Loads data points from a file.
    
    def load_from_file(self, input_file):
        loaded = np.load(input_file)
        if 'pts' not in loaded or 'val' not in loaded:
            raise RuntimeError(f'Error: could not read VectorField from {input_file}!')
        self.add_data_points(loaded['pts'], loaded['val'])

    #--------------------------------------------------------------------------------------------------------------------
    # Saves the VectorField to a file.

    def save_to_file(self, output_file):
        np.savez_compressed(output_file, pts=self.points, val=self.values)


