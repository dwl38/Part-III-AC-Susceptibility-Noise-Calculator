#========================================================================================================================
# The Circuit class is a simplified model of a single-loop electrical circuit, with a voltage source and some number of
# CircuitElements attached in series to the voltage source. It is designed to inherently work with AC phasors, but DC
# behaviour is easily obtained by setting frequency to zero.
#========================================================================================================================

from .circuit_element import CircuitElement

#========================================================================================================================
# Class definition

class Circuit:

    #--------------------------------------------------------------------------------------------------------------------
    # Class constructor for a new Circuit. Input parameter can be blank, or an initial list of CircuitElements.

    def __init__(self, elements: list[CircuitElement] = None):
        
        self.ohmic_elements = list()
        self.nonohmic_elements = list()

        if elements is not None:
            for element in elements:
                if element.is_ohmic():
                    self.ohmic_elements.append(element)
                else:
                    self.nonohmic_elements.append(element)
   
    #--------------------------------------------------------------------------------------------------------------------
    # Adds a CircuitElement to this circuit.

    def add_element(self, element: CircuitElement) -> None:
        if element.is_ohmic():
            self.ohmic_elements.append(element)
        else:
            self.nonohmic_elements.append(element)

    #--------------------------------------------------------------------------------------------------------------------
    # Check that this circuit is linear, i.e. all elements are Ohmic.

    def is_ohmic(self) -> bool:
        return len(self.nonohmic_elements) == 0

    #--------------------------------------------------------------------------------------------------------------------
    # Calculates the AC current phasor for the circuit, given an ideal voltage input (specified by an AC phasor).
    #
    #     - ang_freq: The angular frequency for the AC voltage; set to 0 for DC
    #     - voltage:  The AC voltage phasor
    #

    def calculate_current(self, ang_freq: float, voltage: complex) -> complex:

        # Calculate the total impedance contributed by all of the Ohmic components
        total_impedance = complex(0.0)
        for element in self.ohmic_elements:
            total_impedance += element.get_impedance(ang_freq)

        # If there are no non-Ohmic elements, the calculation is simple
        if len(self.nonohmic_elements) == 0:
            return voltage / total_impedance
        
        # Otherwise, we have to solve via Newton-Raphson iteration:

        EPSILON = 1.0E-4                                                         # Accuracy goal is 0.01%
        MAX_ITER = 10000000                                                      # Max no. of iterations
        guess = (0.0 if total_impedance == 0.0 else (voltage / total_impedance)) # Initial guess
        delta = abs(guess) + 1.0                                                 # Will be used to store changes
        i = 0                                                                    # To keep track of no. of iterations

        while (delta > EPSILON * abs(guess)) and i < MAX_ITER:          # Run until within accuracy goal or MAX_ITER
            value = total_impedance * guess - voltage                   # Calculate Ohmic part of f(x)
            gradient = total_impedance                                  # Calculate Ohmic part of f'(x)
            for element in self.nonohmic_elements:                      # For each non-Ohmic element...
                value += element.get_voltage(ang_freq, guess)           # ...add contribution to f(x)
                gradient += element.get_diff_impedance(ang_freq, guess) # ...add contribution to f'(x)
            if gradient == 0.0:                                         # Prevent division by zero...
                gradient += EPSILON                                     # ...by a random amount if needed
            guess -= value / gradient                                   # Newton-Raphson method: x = x - f(x)/f'(x)
            delta = abs(value / (gradient * guess))                     # Calculate change induced by previous step
            i += 1                                                      # Advance iterator

        return guess

