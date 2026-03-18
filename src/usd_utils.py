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
from pxr import Usd, UsdGeom

from errorDialog_exec_tool import errorDialog_exec_tool

# Gets the selected USD XForm (target prim) in the outliner
def get_selected_usd_xform_prim():
    # Get the current UFE (Universal Front End) selection made by user in outliner
    selection = ufe.GlobalSelection.get()

    if selection.empty():
        return None
    
    # Get last item in the selection
    selected_item = list(selection)[-1]

    # Convert UFE path object to a string path
    ufe_path_obj = selected_item.path()
    ufe_path_string = ufe.PathString.string(ufe_path_obj)

    # Access prim via string path
    prim = mayaUsd.ufe.ufePathToPrim(ufe_path_string)

    if not prim or not prim.IsValid():
        errorTitle = "Error: No Target Xform Prim Selected"
        errorMessage = """
        A target prim inside the USD Stage must be selected.
        """
        errorDialog_exec_tool(errorTitle, errorMessage)
    
    # Ensure prim is an Xform
    if (not prim.IsA(UsdGeom.Xform)):
        return None

    return prim

# Gets the selected target prim in the outliner
def get_selected_prim():
    # Get the current UFE (Universal Front End) selection made by user in outliner
    selection = ufe.GlobalSelection.get()

    if selection.empty():
        return None
    
    # Get last item in the selection
    selected_item = list(selection)[-1]

    # Convert UFE path object to a string path
    ufe_path_obj = selected_item.path()
    ufe_path_string = ufe.PathString.string(ufe_path_obj)

    # Access prim via string path
    prim = mayaUsd.ufe.ufePathToPrim(ufe_path_string)

    if not prim or not prim.IsValid():
        errorTitle = "Error: No Target Prim Selected"
        errorMessage = """
        A target prim inside the USD Stage must be selected.
        """
        errorDialog_exec_tool(errorTitle, errorMessage)

    return prim