#========================================================================================================================
# This file is for the GUI's visualizer, which displays an axial cross-section of the system's various cylinders as
# rectangles for easy visualization.
#========================================================================================================================

from typing import Tuple
from types import MethodType
from .gui_element import GUIElement
from .. import *
import tkinter as tk
import tkinter.ttk as ttk

#========================================================================================================================
# Class definition

class Visualizer(GUIElement):

    #--------------------------------------------------------------------------------------------------------------------
    # Class constructor. The parameters are as follows:
    #
    #     - parent: A Tkinter widget (e.g. frame) which serves as the parent of this sub-menu.
    #
    # Note that the Visualizer will not work until "activated" using the activate() method!
    #

    def __init__(self, parent):
        
        self.frame = ttk.LabelFrame(parent, text='Visualizer', padding=10)

        # TODO: there may be a way to do 'smart' sizing instead of predefined window size...
        self.display_width = 250
        self.display_height = 400

        self.canvas = tk.Canvas(self.frame, bg='#fff', width=self.display_width, height=self.display_height)
        self.canvas.grid(column=0, row=0)

        self.button = ttk.Button(self.frame, text='Update')
        self.button.grid(column=0, row=1, padx=5, pady=5, sticky=tk.S)
        

    #--------------------------------------------------------------------------------------------------------------------
    # The activate() method assigns the visualization routine to the GUI's button, allowing the user to interact with it.
    # It also constructs and exposes the update_display() method (which otherwise would not exist), allowing other
    # routines to update this Visualizer. The parameters are as follows:
    #
    #     - get_current_parameters: A function, of call signature (None)->(dict), which returns the current configuration
    #                               of the simulation parameters.
    #

    def activate(self, get_current_parameters) -> None:

        # Build a new function...
        def update_display(self):
    
            # Find all of the physical parameters (standardized to units of meters)
            config = get_current_parameters()

            sample_r = Q_(float(config['sample_radius']), config['sample_radius_units']).to('m').magnitude
            sample_l = Q_(float(config['sample_length']), config['sample_length_units']).to('m').magnitude
            sample_z = Q_(float(config['sample_offset']), config['sample_offset_units']).to('m').magnitude
            sample_z1 = sample_z - (sample_l/2)
            sample_z2 = sample_z + (sample_l/2)
    
            samplecoil_r = Q_(float(config['samplecoil_radius']), config['samplecoil_radius_units']).to('m').magnitude
            samplecoil_l = Q_(float(config['samplecoil_length']), config['samplecoil_length_units']).to('m').magnitude
            samplecoil_z = Q_(float(config['samplecoil_offset']), config['samplecoil_offset_units']).to('m').magnitude
            samplecoil_z1 = samplecoil_z - (samplecoil_l/2)
            samplecoil_z2 = samplecoil_z + (samplecoil_l/2)
    
            refcoil_r = Q_(float(config['refcoil_radius']), config['refcoil_radius_units']).to('m').magnitude
            refcoil_l = Q_(float(config['refcoil_length']), config['refcoil_length_units']).to('m').magnitude
            refcoil_z = Q_(float(config['refcoil_offset']), config['refcoil_offset_units']).to('m').magnitude
            refcoil_z1 = refcoil_z - (refcoil_l/2)
            refcoil_z2 = refcoil_z + (refcoil_l/2)
    
            drivecoil_r = Q_(float(config['drivecoil_radius']), config['drivecoil_radius_units']).to('m').magnitude
            drivecoil_l = Q_(float(config['drivecoil_length']), config['drivecoil_length_units']).to('m').magnitude
            drivecoil_z1 = -(drivecoil_l/2)
            drivecoil_z2 = (drivecoil_l/2)

            system_r = max(sample_r, samplecoil_r, refcoil_r, drivecoil_r)      # Largest r coordinate to draw
            system_z1 = min(sample_z1, samplecoil_z1, refcoil_z1, drivecoil_z1) # Most negative z coordinate to draw
            system_z2 = max(sample_z2, samplecoil_z2, refcoil_z2, drivecoil_z2) # Most positive z coordinate to draw

            if (system_r == 0.0) or (system_z1 == system_z2):                   # Abort routine early if system size is zero
                return None

            # Calculate scaling factor for nice display (with 5% margins on each side of the display)
            scale_r = self.display_width / (2.4 * system_r)
            scale_z = self.display_height / (1.1 * (system_z2 - system_z1))
            offset_r = self.display_width / 2
            offset_z = (self.display_height / 2) + (scale_z * ((system_z2 + system_z1) / 2))

            # Reset display
            self.canvas.delete('resettable') # Deletes all objects on the canvas with the "resettable" tag

            # Draw items onto screen
            self.canvas.create_rectangle(offset_r - (scale_r * drivecoil_r), offset_z - (scale_z * drivecoil_z1),
                                         offset_r + (scale_r * drivecoil_r), offset_z - (scale_z * drivecoil_z2),
                                         width=0, fill='#ccc', tags='resettable')
            self.canvas.create_rectangle(offset_r - (scale_r * refcoil_r), offset_z - (scale_z * refcoil_z1),
                                         offset_r + (scale_r * refcoil_r), offset_z - (scale_z * refcoil_z2),
                                         width=0, fill='#090', tags='resettable')
            self.canvas.create_rectangle(offset_r - (scale_r * samplecoil_r), offset_z - (scale_z * samplecoil_z1),
                                         offset_r + (scale_r * samplecoil_r), offset_z - (scale_z * samplecoil_z2),
                                         width=0, fill='#b00', tags='resettable')
            self.canvas.create_rectangle(offset_r - (scale_r * sample_r), offset_z - (scale_z * sample_z1),
                                         offset_r + (scale_r * sample_r), offset_z - (scale_z * sample_z2),
                                         width=0, fill='#99b', stipple='gray75', tags='resettable')


        # ...and load that new function into a method for this Visualizer instance
        method = MethodType(update_display, self)
        setattr(self, 'update_display', method)

        # Set the action of the button to the newly-created method
        self.button.configure(command=self.update_display)


    #--------------------------------------------------------------------------------------------------------------------
    # Satisfying GUIElement inheritance requirements

    def grid(self, **kwargs) -> None:
        self.frame.grid(**kwargs)
        
    #--------------------

    def get_configuration(self, prev: dict = None) -> dict:
        if prev is None:
            return dict()
        else:
            return prev
        
    #--------------------

    def set_configuration(self, config: dict) -> Tuple[int, str]:
        return (0, '')

