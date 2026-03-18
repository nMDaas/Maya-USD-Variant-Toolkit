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
def showWindow(errorTitle, errorMessage):
    # get this files location so we can find the .ui file in the /ui/ folder alongside it
    UI_FILE = str(Path(__file__).parent.resolve() / "error_gui.ui")
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

    # Add warning image
    warning_icon = Path(__file__).parent / "icons" / "warning.png"
    warningLabel = ui.warning_image
    pix = QPixmap(warning_icon)
    scaled_pix = pix.scaled(
        30, 30,                 
        Qt.KeepAspectRatio,      
        Qt.SmoothTransformation  
    )
    warningLabel.setPixmap(scaled_pix)
    warningLabel.setScaledContents(False)

    # Add warning message
    ui.error_message.setText(errorMessage)

    ui.setWindowTitle(errorTitle)
    ui.setObjectName(errorMessage)    

    # show the QT ui
    ui.show()
    return ui

def createErrorDialogWindow(errorTitle, errorMessage):
    window=showWindow(errorTitle, errorMessage)

   