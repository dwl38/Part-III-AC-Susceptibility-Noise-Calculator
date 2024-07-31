#========================================================================================================================
# The GUIElement abstract class is an interface for GUI sub-menus, which specifically must:
# 
#   - generate its own graphics within a self-contained Tkinter widget (e.g. a frame), provided a parent;
#   - conform to Tkinter's .grid() geometry manager;
#   - be able to report the current values (with validation) to a "config" dict;
#   - be configurable using a "config" dict.
#========================================================================================================================

from abc import ABC, abstractmethod
from typing import Tuple

class GUIElement(ABC):

    @abstractmethod
    def grid(self, **kwargs) -> None:
        """Replicates the Tkinter .grid() geometry manager."""
        pass

    @abstractmethod
    def get_configuration(self, prev: dict = None) -> dict:
        """Returns the configuration dictionary of the input values in the sub-menu.
        
        Parameters
        ----------
        prev: (Optional) The 'previous' configuration dictionary; if specified, the output will be appended to prev with
              overlaps updated (modifying the original), otherwise the output contains only the values of this sub-menu."""
        pass

    @abstractmethod
    def set_configuration(self, config: dict) -> Tuple[int, str]:
        """Sets the input/output fields of this sub-menu to the values provided by the configuration dictionary. Returns
        the tuple (0, '') if all fields can be configured without issue; otherwise, returns 1 and a string describing the
        error, if there are missing or invalid values (which sets the fields to default values).
        
        Parameters
        ----------
        config: The configuration to set to."""
        pass

