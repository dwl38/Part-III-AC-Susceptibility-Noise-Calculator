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
#     name*: (str) Material name
#     desc*: (str) Material description
#
# [Section 'conductivity']:
#     ohmic*:       (bool) Whether the material is Ohmic or has a nonlinear response
#     conductivity: (float) The conductivity for an isotropic & Ohmic material
#     curve:        (NDArray) A list of current densities against electric field strengths, as non-negative scalars,
#                   specifying the response curve for an isotropic & nonlinear material
#
# [Section 'electrical']:
#     type*:          (str) Is either 'dielectric' or 'ferroelectric'; NOTE THAT FERROELECTRICS ARE NOT IMPLEMENTED YET
#     susceptibility: (float) The dimensionless electrostatic susceptibility for an isotropic & dielectric material
#     curve:          (NDArray) A list of polarizations against electric field strengths, as scalars, specifying the
#                     hysteresis curve for an isotropic & ferroelectric material; THIS IS NOT IMPLEMENTED YET
#
# [Section 'magnetic']:
#     type*:          (str) Is either 'diamagnetic' or 'ferromagnetic'; in this context 'paramagnetic' is equivalent to
#                     'diamagnetic' since the response is identically linear, and 'ferrimagnetic' or 'antiferromagnetic'
#                     are equivalent to 'ferromagnetic' since the response curve is implemented generally; NOTE THAT
#                     FERROMAGNETICS ARE NOT IMPLEMENTED YET
#     susceptibility: (float) The dimensionless magnetostatic susceptibility for an isotropic & diamagnetic material
#     curve:          (NDArray) A list of magnetizations against H field strengths, as scalars, specifying the hysteresis
#                     curve for an isotropic & ferroelectric material; THIS IS NOT IMPLEMENTED YET
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
        else:
            if self.properties['conductivity'].getboolean('ohmic'):
                if 'conductivity' not in self.properties['conductivity']:
                    self.properties['conductivity']['conductivity'] = '0.0'
            else:
                if 'curve' not in self.properties['conductivity']:
                    self.properties['conductivity']['curve'] = '[[0.0, 1.0], [0.0, 0.0]]'

        if 'electrical' not in self.properties:
            self.properties['electrical'] = dict()
        if 'type' not in self.properties['electrical']:
            self.properties['electrical'] = {'type': 'dielectric', 'susceptibility': '0.0'}
        else:
            if self.properties['electrical']['type'].casefold() == 'dielectric':
                if 'susceptibility' not in self.properties['electrical']:
                    self.properties['electrical']['susceptibility'] = '0.0'
            elif self.properties['electrical']['type'].casefold() == 'ferroelectric':
                if 'curve' not in self.properties['electrical']:
                    self.properties['electrical']['curve'] = '[[0.0, 1.0], [0.0, 0.0]]'
            else:
                self.properties['electrical'] = {'type': 'dielectric', 'susceptibility': '0.0'}
                
        if 'magnetic' not in self.properties:
            self.properties['magnetic'] = dict()
        if 'type' not in self.properties['magnetic']:
            self.properties['magnetic'] = {'type': 'diamagnetic', 'susceptibility': '0.0'}
        else:
            if self.properties['magnetic']['type'].casefold() in ('diamagnetic', 'paramagnetic'):
                if 'susceptibility' not in self.properties['magnetic']:
                    self.properties['magnetic']['susceptibility'] = '0.0'
            elif self.properties['magnetic']['type'].casefold() in ('ferromagnetic', 'ferrimagnetic', 'antiferromagnetic'):
                if 'curve' not in self.properties['magnetic']:
                    self.properties['magnetic']['curve'] = '[[0.0, 1.0], [0.0, 0.0]]'
            else:
                self.properties['magnetic'] = {'type': 'diamagnetic', 'susceptibility': '0.0'}
                
        # Construct class members as NDArrays only if needed
        if not self.properties['conductivity'].getboolean('ohmic'):
            self.conductivity_curve = np.array(json.loads(self.properties['conductivity']['curve']))
        if self.properties['electrical']['type'].casefold() == 'ferroelectric':
            self.electrical_curve = np.array(json.loads(self.properties['electrical']['curve']))
        if self.properties['magnetic']['type'].casefold() in ('ferromagnetic', 'ferrimagnetic', 'antiferromagnetic'):
            self.magnetic_curve = np.array(json.loads(self.properties['magnetic']['curve']))
                
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

    #--------------------------------------------------------------------------------------------------------------------
    # Various specific (and type-sanitized) retrivals of properties.

    def is_ohmic(self) -> bool:
        return self.properties.getboolean('conductivity', 'ohmic')

    def conductivity(self) -> float:
        """WARNING: this will crash if the material is not Ohmic! Use current_at_field() for general safety."""
        return self.properties.getfloat('conductivity', 'conductivity')

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

    def is_dielectric(self) -> bool:
        return self.properties['electrical']['type'].casefold() == 'dielectric'
    
    def electrical_susceptibility(self) -> float:
        """WARNING: this will crash if the material is not dielectric! Use polarization_at_field() for general safety."""
        return self.properties.getfloat('electrical', 'susceptibility')
    
    def polarization_at_field(self, E_field):
        if self.properties['electrical']['type'].casefold() == 'dielectric':
            return self.properties.getfloat('electrical', 'susceptibility') * E_field
        else:
            if is_np_vector(E_field):
                # TODO: this currently only takes the positive side (i.e. globally stable solution) of the hysteresis curve.
                # Will need 'past' value of P_field to account for hysteresis!
                E_field_magnitude = np.linalg.norm(E_field)
                P_field_magnitude = np.interp(E_field_magnitude, self.electrical_curve[0], self.electrical_curve[1])
                return (P_field_magnitude / E_field_magnitude) * E_field
            else:
                return np.interp(float(E_field), self.electrical_curve[0], self.electrical_curve[1])
            
    def is_magnetically_linear(self) -> bool:
        return self.properties['magnetic']['type'].casefold() in ('diamagnetic', 'paramagnetic')
    
    def magnetic_susceptibility(self) -> float:
        """WARNING: this will crash if the material is not linear! Use magnetization_at_field() for general safety."""
        return self.properties.getfloat('magnetic', 'susceptibility')
    
    def magnetization_at_field(self, H_field):
        if self.properties['magnetic']['type'].casefold() in ('diamagnetic', 'paramagnetic'):
            return self.properties.getfloat('magnetic', 'susceptibility') * H_field
        else:
            if is_np_vector(H_field):
                # TODO: this currently only takes the positive side (i.e. globally stable solution) of the hysteresis curve.
                # Will need 'past' value of M_field to account for hysteresis!
                H_field_magnitude = np.linalg.norm(H_field)
                M_field_magnitude = np.interp(H_field_magnitude, self.magnetic_curve[0], self.magnetic_curve[1])
                return (M_field_magnitude / H_field_magnitude) * H_field
            else:
                return np.interp(float(H_field), self.magnetic_curve[0], self.magnetic_curve[1])



