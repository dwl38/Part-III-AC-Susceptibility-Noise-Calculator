#------------------------------------------------------------------------------------------------------------------------
# Set up Pint for simple units conversion (this should be the only copy of the units registry!)

import pint
ureg = pint.UnitRegistry()
ureg.default_format = '~P'
ureg.setup_matplotlib()
Q_ = ureg.Quantity

LENGTH_UNITS = ('m', 'cm', 'mm', 'in')  # List of acceptable units of length
FREQ_UNITS = ('Hz', 'rad/s', 'rpm')     # List of acceptable units of frequency (watch out - pint doesn't handle Hertz correctly)
CURRENT_UNITS = ('A', 'mA', 'nA', 'kA') # List of acceptable units of current
B_UNITS = ('T',)                        # List of acceptable units of B field
H_UNITS = ('A/m',)                      # List of acceptable units of H field

#------------------------------------------------------------------------------------------------------------------------
# Global constants

VACUUM_PERMITTIVITY = Q_(8.85418781E-12, ureg.farad/ureg.meter)
VACUUM_PERMEABILITY = Q_(1.256637062E-6, (ureg.second**2)/(ureg.farad * ureg.meter))
SPEED_OF_LIGHT = Q_(299792458, ureg.meter/ureg.second)

VACUUM_PERMITTIVITY_SI = VACUUM_PERMITTIVITY.to_base_units().magnitude
VACUUM_PERMEABILITY_SI = VACUUM_PERMEABILITY.to_base_units().magnitude
SPEED_OF_LIGHT_SI = SPEED_OF_LIGHT.to_base_units().magnitude

PROGRAM_NAME = 'AC Susceptibility Calculator'
PROGRAM_VERSION = '0.0.2'
PROGRAM_DESCRIPTION = ('A python tool for calculating the noise generated in an AC susceptibility measurement of an ' +
                        'arbitrary nonlinear sample; copyrighted (c) 2024 under the MIT License by Darren Wayne Lim.')

#------------------------------------------------------------------------------------------------------------------------
# Useful utility functions

import numpy as np

def is_number(x) -> bool:
    """Checks if x behaves like a scalar number, i.e. castable to complex."""
    try:
        complex(x)
        return True
    except:
        return False
    
def is_vector(x) -> bool:
    """Checks if x behaves like a vector, i.e. castable to a rank-1 NDArray."""
    try:
        test = np.array(x, dtype=complex)
        return len(test.shape) == 1
    except:
        return False

def is_np_vector(x) -> bool:
    """Stricter version of is_vector(), which requires that x is actually a rank-1 NDArray (for broadcasting etc.)."""
    return isinstance(x, np.ndarray) and len(x.shape) == 1

def is_real_number(x) -> bool:
    """Checks if x can be cast to a real number."""
    try:
        float(x)
        return True
    except:
        return False
    
def is_nonneg_real_number(x) -> bool:
    """Checks if x can be cast to a non-negative real number."""
    try:
        return float(x) >= 0.0
    except:
        return False
    
def is_nonneg_int(x) -> bool:
    """Checks if x can be cast to a non-negative integer."""
    try:
        return int(x) >= 0
    except:
        return False
