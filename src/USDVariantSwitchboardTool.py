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
from pxr import Usd, UsdGeom, Sdf
from PySide6.QtCore import QSettings
from abc import ABC, abstractmethod
import re
import mayaUsd.lib as mayaUsdLib
import mayaUsd.ufe as mayaUsd_ufe

# ------------------------------------------------------------------------------------------

class USDVariantSwitchboardTool():
    def __init__(self, _tool_name):
        self.tool_name = _tool_name
        self.switches = [] # refers to existing variant combinations
        self.discovered_data = {}

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

        proxy_nodes = cmds.ls(type="mayaUsdProxyShape")

        if proxy_nodes:
            stage = self.get_usd_stage(proxy_nodes[0])
            if stage:
                variants = self.get_all_variants(stage)
                import pprint
                pprint.pprint(variants)
        else:
            print("No mayaUsdProxyShape found.")



    # VARIANT SWITCHBOARD SPECIFIC FUNCTIONS -------------------------------------------------------

    def get_usd_stage(self, proxy_node):
        """
        Retrieves the USD Stage without relying on ufe.PathString.
        This uses the mayaUsdLib to get the prim from the Maya node, 
        then grabs the stage from that prim.
        """
        # Ensure we have the shape node, not the transform
        shape = cmds.listRelatives(proxy_node, shapes=True, fullPath=True)
        target = shape[0] if shape else proxy_node
        
        # Get the MayaUsd ProxyPrim and then its Stage
        try:
            proxy_prim = mayaUsdLib.GetPrim(target)
            return proxy_prim.GetStage()
        except Exception as e:
            print(f"Failed to get stage: {e}")
            return None

    # Gets all variants that are active in the outliner
    def get_all_variants(self, stage):
        scene_variants = {}
        if not stage: return scene_variants

        for prim in stage.Traverse():
            vsets = prim.GetVariantSets()
            vset_names = vsets.GetNames()
            
            if vset_names:
                p_path = str(prim.GetPath())
                scene_variants[p_path] = {}
                for vset_name in vset_names:
                    vset = vsets.GetVariantSet(vset_name)
                    scene_variants[p_path][vset_name] = {
                        "options": vset.GetVariantNames(),
                        "current_selection": vset.GetVariantSelection()
                    }
        return scene_variants
        

  