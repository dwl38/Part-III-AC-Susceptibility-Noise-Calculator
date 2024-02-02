#========================================================================================================================
# The CircuitElement abstract class is an interface, which allows other objects to generically be modelled as electrical
# circuit elements in the context of the Circuit class.
#
# All instances of the CircuitElement class are obliged to report whether or not they are Ohmic (i.e the voltage phasor
# is always equal to the current phasor times some well-defined frequency-dependent impedance), and if they are they are
# obliged to report this impedance; or if not they are obliged to report both the voltage-current curve, as well as the
# differential impedance at a given current.
#========================================================================================================================

from abc import ABC, abstractmethod

class CircuitElement(ABC):

    @abstractmethod
    def is_ohmic(self) -> bool:
        """Returns True if this CircuitElement is Ohmic, False otherwise."""
        pass

    @abstractmethod
    def get_impedance(self, ang_freq: float) -> complex:
        """Returns the impedance of this CircuitElement if it is Ohmic. Undefined otherwise.
        
        Parameters
        ----------
        ang_freq: The angular frequency for the AC current"""
        pass

    @abstractmethod
    def get_voltage(self, ang_freq: float, current: complex) -> complex:
        """Returns the AC voltage phasor of this CircuitElement given an AC current phasor, if it is non-Ohmic. This
        function should effectively describe the voltage-curret curve for this CircuitElement. It is undefined if the
        CircuitElement is Ohmic.
        
        Parameters
        ----------
        ang_freq: The angular frequency for the AC current
        current: The AC current phasor"""
        pass

    @abstractmethod
    def get_diff_impedance(self, ang_freq: float, current: complex) -> complex:
        """Returns the differential impedance of this CircuitElement given an AC current phasor, defined as the partial
        derivative of the voltage phasor against the current phasor, if it is non-Ohmic. This function is undefined if
        the CircuitElement is Ohmic.
        
        Parameters
        ----------
        ang_freq: The angular frequency for the AC current
        current: The AC current phasor"""
        pass