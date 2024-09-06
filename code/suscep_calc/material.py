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
        else:
            if self.properties.getboolean('conductivity', 'ohmic'):
                if 'conductivity' not in self.properties['conductivity']:
                    self.properties['conductivity']['conductivity'] = '0.0'
            else:
                if 'curve' not in self.properties['conductivity']:
                    self.conductivity_curve = np.array([[0, 1], [0, 0]], dtype=float)
                else:
                    self.conductivity_curve = np.array(json.loads(self.properties['conductivity']['curve']), dtype=float)

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
        """WARNING: this method will raise a NoSectionError if the material is not Ohmic!"""
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
        """WARNING: this method will raise a NoSectionError if the material is not dielectric!"""
        return self.properties.getfloat('electrical', 'susceptibility')
    
    #--------------------------------------------------------------------------------------------------------------------
    # Returns the material's Jiles-Atherton parameters for modelling polarization hysteresis, if it is ferroelectric.

    def electrical_JA_parameters(self) -> dict:
        """WARNING: this method will raise a NoSectionError if the material is dielectric!"""
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
        """WARNING: this method will raise a NoSectionError if the material is not linear!"""
        return self.properties.getfloat('magnetic', 'susceptibility')
    
    #--------------------------------------------------------------------------------------------------------------------
    # Returns the material's Jiles-Atherton parameters for modelling magnetization hysteresis, if it is ferromagnetic.
    
    def magnetic_JA_parameters(self) -> dict:
        """WARNING: this method will raise a NoSectionError if the material is linear!"""
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
    # Uses the Jiles-Atherton model to calculate the resultant D field, given an applied E field with a finite number of
    # single-frequency AC components. The output is a list of ordered pairs for each frequency component, with each pair
    # containing the D field phasor and corresponding angular frequency.
    #
    #     - E_field_phasors:  A list, or otherwise Iterable, of ordered pairs (E_n, omega_n) where E_n is the nth phasor
    #                           corresponding to angular frequency omega_n, representing the applied E field in terms of
    #                           a sum of single-frequency components. Use omega_n = 0 to add a DC component.
    #     - N_time:           (int) Number of time points to divide the calculation into. This also controls the output,
    #                           as only the first N_time lowest-order frequency components (including the DC component)
    #                           will be calculated.
    #
    
    def calculate_D_field_from_E_field(self, E_field_phasors: list[tuple[complex, float]], N_time: int) -> list[tuple[complex, float]]:

        result = list()

        if N_time < len(E_field_phasors) + 1:
            raise ValueError('N_time must be at least one greater than the number of input components!')

        # If this material is linear, we can completely skip all calculations
        if self.is_dielectric():
            permittivity = VACUUM_PERMITTIVITY_SI * (1.0 + self.electrical_susceptibility())
            for E_field_phasor in E_field_phasors:
                result.append((permittivity * E_field_phasor[0], E_field_phasor[1]))
            return result

        # Calculate the frequencies of lowest-order harmonics that can possibly appear in the signal
        target_frequencies = [0.0,]
        step = 1
        input_frequencies = [E_field_phasor[1] for E_field_phasor in E_field_phasors if E_field_phasor[1] > 0.0]
        n_inputs = len(input_frequencies)
        while len(target_frequencies) < N_time:
            index = [-step,] * n_inputs
            for i in range((2*step + 1)**n_inputs):
                for j in range(n_inputs):
                    if index[j] > step:
                        index[j] = -step
                        index[j+1] = index[j+1] + 1
                possible_frequency = 0.0
                for j in range(n_inputs):
                    possible_frequency += input_frequencies[j] * index[j]
                if possible_frequency > 0.0 and possible_frequency not in target_frequencies:
                    target_frequencies.append(possible_frequency)
                index[0] = index[0] + 1
            step = step + 1
        target_frequencies.sort()
        if len(target_frequencies) > N_time:
            target_frequencies = target_frequencies[0:N_time]

        # Find geometric mean of the periods of the AC components
        mean_period = 1.0
        for freq in input_frequencies:
            mean_period = mean_period * freq
        mean_period = np.float_power(mean_period, (1.0/n_inputs))

        # The 'infinitesimal' time step for time-domain simulation is selected so that the mean period lies geometrically
        # halfway between dt and Ndt (this ensures that dt is "as small as possible" while Ndt is "as large as possible")
        DT = mean_period / np.sqrt(N_time)

        # Procedure is different if calculating scalar field vs vector field; either way, calculate E field and then D
        # field in time domain using Jiles-Atherton model
        if is_vector(E_field_phasors[0, 0]):
            n_dims = len(E_field_phasors[0, 0])
            D_field = np.array((N_time, n_dims), dtype=float)
            for dim in range(n_dims):
                E_field = np.zeros((N_time), dtype=float)
                for phasor in E_field_phasors:
                    exponentials = np.array([np.exp(-1j * phasor[1] * t * DT) for t in range(N_time)])
                    E_field += np.real(phasor[0, dim] * exponentials)
                D_field[:, dim] = self.__D_field_from_E_field_time_domain(E_field, N_time)
        else:
            E_field = np.zeros((N_time), dtype=float)
            for phasor in E_field_phasors:
                exponentials = np.array([np.exp(-1j * phasor[1] * t * DT) for t in range(N_time)])
                E_field += np.real(phasor[0] * exponentials)
            D_field = self.__D_field_from_E_field_time_domain(E_field, N_time)

        # Calculate phasor of D field corresponding to each target frequency
        for freq in target_frequencies:
            exponentials = np.array([np.exp(1j * freq * t * DT) for t in range(N_time)], dtype=complex)
            coefficient = (1.0 / N_time) * np.tensordot(exponentials, D_field)
            result.append((coefficient, freq))

        return result
    
    #--------------------------------------------------------------------------------------------------------------------
    # "Secret" internal function for calculate_D_field_from_E_field(), as a direct implementation of the Jiles-Atherton
    # model for scalar fields; takes in a scalar E field as a time-domain function, and returns the scalar D field also
    # in the time-domain.

    def __D_field_from_E_field_time_domain(self, E_field, N_time):

        # Collect Jiles-Atherton parameters
        alpha = self.properties.getfloat('electrical', 'alpha')
        a = self.properties.getfloat('electrical', 'a')
        psat = self.properties.getfloat('electrical', 'psat')
        k = self.properties.getfloat('electrical', 'k')
        c = self.properties.getfloat('electrical', 'c')

        # Calculate P field as a function of time, using Jiles-Atherton model
        P_field = np.zeros((N_time), dtype=float)
        E_eff = (E_field[0] + (alpha * P_field[0])) / a
        P_field[0] = psat * (np.power(np.tanh(E_eff), -1.0) - np.power(E_eff, -1.0)) * (c / (1.0 + c))
        P_hys = 0.0
        for t in range(1, N_time):
            E_eff = (E_field[t] + (alpha * P_field[t-1])) / a
            P_an = psat * (np.power(np.tanh(E_eff), -1.0) - np.power(E_eff, -1.0))
            delta_E = E_field[t] - E_field[t-1]
            P_diff = P_an - P_field[t-1]
            delta_P_hys = delta_E * P_diff / ((k * np.sign(delta_E)) - (alpha * P_diff))
            P_hys += delta_P_hys
            P_field[t] = (P_hys + (c * P_an)) / (1.0 + c)

        # D field is E field plus P field
        return ((VACUUM_PERMITTIVITY_SI * E_field) + P_field)
    
    #--------------------------------------------------------------------------------------------------------------------
    # Uses the Jiles-Atherton model to calculate the resultant B field, given an applied H field with a finite number of
    # single-frequency AC components. The output is a list of ordered pairs for each frequency component, with each pair
    # containing the D field phasor and corresponding angular frequency.
    #
    #     - H_field_phasors:  A list, or otherwise Iterable, of ordered pairs (H_n, omega_n) where H_n is the nth phasor
    #                           corresponding to angular frequency omega_n, representing the applied H field in terms of
    #                           a sum of single-frequency components. Use omega_n = 0 to add a DC component.
    #     - N_time:           (int) Number of time points to divide the calculation into. This also controls the output,
    #                           as only the first N_time lowest-order frequency components (including the DC component)
    #                           will be calculated.
    #
    
    def calculate_B_field_from_H_field(self, H_field_phasors: list[tuple[complex, float]], N_time: int) -> list[tuple[complex, float]]:

        result = list()

        if N_time < len(H_field_phasors) + 1:
            raise ValueError('N_time must be at least one greater than the number of input components!')

        # If this material is linear, we can completely skip all calculations
        if self.is_magnetically_linear():
            permeability = VACUUM_PERMEABILITY_SI * (1.0 + self.magnetic_susceptibility())
            for H_field_phasor in H_field_phasors:
                result.append((permeability * H_field_phasor[0], H_field_phasor[1]))
            return result

        # Calculate the frequencies of lowest-order harmonics that can possibly appear in the signal
        target_frequencies = [0.0,]
        step = 1
        input_frequencies = [H_field_phasor[1] for H_field_phasor in H_field_phasors if H_field_phasor[1] > 0.0]
        n_inputs = len(input_frequencies)
        while len(target_frequencies) < N_time:
            index = [-step,] * n_inputs
            for i in range((2*step + 1)**n_inputs):
                for j in range(n_inputs):
                    if index[j] > step:
                        index[j] = -step
                        index[j+1] = index[j+1] + 1
                possible_frequency = 0.0
                for j in range(n_inputs):
                    possible_frequency += input_frequencies[j] * index[j]
                if possible_frequency > 0.0 and possible_frequency not in target_frequencies:
                    target_frequencies.append(possible_frequency)
                index[0] = index[0] + 1
            step = step + 1
        target_frequencies.sort()
        if len(target_frequencies) > N_time:
            target_frequencies = target_frequencies[0:N_time]

        # Find geometric mean of the periods of the AC components
        mean_period = 1.0
        for freq in input_frequencies:
            mean_period = mean_period * freq
        mean_period = np.float_power(mean_period, (1.0/n_inputs))

        # The 'infinitesimal' time step for time-domain simulation is selected so that the mean period lies geometrically
        # halfway between dt and Ndt (this ensures that dt is "as small as possible" while Ndt is "as large as possible")
        DT = mean_period / np.sqrt(N_time)

        # Procedure is different if calculating scalar field vs vector field; either way, calculate H field and then B
        # field in time domain using Jiles-Atherton model
        if is_vector(H_field_phasors[0, 0]):
            n_dims = len(H_field_phasors[0, 0])
            B_field = np.array((N_time, n_dims), dtype=float)
            for dim in range(n_dims):
                H_field = np.zeros((N_time), dtype=float)
                for phasor in H_field_phasors:
                    exponentials = np.array([np.exp(-1j * phasor[1] * t * DT) for t in range(N_time)])
                    H_field += np.real(phasor[0, dim] * exponentials)
                B_field[:, dim] = self.__B_field_from_H_field_time_domain(H_field, N_time)
        else:
            H_field = np.zeros((N_time), dtype=float)
            for phasor in H_field_phasors:
                exponentials = np.array([np.exp(-1j * phasor[1] * t * DT) for t in range(N_time)])
                H_field += np.real(phasor[0] * exponentials)
            B_field = self.__B_field_from_H_field_time_domain(H_field, N_time)

        # Calculate phasor of B field corresponding to each target frequency
        for freq in target_frequencies:
            exponentials = np.array([np.exp(1j * freq * t * DT) for t in range(N_time)], dtype=complex)
            coefficient = (1.0 / N_time) * np.tensordot(exponentials, B_field)
            result.append((coefficient, freq))

        return result

    #--------------------------------------------------------------------------------------------------------------------
    # "Secret" internal function for calculate_B_field_from_H_field(), as a direct implementation of the Jiles-Atherton
    # model for scalar fields; takes in a scalar H field as a time-domain function, and returns the scalar B field also
    # in the time-domain.

    def __B_field_from_H_field_time_domain(self, H_field, N_time):

        # Collect Jiles-Atherton parameters
        alpha = self.properties.getfloat('magnetic', 'alpha')
        a = self.properties.getfloat('magnetic', 'a')
        msat = self.properties.getfloat('magnetic', 'msat')
        k = self.properties.getfloat('magnetic', 'k')
        c = self.properties.getfloat('magnetic', 'c')

        # Calculate P field as a function of time, using Jiles-Atherton model
        M_field = np.zeros((N_time), dtype=float)
        H_eff = (H_field[0] + (alpha * M_field[0])) / a
        M_field[0] = msat * (np.power(np.tanh(H_eff), -1.0) - np.power(H_eff, -1.0)) * (c / (1.0 + c))
        M_hys = 0.0
        for t in range(1, N_time):
            H_eff = (H_field[t] + (alpha * M_field[t-1])) / a
            M_an = msat * (np.power(np.tanh(H_eff), -1.0) - np.power(H_eff, -1.0))
            delta_H = H_field[t] - H_field[t-1]
            M_diff = M_an - M_field[t-1]
            delta_M_hys = delta_H * M_diff / ((k * np.sign(delta_H)) - (alpha * M_diff))
            M_hys += delta_M_hys
            M_field[t] = (M_hys + (c * M_an)) / (1.0 + c)

        # B field is H field plus M field
        return (VACUUM_PERMEABILITY_SI * (H_field + M_field))



