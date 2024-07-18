#========================================================================================================================
# The Material class stores the electrodynamic properties of a given material; in particular the electrical conductivity,
# (static) electric & magnetic susceptibilities, and magnetization response. These properties can be specified either as
# constants or as functions of several input parameters, including temperature and external field strength.
#
# The properties are stored within the class as a ConfigParser object, which behaves almost exactly like a dictionary of
# dictionaries, except with some added logic for default values and case-insensitivity. Values can be set and retrieved
# from the ConfigParser by specifying two case-insensitive string keys ('section' and 'option').
#------------------------------------------------------------------------------------------------------------------------
# The fields inside the material properties are specified as per the following format; note that specific fields are
# allowed to be missing (e.g. 'conductivity.tensor') if they are irrelevant to the material. Fields marked with * are
# compulsory.
#
# [Section 'misc']:
#     name*:      (str) Material name.
#     desc*:      (str) Material description.
#
# [Section 'conductivity']:
#     ohmic*:       (bool) Whether the material is Ohmic or has a nonlinear response.
#     conductivity: (float) The conductivity for an isotropic & Ohmic material, measured in S/m.
#     curve:        (NDArray) A list of current densities against electric field strengths, as non-negative scalars,
#                     specifying the response curve for an isotropic & nonlinear material.
#
# [Section 'electrical']:
#     type*:          (str) Is either 'dielectric' or 'ferroelectric'.
#     susceptibility: (float) The dimensionless electrostatic susceptibility for an isotropic & dielectric material.
#     alpha:          (float) The Jiles-Atherton parameter for interdomain coupling in an isotropic & ferroelectric
#                       material; dimensionless.
#     a:              (float) The Jiles-Atherton parameter for domain wall density in an isotropic & ferroelectric
#                       material; has units of C/m^2.
#     psat:           (float) The Jiles-Atherton parameter for the saturation polarization of an isotropic &
#                       ferroelectric material; has units of C/m^2.
#     k:              (float) The Jiles-Atherton parameter for the energy needed to break pinning sites in an isotropic &
#                       ferroelectric material; has units of C/m^2.
#     c:              (float) The Jiles-Atherton parameter for the polarization reversibility in an isotropic &
#                       ferroelectric material; dimensionless.
#
# [Section 'magnetic']:
#     type*:          (str) Is either 'diamagnetic' or 'ferromagnetic'; in this context 'paramagnetic' is equivalent to
#                       'diamagnetic' since the response is also linear, while 'ferrimagnetic' or 'antiferromagnetic' are
#                       equivalent to 'ferromagnetic' since the response curve is implemented generally.
#     susceptibility: (float) The dimensionless magnetostatic susceptibility for an isotropic & diamagnetic material.
#     alpha:          (float) The Jiles-Atherton parameter for interdomain coupling in an isotropic & ferromagnetic
#                       material; dimensionless.
#     a:              (float) The Jiles-Atherton parameter for domain wall density in an isotropic & ferromagnetic
#                       material; has units of A/m.
#     msat:           (float) The Jiles-Atherton parameter for the saturation magnetization of an isotropic &
#                       ferromagnetic material; has units of A/m.
#     k:              (float) The Jiles-Atherton parameter for the energy needed to break pinning sites in an isotropic &
#                       ferromagnetic material; has units of A/m.
#     c:              (float) The Jiles-Atherton parameter for the magnetization reversibility in an isotropic &
#                       ferromagnetic material; dimensionless.
#
#========================================================================================================================

from . import *
import configparser
import numpy as np
import json

#========================================================================================================================
# Class definition

class Material:

    #--------------------------------------------------------------------------------------------------------------------
    # Class constructor for a new Material. This constructor should not be used directly! See read_from_file instead.
    #
    #     - init: Either a dict of dicts, or a ConfigParser, containing the properties of the material being defined.
    #
    
    def __init__(self, init: dict | configparser.ConfigParser):
        
        self.properties = configparser.ConfigParser()
        
        # Data type sanitization

        if isinstance(init, (dict, configparser.ConfigParser)):
            if 'misc' in init and isinstance(init['misc'], (dict, configparser.SectionProxy)):
                self.properties['misc'] = init['misc']
            if 'conductivity' in init and isinstance(init['conductivity'], (dict, configparser.SectionProxy)):
                self.properties['conductivity'] = init['conductivity']
            if 'electrical' in init and isinstance(init['electrical'], (dict, configparser.SectionProxy)):
                self.properties['electrical'] = init['electrical']
            if 'magnetic' in init and isinstance(init['magnetic'], (dict, configparser.SectionProxy)):
                self.properties['magnetic'] = init['magnetic']

        # Check for missing values and implement default values if needed

        if 'misc' not in self.properties:
            self.properties['misc'] = dict()
        if 'name' not in self.properties['misc']:
            self.properties['misc']['name'] = 'Vacuum'
        if 'desc' not in self.properties['misc']:
            self.properties['misc']['desc'] = 'Classical vaccum'

        if 'conductivity' not in self.properties:
            self.properties['conductivity'] = dict()
        if 'ohmic' not in self.properties['conductivity']:
            self.properties['conductivity'] = {'ohmic': 'True', 'conductivity': '0.0'}

        if 'electrical' not in self.properties:
            self.properties['electrical'] = dict()
        if 'type' not in self.properties['electrical']:
            self.properties['electrical'] = {'type': 'dielectric', 'susceptibility': '0.0'}
        else:
            t = self.properties['electrical']['type'].casefold()
            if t == 'dielectric':
                self.properties['electrical']['type'] = 'dielectric'
            elif t == 'ferroelectric':
                self.properties['electrical']['type'] = 'ferroelectric'
            else:
                raise RuntimeError(f'Unrecognized material type "{t}"!')
                
        if 'magnetic' not in self.properties:
            self.properties['magnetic'] = dict()
        if 'type' not in self.properties['magnetic']:
            self.properties['magnetic'] = {'type': 'diamagnetic', 'susceptibility': '0.0'}
        else:
            t = self.properties['magnetic']['type'].casefold()
            if t == 'diamagnetic' or t == 'paramagnetic':
                self.properties['magnetic']['type'] = 'diamagnetic'
            elif t == 'ferromagnetic' or t == 'ferrimagnetic' or t == 'antiferromagnetic':
                self.properties['magnetic']['type'] = 'ferromagnetic'
            else:
                raise RuntimeError(f'Unrecognized material type "{t}"!')
                
    #--------------------------------------------------------------------------------------------------------------------
    # Loads a Material from a file.

    @classmethod
    def read_from_file(cls, input_file):
        config = configparser.ConfigParser()
        config.read(input_file)
        return cls(config)
    
    #--------------------------------------------------------------------------------------------------------------------
    # Saves the Material to a file.

    def save_to_file(self, output_file):
        with open(output_file, 'w') as configfile:
            self.properties.write(configfile)

    #====================================================================================================================
    # Various specific (and type-sanitized) retrivals of properties.

    #--------------------------------------------------------------------------------------------------------------------
    # Returns true if the material is Ohmic, false otherwise.

    def is_ohmic(self) -> bool:
        return self.properties.getboolean('conductivity', 'ohmic')
    
    #--------------------------------------------------------------------------------------------------------------------
    # Returns the material's electrical conductivity if it is Ohmic.

    def conductivity(self) -> float:
        """WARNING: this will crash if the material is not Ohmic! Use current_at_field() for general safety."""
        return self.properties.getfloat('conductivity', 'conductivity')
    
    #--------------------------------------------------------------------------------------------------------------------
    # Calculates the current density J, given a static electric field E. The input can be either a scalar or a vector.

    def current_at_field(self, E_field):
        if self.properties.getboolean('conductivity', 'ohmic'):
            return self.properties.getfloat('conductivity', 'conductivity') * E_field
        else:
            if is_np_vector(E_field):
                # TODO: this currently only takes the positive side (i.e. globally stable solution) of the hysteresis curve.
                # Will need 'past' value of J_field to account for hysteresis!
                E_field_magnitude = np.linalg.norm(E_field)
                J_field_magnitude = np.interp(E_field_magnitude, self.conductivity_curve[0], self.conductivity_curve[1])
                return (J_field_magnitude / E_field_magnitude) * E_field
            else:
                return np.interp(float(E_field), self.conductivity_curve[0], self.conductivity_curve[1])
            
    #--------------------------------------------------------------------------------------------------------------------
    # Returns true if the material is dielectric (i.e. electrostatically linear), false otherwise.

    def is_dielectric(self) -> bool:
        return self.properties['electrical']['type'].casefold() == 'dielectric'
    
    #--------------------------------------------------------------------------------------------------------------------
    # Returns the material's electrical susceptibility if it is dielectric.

    def electrical_susceptibility(self) -> float:
        """WARNING: this will crash if the material is not dielectric!"""
        return self.properties.getfloat('electrical', 'susceptibility')
    
    #--------------------------------------------------------------------------------------------------------------------
    # Returns the material's Jiles-Atherton parameters for modelling polarization hysteresis, if it is ferroelectric.

    def electrical_JA_parameters(self) -> dict:
        result = dict()
        result['alpha'] = self.properties.getfloat('electrical', 'alpha')
        result['a'] = self.properties.getfloat('electrical', 'a')
        result['psat'] = self.properties.getfloat('electrical', 'psat')
        result['k'] = self.properties.getfloat('electrical', 'k')
        result['c'] = self.properties.getfloat('electrical', 'c')
        return result
            
    #--------------------------------------------------------------------------------------------------------------------
    # Returns true if the material is magnetically linear, i.e. either diamagnetic or paramagnetic, and false otherwise.

    def is_magnetically_linear(self) -> bool:
        return self.properties['magnetic']['type'].casefold() in ('diamagnetic', 'paramagnetic')
    
    #--------------------------------------------------------------------------------------------------------------------
    # Returns the material's magnetic susceptibility if it is dielectric.

    def magnetic_susceptibility(self) -> float:
        """WARNING: this will crash if the material is not linear!"""
        return self.properties.getfloat('magnetic', 'susceptibility')
    
    #--------------------------------------------------------------------------------------------------------------------
    # Returns the material's Jiles-Atherton parameters for modelling magnetization hysteresis, if it is ferromagnetic.
    
    def magnetic_JA_parameters(self) -> dict:
        result = dict()
        result['alpha'] = self.properties.getfloat('magnetic', 'alpha')
        result['a'] = self.properties.getfloat('magnetic', 'a')
        result['msat'] = self.properties.getfloat('magnetic', 'msat')
        result['k'] = self.properties.getfloat('magnetic', 'k')
        result['c'] = self.properties.getfloat('magnetic', 'c')
        return result
    
    #====================================================================================================================
    # Jiles-Atherton model implementation: calculates the resultant D/B fields in terms of phasors, given an applied E/H
    # field in terms of phasors. Since the behaviour is non-linear, it is important that the input fully describes the
    # entire applied field, and not just any single-frequency component; as such the input should be a list of phasors.
    # The output, accordingly, is a list of phasors (representing a range of harmonics over multiple frequencies), even
    # if the input was single-frequency.

    #--------------------------------------------------------------------------------------------------------------------
    # Uses the Jiles-Atherton model to calculate the resultant D field, given an applied E field. The output is a list of
    # phasors
    



