#========================================================================================================================
# This file is for the sub-menu for saving/loading simulation parameters.
#========================================================================================================================

from typing import Tuple
from .gui_element import GUIElement
from .. import *
import os
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog
import tkinter.messagebox

import configparser

#========================================================================================================================
# Class definition

class FileIO(GUIElement):

    #--------------------------------------------------------------------------------------------------------------------
    # Class constructor. The parameters are as follows:
    #
    #     - parent:            A Tkinter widget (e.g. frame) which serves as the parent of this sub-menu.
    #     - gui_elements:      A list, or otherwise iterable, of GUIElements to be updated upon loading a configuration.
    #     - PROGRAM_DIRECTORY: The program main's current working directory.
    #

    def __init__(self, parent, gui_elements, PROGRAM_DIRECTORY):
        
        self.frame = ttk.LabelFrame(parent, text='Configuration', padding=10)
        self.gui_elements = gui_elements

        #-----------------------------------
        # Construct the save button's action

        def save_button_action():

            initdir = os.path.join(PROGRAM_DIRECTORY, 'data', 'sim')
            if not os.path.isdir(initdir):
                initdir = PROGRAM_DIRECTORY

            filename = tkinter.filedialog.asksaveasfilename(initialdir=initdir, filetypes=(('Config file', '*.cfg'), ('All files', '*.*')))
            if filename is not None:
                config = dict()
                for element in self.gui_elements:
                    config = element.get_configuration(config)
                parser = configparser.ConfigParser()
                parser.read_dict({'DEFAULT': config})
                with open(filename, 'w') as config_file:
                    parser.write(config_file)

        self.save_button = ttk.Button(self.frame, text='Save...', command=save_button_action)
        self.save_button.grid(column=0, row=0, padx=5, pady=5)

        #-----------------------------------
        # Construct the load button's action

        def load_button_action():

            initdir = os.path.join(PROGRAM_DIRECTORY, 'data', 'sim')
            if not os.path.isdir(initdir):
                initdir = PROGRAM_DIRECTORY

            filename = tkinter.filedialog.askopenfilename(initialdir=initdir, filetypes=(('Config file', '*.cfg'), ('All files', '*.*')))
            if filename is not None and os.path.isfile(filename):
                try:
                    parser = configparser.ConfigParser()
                    parser.read(filename)
                    config = dict(parser['DEFAULT'])
                    result = 0
                    err_str = ''
                    for element in self.gui_elements:
                        r, err = element.set_configuration(config)
                        result += r
                        err_str += err
                    if r > 0:
                        tkinter.messagebox.showwarning(title='Warning', message='Configuration file contains errors:\n\n'+err_str+'\nErroneous values set to default.')
                except Exception as e:
                    tkinter.messagebox.showerror(title='Error', message='Error occured while loading "'+filename+'":\n\n'+str(e))
   
        self.load_button = ttk.Button(self.frame, text='Load...', command=load_button_action)
        self.load_button.grid(column=0, row=1, padx=5, pady=5)
        

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

