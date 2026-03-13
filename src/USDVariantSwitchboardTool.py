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

        self.prim_vsets_map = {} # map[prim] = {vs1, vs2, ...}
        self.vset_variants_map = {} #map[prim/vset] = {v1, v2, ...}
        self.stage_prisms = []

        # Load stage_variants
        proxy_nodes = cmds.ls(type="mayaUsdProxyShape")
        if proxy_nodes:
            stage = self.get_usd_stage(proxy_nodes[0])
            if stage:
                self.get_all_stage_variants(stage)
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
        # Create prim dropdown widget
        prim_dropdown = QComboBox()
        prim_dropdown.addItems(self.stage_prims)

        # Create variant set dropdown widget
        vset_dropdown = QComboBox()
        vset_dropdown.addItems(self.prim_vsets_map[self.stage_prims[0]])

        # add it to the grid layout
        rowIndex = ui.gridLayout_newSwitch.rowCount()
        ui.gridLayout_newSwitch.addWidget(prim_dropdown, rowIndex, 0)
        ui.gridLayout_newSwitch.addWidget(vset_dropdown, rowIndex, 1)

    def get_stage_prims(self):
        self.stage_prims = []
        for prim_name, vset_list in  self.prim_vsets_map.items():
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
        self.prim_vsets_map = {}
        self.vset_variants_map = {}

        for prim in stage.Traverse():
            prim_name = prim.GetName()
            vsets = prim.GetVariantSets()
            vset_names = vsets.GetNames()
            vs_variants_map = []
            
            # Only process if the prim has variant sets
            if vset_names:      
                self.prim_vsets_map[prim_name] = vset_names

                for vset_name in vset_names:
                    vset = vsets.GetVariantSet(vset_name)
                    variants = vset.GetVariantNames()

                    # Only process if the variant set has variants
                    if variants:
                        key_name = prim_name + "/" + vset_name
                        self.vset_variants_map[key_name] = variants

                

                
                
                
        

  