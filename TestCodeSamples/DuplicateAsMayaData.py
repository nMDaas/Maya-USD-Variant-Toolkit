import ufe
import mayaUsd.ufe
from pxr import Usd, UsdGeom, Gf
import maya.mel as mel

"""
----------------------------------------------------------------------------
Given a prim inside a USD stage, duplicate as Maya data outside the stage

Inputs:
- maya viewport: a selected prim to duplicate as maya data

How to use: 
1. Select the prim in the outliner in the USD stage
2. Run the script

----------------------------------------------------------------------------

"""

# Get ufe path of the prim selected
def get_selected_usd_prim_ufe_path():
    selection = ufe.GlobalSelection.get()
    if selection.empty():
        print("Nothing selected.")
        return None
    
    selected_item = list(selection)[-1]
    ufe_path_string = ufe.PathString.string(selected_item.path())
    
    return ufe_path_string

def duplicateAsMayaData():
    basePrim_ufe_path = get_selected_usd_prim_ufe_path()
    print(basePrim_ufe_path)
    mel.eval(f'mayaUsdDuplicate "{basePrim_ufe_path}" ""')

#--------------------------------------------------------------------------------
