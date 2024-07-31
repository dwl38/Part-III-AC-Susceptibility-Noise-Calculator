#========================================================================================================================
# The 'gui' folder contains all of the sub-modules required to display interactive sub-menus in the program main GUI, so
# that the user may input simulation values.
#========================================================================================================================


#------------------------------------------------------------------------------------------------------------------------
# Import shortcuts

from .gui_element import GUIElement

from .drivecoil import Drivecoil
from .samplecoil import Samplecoil
from .refcoil import Refcoil
from .sample import Sample
from .visualizer import Visualizer
from .calculation import CalculationSubmenu
from .fileio import FileIO


