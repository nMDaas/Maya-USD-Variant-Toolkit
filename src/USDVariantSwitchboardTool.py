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

        self.stage_variants = {} # self.stage_variants[prim] = (variant_set_name, [option1, option2, ...])
        self.stage_prims = [] # loaded from stage_variants

        # Load stage_variants
        proxy_nodes = cmds.ls(type="mayaUsdProxyShape")
        if proxy_nodes:
            stage = self.get_usd_stage(proxy_nodes[0])
            if stage:
                self.get_all_stage_variants(stage)
                import pprint
        else:
            print("No mayaUsdProxyShape found.")

        # Load stage_prims
        self.get_stage_prims()

    # GETTERS ------------------------------------------------------------------------------

    def getToolName(self):
        return self.tool_name
    
    # UI FUNCTIONS -------------------------------------------------------------------------

    def setupUserInterface(self, ui):
        ui.setWindowTitle(self.getToolName())
        ui.setObjectName(self.getToolName())

        # scrollArea_newSwitch and add_button should by default
        ui.scrollArea_newSwitch.hide()
        ui.add_button.hide()

        #TODO: If no switches, should say that

        ui.addSwitchButton.clicked.connect(partial(self.createNewSwitch, ui))
        ui.addVariantButton.clicked.connect(partial(self.add_switch_row, ui))

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
        options = self.stage_prims
        dropdown.addItems(options)

        # add it to the grid layout
        rowIndex = ui.gridLayout_newSwitch.rowCount()
        ui.gridLayout_newSwitch.addWidget(dropdown, rowIndex, 0)

    def get_stage_prims(self):
        self.stage_prims = []
        for prim_name, vset_list in  self.stage_variants.items():
            self.stage_prims.append(prim_name)

    # VARIANT SWITCHBOARD SPECIFIC FUNCTIONS -------------------------------------------------------

    # TODO: Move this to utilities
    def get_usd_stage(self, proxy_node):
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
    def get_all_stage_variants(self, stage):
        self.stage_variants = {}

        for prim in stage.Traverse():
            vsets = prim.GetVariantSets()
            vset_names = vsets.GetNames()
            
            # Only process if the prim has variant sets
            if vset_names:
                prim_name = prim.GetName()
                
                # self.stage_variants[prim] = (variant_set_name, [option1, option2, ...])
                variant_data = []
                
                for vset_name in vset_names:
                    vset = vsets.GetVariantSet(vset_name)
                    options = vset.GetVariantNames()
                    
                    variant_data.append({
                        "vset_name": vset_name,
                        "variants": options,
                    })
                
                self.stage_variants[prim_name] = variant_data
                
        

  