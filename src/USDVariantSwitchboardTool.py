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

    def createNewSwitch(self, ui):
        # show options to create a new switch
        scrollArea_newSwitch = ui.findChild(QScrollArea, "scrollArea_newSwitch")
        scrollArea_newSwitch.show()
        ui.add_button.show()

        # hide '+ Variant Combination' button
        ui.addSwitchButton.hide()

    # GETTERS ------------------------------------------------------------------------------

    def getToolName(self):
        return self.tool_name