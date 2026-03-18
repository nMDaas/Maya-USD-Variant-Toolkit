# Details

# Instructions: to run, navigate to execute_tool.py and run the file

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

import sys
my_script_dir = "/Users/natashadaas/USD_Switchboard/src" 
if my_script_dir not in sys.path:
    sys.path.append(my_script_dir)

from VariantAuthoringTool import VariantAuthoringTool
from UsdFileVariantAuthor import UsdFileVariantAuthor
from TransformVariantAuthor import TransformVariantAuthor
from MaterialVariantAuthor import MaterialVariantAuthor
from ModelVariantAuthor import ModelVariantAuthor

def one_undo(func):
    """
    Decorator - guarantee close chunk.
    type: (function) -> function
    """
    @wraps(func)
    def wrap(*args, **kwargs):
        try:
            cmds.undoInfo(openChunk=True)
            return func(*args, **kwargs)
        except Exception as e:
            raise e
        finally:
            cmds.undoInfo(closeChunk=True)
    return wrap
        
#show gui window
def showWindow(tool, gui):
    # get this files location so we can find the .ui file in the /ui/ folder alongside it
    UI_FILE = str(Path(__file__).parent.resolve() / gui)
    loader = QUiLoader()
    file = QFile(UI_FILE)
    file.open(QFile.ReadOnly)
     
    #Get Maya main window to parent gui window to it
    mayaMainWindowPtr = OpenMayaUI.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(int(mayaMainWindowPtr), QWidget)
    ui = loader.load(file, parentWidget=mayaMainWindow)
    file.close()
    
    ui.setParent(mayaMainWindow)
    ui.setWindowFlags(Qt.Window)
    
    ui.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

    global folder_path
    folder_path = ''

    # tool specific set up
    successful = tool.setupUserInterface(ui)

    # Runs only if tool setup was successful
    if successful is not False:
        def add_variant_row():
            tool.add_variant_row(ui)

        #connect buttons to functions
        ui.addVariantButton.clicked.connect(add_variant_row)
        
        # show the QT ui
        ui.show()
        return ui

def executeUsdFileVariantAuthor():
    tool = UsdFileVariantAuthor("Manage USD File Variants on Target Prim")
    window=showWindow(tool, "gui.ui")

def executeTransformVariantAuthor():
    tool = TransformVariantAuthor("Manage Transform Variants On Target Prim")
    window=showWindow(tool, "gui.ui")

def executeMaterialVariantAuthor():
    tool = MaterialVariantAuthor("Manage Material Variants On Target Prim")
    window=showWindow(tool, "gui.ui")

def executeModelVariantAuthor():
    tool = ModelVariantAuthor("Manage Modeling Variants on Target Prim")
    window=showWindow(tool, "geo_gui.ui")

if __name__ == "__main__":
    executeWrapper()

   