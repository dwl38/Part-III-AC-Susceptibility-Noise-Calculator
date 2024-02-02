#========================================================================================================================
# This module contains a few implementations of extremely simple CircuitElements, namely ideal resistors, inductors, and
# capacitors.
#========================================================================================================================

from .circuit_element import CircuitElement

#------------------------------------------------------------------------------------------------------------------------
# A simple ideal resistor

class Resistor(CircuitElement):

    def __init__(self, resistance: float):
        self.resistance = resistance

    def is_ohmic(self) -> bool:
        return True

    def get_impedance(self, ang_freq: float) -> complex:
        return self.resistance

    def get_voltage(self, ang_freq: float, current: complex) -> complex:
        pass

    def get_diff_impedance(self, ang_freq: float, current: complex) -> complex:
        pass
    
#------------------------------------------------------------------------------------------------------------------------
# A simple ideal inductor

class Inductor(CircuitElement):

    def __init__(self, inductance: float):
        self.inductance = inductance

    def is_ohmic(self) -> bool:
        return True

    def get_impedance(self, ang_freq: float) -> complex:
        return (1j * ang_freq * self.inductance)

    def get_voltage(self, ang_freq: float, current: complex) -> complex:
        pass

    def get_diff_impedance(self, ang_freq: float, current: complex) -> complex:
        pass
    
#------------------------------------------------------------------------------------------------------------------------
# A simple ideal capacitor

class Capacitor(CircuitElement):

    def __init__(self, capacitance: float):
        self.capacitance = capacitance

    def is_ohmic(self) -> bool:
        return True

    def get_impedance(self, ang_freq: float) -> complex:
        return (-1j) / (ang_freq * self.capacitance)

    def get_voltage(self, ang_freq: float, current: complex) -> complex:
        pass

    def get_diff_impedance(self, ang_freq: float, current: complex) -> complex:
        pass
    