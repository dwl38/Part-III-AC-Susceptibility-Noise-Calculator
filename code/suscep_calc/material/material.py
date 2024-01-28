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

import configparser
import numpy as np

#========================================================================================================================
# Class definition

class Material:

    #--------------------------------------------------------------------------------------------------------------------
    # Class constructor for a new Material. This constructor should not be used directly! See read_from_file instead.
    #
    #     - properties: A dict containing the properties of the material being defined.
    #
    
    def __init__(self, properties):
        
        self.__properties = configparser.ConfigParser()
        
        # Data type sanitization

        if isinstance(properties, (dict, configparser.ConfigParser)):
            if 'misc' in properties and isinstance(properties['misc'], (dict, configparser.SectionProxy)):
                self.__properties['misc'] = properties['misc']
            if 'conductivity' in properties and isinstance(properties['conductivity'], (dict, configparser.SectionProxy)):
                self.__properties['conductivity'] = properties['conductivity']
            if 'electrical' in properties and isinstance(properties['electrical'], (dict, configparser.SectionProxy)):
                self.__properties['electrical'] = properties['electrical']
            if 'magnetic' in properties and isinstance(properties['magnetic'], (dict, configparser.SectionProxy)):
                self.__properties['magnetic'] = properties['magnetic']

        # Check for missing values and implement default values if needed

        if 'misc' not in self.__properties:
            self.__properties['misc'] = dict()
        if 'name' not in self.__properties['misc']:
            self.__properties['misc']['name'] = 'Vacuum'
        if 'desc' not in self.__properties['misc']:
            self.__properties['misc']['desc'] = 'Classical vaccum'

        if 'conductivity' not in self.__properties:
            self.__properties['conductivity'] = dict()
        if 'ohmic' not in self.__properties['conductivity']:
            self.__properties['conductivity'] = {'ohmic': 'True', 'conductivity': '0.0'}
        else:
            if self.__properties['conductivity'].getboolean('ohmic'):
                if 'conductivity' not in self.__properties['conductivity']:
                    self.__properties['conductivity']['conductivity'] = '0.0'
            else:
                if 'curve' not in self.__properties['conductivity']:
                    self.__properties['conductivity']['curve'] = '[[0.0, 1.0], [0.0, 0.0]]'

        if 'electrical' not in self.__properties:
            self.__properties['electrical'] = dict()
        if 'type' not in self.__properties['electrical']:
            self.__properties['electrical'] = {'type': 'dielectric', 'susceptibility': '0.0'}
        else:
            if self.__properties['electrical']['type'].casefold() == 'dielectric':
                if 'susceptibility' not in self.__properties['electrical']:
                    self.__properties['electrical']['susceptibility'] = '0.0'
            elif self.__properties['electrical']['type'].casefold() == 'ferroelectric':
                if 'curve' not in self.__properties['electrical']:
                    self.__properties['electrical']['curve'] = '[[0.0, 1.0], [0.0, 0.0]]'
            else:
                self.__properties['electrical'] = {'type': 'dielectric', 'susceptibility': '0.0'}
                
        if 'magnetic' not in self.__properties:
            self.__properties['magnetic'] = dict()
        if 'type' not in self.__properties['magnetic']:
            self.__properties['magnetic'] = {'type': 'diamagnetic', 'susceptibility': '0.0'}
        else:
            if self.__properties['magnetic']['type'].casefold() in ('diamagnetic', 'paramagnetic'):
                if 'susceptibility' not in self.__properties['magnetic']:
                    self.__properties['magnetic']['susceptibility'] = '0.0'
            elif self.__properties['magnetic']['type'].casefold() in ('ferromagnetic', 'ferrimagnetic', 'antiferromagnetic'):
                if 'curve' not in self.__properties['magnetic']:
                    self.__properties['magnetic']['curve'] = '[[0.0, 1.0], [0.0, 0.0]]'
            else:
                self.__properties['magnetic'] = {'type': 'diamagnetic', 'susceptibility': '0.0'}
                
                
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
            self.__properties.write(configfile)

"""
    #--------------------------------------------------------------------------------------------------------------------
    # Returns the thermal conductivity of the material at a given temperature, using an interpolator for temperatures
    # falling between known datapoints of the material. This function is natively projectable to numpy arrays, although
    # be warned that the execution time is proportional to the array length!
    #
    #     - temp: Either a float representing the temperature, in K, to calculate the thermal conductivity for; or a
    #               numpy array containing a strictly-ascending range of temperatures, to calculate the thermal
    #               conductivities at. The output type matches the input type.
    #

    def getThermalKAtT(self, temp):
        try:
            t = float(temp)
            index = np.count_nonzero(self.__thermalK[0,:] < t)
            if index == 0:
                if self.type == 'metal':
                    return (self.__thermalK[1, 0] * (t / self.__thermalK[0, 0]))
                elif self.type == 'insulator':
                    return (self.__thermalK[1, 0] * ((t / self.__thermalK[0, 0])**3))
                else:
                    return self.__thermalK[1, 0]
            elif index == self.__thermalK.shape[1]:
                return self.__thermalK[1, -1]
            else:
                x = (t - self.__thermalK[0, index-1]) / (self.__thermalK[0, index] - self.__thermalK[0, index-1])
                y = self.__thermalK[1, index] - self.__thermalK[1, index-1]
                return (self.__thermalK[1, index-1] + (x * y))
        except TypeError:
            t = np.sort(np.array(temp, dtype=float).flatten())
            result = np.empty(t.shape[0], dtype=float)
            prefix = np.count_nonzero(t <= self.__thermalK[0, 0])
            if self.type == 'metal':
                for i in range(prefix):
                    result[i] = (self.__thermalK[1, 0] * (t[i] / self.__thermalK[0, 0]))
            elif self.type == 'insulator':
                for i in range(prefix):
                    result[i] = (self.__thermalK[1, 0] * ((t[i] / self.__thermalK[0, 0])**3))
            else:
                result[:prefix] = self.__thermalK[1, 0]
            postfix = np.count_nonzero(t >= self.__thermalK[0, -1])
            if postfix > 0:
                result[-postfix:] = self.__thermalK[1, -1]
            index_input = prefix
            index_search = 0
            while (index_input < len(t)) and (index_search < (self.__thermalK.shape[1] - 1)):
                var = t[index_input]
                left, right = self.__thermalK[0, index_search], self.__thermalK[0, index_search+1]
                if left < var and right < var:
                    index_search = index_search + 1
                elif left < var and right >= var:
                    x = (var - left) / (right - left)
                    y = self.__thermalK[1, index_search+1] - self.__thermalK[1, index_search]
                    result[index_input] = (self.__thermalK[1, index_search] + (x * y))
                    index_input = index_input + 1
                else:
                    raise RuntimeError('Interpolation failed (oops, you shouldn\'t see this!)')
            return result

    #--------------------------------------------------------------------------------------------------------------------
    # Returns the integral of the thermal conductivity of the material across a temperature range. This is the fastest
    # and also most numerically accurate way to perform this particular integral (being an integral over an interpolator
    # of known datapoints), as opposed to numerically integrating the results of getThermalKAtT(...).
    #
    #     - temp1: The lower bound to integrate from.
    #     - temp2: The upper bound to integrate to.
    #
    
    def integrateThermalKOverT(self, temp1, temp2):
        temp1, temp2 = float(temp1), float(temp2)
        if temp2 < temp1:
            return -self.integrateThermalKOverT(temp2, temp1)
        start_index = self.__thermalK[0].searchsorted(temp1)
        end_index = self.__thermalK[0].searchsorted(temp2) - 1
        if start_index == self.__thermalK.shape[0]:
            return (temp2 - temp1) * self.__thermalK[1, -1]
        if end_index == -1:
            if self.type == 'metal':
                grad = self.__thermalK[1, 0] / self.__thermalK[0, 0]
                return 0.5 * grad * ((temp2**2) - (temp1**2))
            elif self.type == 'insulator':
                grad = self.__thermalK[1, 0] / ((self.__thermalK[0, 0])**3)
                return 0.25 * grad * ((temp2**4) - (temp1**4))
            else:
                return (temp2 - temp1) * self.__thermalK[1, 0]
        result = 0.0
        if start_index == 0:
            if self.type == 'metal':
                grad = self.__thermalK[1, 0] / self.__thermalK[0, 0]
                result += 0.5 * grad * (((self.__thermalK[0, 0])**2) - (temp1**2))
            elif self.type == 'insulator':
                grad = self.__thermalK[1, 0] / ((self.__thermalK[0, 0])**3)
                result += 0.25 * grad * (((self.__thermalK[0, 0])**4) - (temp1**4))
            else:
                result += (self.__thermalK[0, 0] - temp1) * self.__thermalK[1, 0]
        else:
            x = (temp1 - self.__thermalK[0, start_index-1]) / (self.__thermalK[0, start_index] - self.__thermalK[0, start_index-1])
            y = self.__thermalK[1, start_index] - self.__thermalK[1, start_index-1]
            point = self.__thermalK[1, start_index-1] + (x * y)
            result += 0.5 * (point + self.__thermalK[1, start_index]) * (self.__thermalK[0, start_index] - temp1)
        if end_index == self.__thermalK.shape[0] - 1:
            result += (temp2 - self.__thermalK[0, -1]) * self.__thermalK[1, -1]
        else:
            x = (temp2 - self.__thermalK[0, end_index]) / (self.__thermalK[0, end_index+1] - self.__thermalK[0, end_index])
            y = self.__thermalK[1, end_index+1] - self.__thermalK[1, end_index]
            point = self.__thermalK[1, end_index] + (x * y)
            result += 0.5 * (point + self.__thermalK[1, end_index]) * (temp2 - self.__thermalK[0, end_index])
        for i in range(start_index, end_index, 1):
            result += 0.5 * (self.__thermalK[1, i] + self.__thermalK[1, i+1]) * (self.__thermalK[0, i+1] - self.__thermalK[0, i])
        return result

    #--------------------------------------------------------------------------------------------------------------------
    # Returns the electrical conductivity of the material at a given temperature, using an interpolator for temperatures
    # falling between known datapoints of the material. This function is natively projectable to numpy arrays, although
    # be warned that the execution time is proportional to the array length!
    #
    #     - temp: Either a float representing the temperature, in K, to calculate the electrical conductivity for; or a
    #               numpy array containing a strictly-ascending range of temperatures, to calculate the electrical
    #               conductivities at. The output type matches the input type.
    #
    
    def getElectricKAtT(self, temp):
        try:
            t = float(temp)
            index = np.count_nonzero(self.__electricK[0,:] < t)
            if index == 0:
                return self.__electricK[1, 0]
            elif index == self.__electricK.shape[1]:
                return self.__electricK[1, -1]
            else:
                x = (t - self.__electricK[0, index-1]) / (self.__electricK[0, index] - self.__electricK[0, index-1])
                y = self.__electricK[1, index] - self.__electricK[1, index-1]
                return (self.__electricK[1, index-1] + (x * y))
        except TypeError:
            t = np.sort(np.array(temp, dtype=float).flatten())
            result = np.empty(t.shape[0], dtype=float)
            prefix = np.count_nonzero(t <= self.__electricK[0, 0])
            result[:prefix] = self.__electricK[1, 0]
            postfix = np.count_nonzero(t >= self.__electricK[0, -1])
            if postfix > 0:
                result[-postfix:] = self.__electricK[1, -1]
            index_input = prefix
            index_search = 0
            while (index_input < len(t)) and (index_search < (self.__electricK.shape[1] - 1)):
                var = t[index_input]
                left, right = self.__electricK[0, index_search], self.__electricK[0, index_search+1]
                if left < var and right < var:
                    index_search = index_search + 1
                elif left < var and right >= var:
                    x = (var - left) / (right - left)
                    y = self.__electricK[1, index_search+1] - self.__electricK[1, index_search]
                    result[index_input] = (self.__electricK[1, index_search] + (x * y))
                    index_input = index_input + 1
                else:
                    raise RuntimeError('Interpolation failed (oops, you shouldn\'t see this!)')
            return result

"""

