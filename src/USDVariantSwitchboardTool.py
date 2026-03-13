import sys
from PySide6.QtCore import * 
from PySide6.QtGui import *
from PySide6.QtUiTools import *
from PySide6.QtWidgets import *
from functools import partial
import maya.cmds as cmds
from maya import OpenMayaUI
from pathlib import Path
from shiboken6 import wrapInstance
from functools import wraps
import math
import os
import ufe
import mayaUsd.ufe
from pxr import Usd, UsdGeom, Sdf
from PySide6.QtCore import QSettings
from abc import ABC, abstractmethod
import re

# ------------------------------------------------------------------------------------------

class USDVariantSwitchboardTool():
    def __init__(self, _tool_name):
        self.tool_name = _tool_name
        self.switches = [] # refers to existing variant combinations

    def setupUserInterface(self, ui):
        ui.setWindowTitle(self.getToolName())
        ui.setObjectName(self.getToolName())

        # scrollArea_newSwitch and add_button should by default
        ui.scrollArea_newSwitch.hide()
        ui.add_button.hide()

        #TODO: If no switches, should say that

        ui.addSwitchButton.clicked.connect(partial(self.createNewSwitch, ui))
        ui.addVariantButton.clicked.connect(partial(self.add_switch_row, ui))

    # GETTERS ------------------------------------------------------------------------------

    def getToolName(self):
        return self.tool_name
    
    # UI FUNCTIONS -------------------------------------------------------------------------

    def createNewSwitch(self, ui):
        # show options to create a new switch
        scrollArea_newSwitch = ui.findChild(QScrollArea, "scrollArea_newSwitch")
        scrollArea_newSwitch.show()
        ui.add_button.show()

        # hide '+ Variant Combination' button
        ui.addSwitchButton.hide()

    # add dropdown to choose from valid variant options
    def add_switch_row(self, ui):
        # Create widget
        dropdown = QComboBox()
        options = ["Model A", "Model B (Legacy)", "Model C", "Experimental"]
        dropdown.addItems(options)

        # disable invalid options
        item = dropdown.model().item(2)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)

        # add it to the grid layout
        rowIndex = ui.gridLayout_newSwitch.rowCount()
        ui.gridLayout_newSwitch.addWidget(dropdown, rowIndex, 0)

    