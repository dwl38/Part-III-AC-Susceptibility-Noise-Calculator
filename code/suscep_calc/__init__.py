#------------------------------------------------------------------------------------------------------------------------
# Set up Pint for simple units conversion (this should be the only copy of the units registry!)

import pint
ureg = pint.UnitRegistry()
ureg.default_format = '~P'
ureg.setup_matplotlib()
Q_ = ureg.Quantity

#------------------------------------------------------------------------------------------------------------------------
# Global constants

VACUUM_PERMITTIVITY = Q_(8.85418781E-12, ureg.farad/ureg.meter)
VACUUM_PERMEABILITY = Q_(1.256637062E-6, (ureg.second**2)/(ureg.farad * ureg.meter))
SPEED_OF_LIGHT = Q_(299792458, ureg.meter/ureg.second)

PROGRAM_NAME = 'AC Susceptibility Calculator'
PROGRAM_VERSION = '0.0.1'
PROGRAM_DESCRIPTION = ('A python tool for calculating the noise generated in an AC susceptibility measurement of an ' +
                        'arbitrary nonlinear sample; authored by Darren Wayne Lim.')