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
        pass

    @abstractmethod
    def get_impedance(self, ang_freq: float) -> complex:
        pass

    @abstractmethod
    def get_voltage(self, ang_freq: float, current: complex) -> complex:
        pass

    @abstractmethod
    def get_diff_impedance(self, ang_freq: float, current: complex) -> complex:
        pass