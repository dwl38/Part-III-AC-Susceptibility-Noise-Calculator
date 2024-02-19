#========================================================================================================================
# The VectorField class is a model of a continuous d-dimensional complex vector field over 3D space, i.e. a map from R3
# to C^d. The class itself is really just a fancy wrapper for scipy's built-in interpolator, but with added functionality
# for saving/loading from a file, and a standardized interface for passing values between objects.
#------------------------------------------------------------------------------------------------------------------------
# The VectorField object internally stores a set of 'data points', where each data point represents the value of the C^d
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
    #     - init_values:    (NDArray) This must be specified along with init_points, and must be either a NDArray of
    #                       shape (N, d) or an iterable of NDArrays of shape (d) of complex numbers, which gives the
    #                       values of the initial data points.
    #

    def __init__(self, init_points: np.ndarray | Iterable[np.ndarray] | None = None,
                 init_values: np.ndarray | Iterable[np.ndarray] | None = None):

        # Class attributes
        self.points = None
        self.values = None
        self.interp = None
        self.ndims = None

        # If initial points are provided, initialize them
        if init_points is not None and init_values is not None:
            self.add_data_points(init_points, init_values)
            if self.points.shape[1] != 3:
                warnings.warn(f'Created VectorField in {self.points.shape[1]}D space, which may give unintended behaviour.')

        # Error catching
        elif init_points is None and init_values is not None:
            raise RuntimeError('init_values specified without init_points!')
        elif init_values is None and init_points is not None:
            raise RuntimeError('init_points specified without init_values!')
        
    #--------------------------------------------------------------------------------------------------------------------
    # Calculates the value of the VectorField at a point or list of points xi.

    def __call__(self, xi):

        # Construct the interpolator, if it hasn't already been
        if self.interp is None:
            if self.points is None:
                raise RuntimeError('VectorField has no data points to interpolate from!')
            self.interp = LinearNDInterpolator(self.points, self.values)
        
        return self.interp(xi)
    
    #--------------------------------------------------------------------------------------------------------------------
    # Adds new data points to the interpolator.
    #
    #     - points:    (NDArray) This is either a NDArray of shape (N, 3) or an iterable of NDArrays of shape (3) of real
    #                  numbers, which gives the positions of the new data points.
    #     - values:    (NDArray) This is either a NDArray of shape (N, d) or an iterable of NDArrays of shape (d) of
    #                  complex numbers, which gives the values of the new data points.
    #

    def add_data_points(self, points: np.ndarray | Iterable[np.ndarray], values: np.ndarray | Iterable[np.ndarray]) -> None:

        # Force inputs into correct format
        new_points = np.atleast_2d(np.array(points, dtype=float))
        new_values = np.array(values, dtype=complex)
        if len(new_values.shape) == 1 and new_values.shape[0] == new_points.shape[0]:
            new_values = new_values[:, np.newaxis] # Special case for d = 1
        else:
            new_values = np.atleast_2d(new_values)

        # Error catching
        if len(new_points.shape) != 2:
            raise RuntimeError(f'Data point coordinates must have shape (N, 3), not {new_points.shape}!')
        if len(new_values.shape) != 2:
            raise RuntimeError(f'Data point values must have shape (N, d), not {new_values.shape}!')
        if new_points.shape[0] != new_values.shape[0]:
            raise RuntimeError('Number of data points do not match in init_points and init_values!')

        # Append inputs to existing data points, or save them as data points if none previously exist
        if self.points is None:
            self.points = new_points
            self.values = new_values
            self.ndims = self.values.shape[1]
        else:
            if self.ndims != new_values.shape[1]:
                raise RuntimeError('Cannot add data points with different dimensionality!')
            self.points = np.append(self.points, new_points, axis=0)
            self.values = np.append(self.values, new_values, axis=0)

        # Ensure that all data points are unique wrt positions (no repeats allowed)
        self.points, indices = np.unique(self.points, return_index=True, axis=0)
        self.values = self.values[indices]

        # Reset the interpolator (it will be reconstructed at the next call-time)
        self.interp = None
    
    #--------------------------------------------------------------------------------------------------------------------
    # Loads a VectorField from a file.

    @classmethod
    def read_from_file(cls, input_file):
        loaded = np.load(input_file)
        if 'pts' not in loaded or 'val' not in loaded:
            raise RuntimeError(f'Error: could not read VectorField from {input_file}!')
        return cls(loaded['pts'], loaded['val'])
    
    #--------------------------------------------------------------------------------------------------------------------
    # Loads data points from a file. (WARNING: if this VectorField already has pre-existing data points, this method
    # appends the new data point from the file on top of the pre-existing ones without necessarily overwriting it!)
    
    def load_from_file(self, input_file):
        loaded = np.load(input_file)
        if 'pts' not in loaded or 'val' not in loaded:
            raise RuntimeError(f'Error: could not read VectorField from {input_file}!')
        self.add_data_points(loaded['pts'], loaded['val'])

    #--------------------------------------------------------------------------------------------------------------------
    # Saves the VectorField to a file.

    def save_to_file(self, output_file):
        np.savez_compressed(output_file, pts=self.points, val=self.values)
        
    #--------------------------------------------------------------------------------------------------------------------
    # Returns the complex conjugate of this VectorField.

    def conj(self):
        if self.points is None:
            return VectorField()
        return VectorField(self.points, np.conj(self.values))

    #--------------------------------------------------------------------------------------------------------------------
    # Binary arithmetic operations for VectorFields.

    def __add__(self, other):
        """Addition is defined between a VectorField and a constant vector, or between two VectorFields. Note that adding
        two VectorFields will generate a new VectorField whose data points are the union of those of the two constituents
        but within the intersection of their convex hulls, which might introduce interpolation errors."""
        if self.values is None:
            raise RuntimeError('This VectorField has not been initialized!')
        if is_vector(other):
            new_values = self.values + np.array(other, dtype=complex)
            return VectorField(self.points, new_values)
        elif self.ndims == 1 and is_number(other):
            new_values = self.values + other # Special case for d = 1
            return VectorField(self.points, new_values)
        elif isinstance(other, VectorField):
            if self.ndims != other.ndims:
                raise RuntimeError(f'Cannot add VectorFields of different dimensions (d={self.ndims} and d={other.ndims})!')
            new_points = np.unique(np.append(self.points, other.points, axis=0), axis=0) # Union of points
            new_values = self(new_points) + other(new_points)
            nan_indices = np.isnan(new_values[:, 0]) # Need to remove points outside either convex hull!
            new_points = new_points[np.logical_not(nan_indices)]
            new_values = new_values[np.logical_not(nan_indices)]
            return VectorField(new_points, new_values)
        else:
            return NotImplemented

    def __sub__(self, other):
        """Subtraction is defined between a VectorField and a constant vector, or between two VectorFields. Note that
        subtracting two VectorFields will generate a new VectorField whose data points are the union of those of the two
        constituents but within the intersection of their convex hulls, which might introduce interpolation errors."""
        if self.values is None:
            raise RuntimeError('This VectorField has not been initialized!')
        if is_vector(other):
            new_values = self.values - np.array(other, dtype=complex)
            return VectorField(self.points, new_values)
        elif self.ndims == 1 and is_number(other):
            new_values = self.values - other # Special case for d = 1
            return VectorField(self.points, new_values)
        elif isinstance(other, VectorField):
            if self.ndims != other.ndims:
                raise RuntimeError(f'Cannot subtract VectorFields of different dimensions (d={self.ndims} and d={other.ndims})!')
            new_points = np.unique(np.append(self.points, other.points, axis=0), axis=0) # Union of points
            new_values = self(new_points) - other(new_points)
            nan_indices = np.isnan(new_values[:, 0]) # Need to remove points outside either convex hull!
            new_points = new_points[np.logical_not(nan_indices)]
            new_values = new_values[np.logical_not(nan_indices)]
            return VectorField(new_points, new_values)
        else:
            return NotImplemented
        
    def __mul__(self, other):
        """Multiplication is defined between a VectorField and a constant scalar, or (as a special case) between a
        d-dimensional VectorField and a 1-dimensional VectorField (representing a scalar field). Note that this special
        case generates a new VectorField whose data points are the union of those of the two constituents but within the
        intersection of their convex hulls, which might introduce interpolation errors."""
        if self.values is None:
            raise RuntimeError('This VectorField has not been initialized!')
        if is_number(other):
            new_values = self.values * other
            return VectorField(self.points, new_values)
        elif isinstance(other, VectorField):
            if self.ndims == 1 or other.ndims == 1:
                new_points = np.unique(np.append(self.points, other.points, axis=0), axis=0)
                new_values = self(new_points) * other(new_points)
                nan_indices = np.isnan(new_values[:, 0])
                new_points = new_points[np.logical_not(nan_indices)]
                new_values = new_values[np.logical_not(nan_indices)]
                return VectorField(new_points, new_values)
            else:
                return NotImplemented
        else:
            return NotImplemented
        
    def __matmul__(self, other):
        """The matrix multiplication operator @ is interpreted specifically as a shorthand for the scalar inner product
        between two complex VectorFields of equal dimension. Note that this generates a new 1-dimensional VectorField
        whose data points are the union of those of the two constituents but within the intersection of their convex
        hulls, which might introduce interpolation errors."""
        if self.values is None:
            raise RuntimeError('This VectorField has not been initialized!')
        if is_vector(other):
            new_values = np.dot(np.conj(self.values), np.array(other, dtype=complex))
            return VectorField(self.points, new_values)
        elif isinstance(other, VectorField):
            if self.ndims != other.ndims:
                raise RuntimeError(f'Cannot dot VectorFields of different dimensions (d={self.ndims} and d={other.ndims})!')
            new_points = np.unique(np.append(self.points, other.points, axis=0), axis=0)
            new_values = np.einsum('ij,ij->i', np.conj(self(new_points)), other(new_points))
            nan_indices = np.isnan(new_values[:, 0])
            new_points = new_points[np.logical_not(nan_indices)]
            new_values = new_values[np.logical_not(nan_indices)]
            return VectorField(new_points, new_values)
        else:
            return NotImplemented
        
    def __truediv__(self, other):
        """Division is defined between a VectorField and a constant scalar, or (as a special case) between a d-dimensional
        VectorField and a 1-dimensional VectorField (representing a scalar field). Note that this special case generates
        a new VectorField whose data points are the union of those of the two constituents but within the intersection of
        their convex hulls, which might introduce interpolation errors."""
        if self.values is None:
                raise RuntimeError('This VectorField has not been initialized!')
        if is_number(other):
            new_values = self.values / other
            return VectorField(self.points, new_values)
        elif isinstance(other, VectorField):
            if other.ndims == 1:
                new_points = np.unique(np.append(self.points, other.points, axis=0), axis=0)
                new_values = self(new_points) / other(new_points)
                nan_indices = np.isnan(new_values[:, 0])
                new_points = new_points[np.logical_not(nan_indices)]
                new_values = new_values[np.logical_not(nan_indices)]
                return VectorField(new_points, new_values)
            else:
                raise RuntimeError(f'Cannot divide by a VectorField of dimension {other.ndims}!')
        else:
            return NotImplemented
        
    def __radd__(self, other):
        """Addition is defined between a constant vector and a VectorField."""
        if self.values is None:
            raise RuntimeError('This VectorField has not been initialized!')
        if is_vector(other):
            new_values = np.array(other, dtype=complex) + self.values
            return VectorField(self.points, new_values)
        elif self.ndims == 1 and is_number(other):
            new_values = other + self.values # Special case for d = 1
            return VectorField(self.points, new_values)
        else:
            return NotImplemented
        
    def __rsub__(self, other):
        """Subtraction is defined between a constant vector and a VectorField."""
        if self.values is None:
            raise RuntimeError('This VectorField has not been initialized!')
        if is_vector(other):
            new_values = np.array(other, dtype=complex) - self.values
            return VectorField(self.points, new_values)
        elif self.ndims == 1 and is_number(other):
            new_values = other - self.values # Special case for d = 1
            return VectorField(self.points, new_values)
        else:
            return NotImplemented
        
    def __rmul__(self, other):
        """Multiplication is defined between a constant scalar and a VectorField."""
        if self.values is None:
            raise RuntimeError('This VectorField has not been initialized!')
        if is_number(other):
            new_values = other * self.values
            return VectorField(self.points, new_values)
        else:
            return NotImplemented
        
    def __rmatmul__(self, other):
        """The matrix multiplication operator @ is interpreted specifically as a shorthand for the scalar inner product
        between a constant complex vector and a complex VectorField of equal dimension."""
        if self.values is None:
            raise RuntimeError('This VectorField has not been initialized!')
        if is_vector(other):
            new_values = np.dot(self.values, np.conj(np.array(other, dtype=complex)))
            return VectorField(self.points, new_values)
        else:
            return NotImplemented
        
    def __rtruediv__(self, other):
        """Division is defined between a constant scalar and a 1-dimensional VectorField (representing a scalar field)."""
        if self.values is None:
                raise RuntimeError('This VectorField has not been initialized!')
        if is_number(other):
            if self.ndims == 1:
                new_values = other / self.values
                return VectorField(self.points, new_values)
            else:
                raise RuntimeError(f'Cannot divide by a VectorField of dimension {self.ndims}!')
        else:
            return NotImplemented
        
    #--------------------------------------------------------------------------------------------------------------------
    # Incremental arithmetic operations for VectorFields.
        
    def __iadd__(self, other):
        if self.values is None:
            raise RuntimeError('This VectorField has not been initialized!')
        if is_vector(other):
            self.values += np.array(other, dtype=complex)
            self.interp = None
            return self
        elif self.ndims == 1 and is_number(other):
            self.values += other # Special case for d = 1
            self.interp = None
            return self
        elif isinstance(other, VectorField):
            if self.ndims != other.ndims:
                raise RuntimeError(f'Cannot add VectorFields of different dimensions (d={self.ndims} and d={other.ndims})!')
            new_points = np.unique(np.append(self.points, other.points, axis=0), axis=0) # Union of points
            new_values = self(new_points) + other(new_points)
            nan_indices = np.isnan(new_values[:, 0]) # Need to remove points outside either convex hull!
            self.points = new_points[np.logical_not(nan_indices)]
            self.values = new_values[np.logical_not(nan_indices)]
            self.interp = None
            return self
        else:
            return NotImplemented
        
    def __isub__(self, other):
        if self.values is None:
            raise RuntimeError('This VectorField has not been initialized!')
        if is_vector(other):
            self.values -= np.array(other, dtype=complex)
            self.interp = None
            return self
        elif self.ndims == 1 and is_number(other):
            self.values -= other # Special case for d = 1
            self.interp = None
            return self
        elif isinstance(other, VectorField):
            if self.ndims != other.ndims:
                raise RuntimeError(f'Cannot subtract VectorFields of different dimensions (d={self.ndims} and d={other.ndims})!')
            new_points = np.unique(np.append(self.points, other.points, axis=0), axis=0) # Union of points
            new_values = self(new_points) - other(new_points)
            nan_indices = np.isnan(new_values[:, 0]) # Need to remove points outside either convex hull!
            self.points = new_points[np.logical_not(nan_indices)]
            self.values = new_values[np.logical_not(nan_indices)]
            self.interp = None
            return self
        else:
            return NotImplemented
        
    def __imul__(self, other):
        if self.values is None:
            raise RuntimeError('This VectorField has not been initialized!')
        if is_number(other):
            self.values *= other
            self.interp = None
            return self
        elif isinstance(other, VectorField):
            if self.ndims == 1 or other.ndims == 1:
                new_points = np.unique(np.append(self.points, other.points, axis=0), axis=0)
                new_values = self(new_points) * other(new_points)
                nan_indices = np.isnan(new_values[:, 0])
                self.points = new_points[np.logical_not(nan_indices)]
                self.values = new_values[np.logical_not(nan_indices)]
                self.interp = None
                self.ndims = self.values.shape[1]
                return self
            else:
                return NotImplemented
        else:
            return NotImplemented
        
    def __itruediv__(self, other):
        if self.values is None:
                raise RuntimeError('This VectorField has not been initialized!')
        if is_number(other):
            self.values /= other
            self.interp = None
            return self
        elif isinstance(other, VectorField):
            if other.ndims == 1:
                new_points = np.unique(np.append(self.points, other.points, axis=0), axis=0)
                new_values = self(new_points) / other(new_points)
                nan_indices = np.isnan(new_values[:, 0])
                self.points = new_points[np.logical_not(nan_indices)]
                self.values = new_values[np.logical_not(nan_indices)]
                self.interp = None
                return self
            else:
                raise RuntimeError(f'Cannot divide by a VectorField of dimension {other.ndims}!')
        else:
            return NotImplemented
        
    #--------------------------------------------------------------------------------------------------------------------
    # Unary arithmetic operations for VectorFields.

    def __neg__(self):
        if self.points is None:
            return VectorField()
        return VectorField(self.points, -self.values)
    
    def __pos__(self):
        if self.points is None:
            return VectorField()
        return VectorField(self.points, self.values)
    
    def __abs__(self):
        if self.points is None:
            return VectorField()
        return VectorField(self.points, np.linalg.norm(self.values, axis=1))


    