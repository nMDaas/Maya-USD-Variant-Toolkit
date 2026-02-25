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
from pxr import Usd, UsdGeom, Gf, UsdShade, Sdf
from PySide6.QtCore import QSettings
from abc import ABC, abstractmethod

my_script_dir = "/Users/natashadaas/USD_Switchboard/src" 
if my_script_dir not in sys.path:
    sys.path.append(my_script_dir)

from VariantAuthoringTool import VariantAuthoringTool

# ------------------------------------------------------------------------------------------

class MaterialVariantAuthor(VariantAuthoringTool):

    def __init__(self, _tool_name):
        super().__init__(_tool_name)

        self.usd_filepath_dict = {} # stores [row, filepath]

        # icon paths
        self.pin_icon = Path(__file__).parent / "icons" / "pin.png"
        self.pinned_icon  = Path(__file__).parent / "icons" / "pin-confirmed.png"

    # UI FUNCTIONS -------------------------------------------------------------------------

    def close(self, ui):
        ui.close()

    def setupUserInterface(self, ui):
        successful = super().setupUserInterface(ui)

        if successful is False:
            return False
        else:
            # Check if the targetPrim already has a variant of this type (material)
            exists, existing_vsets = self.find_authoring_variant_sets("material")
            remove_widget = ui.findChild(QPushButton, "vs_remove")
            if exists:
                self.creatingNewVariant = False
                self.handle_vs_selection_change(ui, existing_vsets[0].GetName())
                if (remove_widget):
                    remove_widget.show() 
            else:
                remove_widget.hide() 

            ui.final_button.setText("Close")
            ui.final_button.clicked.connect(partial(self.close, ui))

            return True

    def add_variant_row(self, ui):
        # Create widgets
        label = QLabel(f"Variant: ")
        variant_name_line_edit = QLineEdit()
        setButton = QPushButton()

        # Setting setButton settings
        setButton.setIcon(QIcon(str(self.pin_icon)))
        setButton.setIconSize(QSize(22,22))
        setButton.setFlat(True)

        # Get new row index
        rowIndex = ui.gridLayout.rowCount()

        if (rowIndex == 1):
            variant_name_line_edit.setText("Default")

        # Setting object names
        variant_name_line_edit.setObjectName(f"variant_input_{rowIndex}")
        setButton.setObjectName(f"set_button_{rowIndex}")

        # Add to the grid layout in new row
        ui.gridLayout.addWidget(label, rowIndex, 0)
        ui.gridLayout.addWidget(variant_name_line_edit, rowIndex, 1)    
        ui.gridLayout.addWidget(setButton, rowIndex, 2)   

        setButton.clicked.connect(lambda checked=False, r=rowIndex: self.setMaterialVariantSet(ui, r))

    # VARIANT AUTHORING SPECIFIC FUNCTIONS -------------------------------------------------------

    # set XForm material variant for that row - linked to row number
    def setMaterialVariantSet(self, ui, row_number):
        # create set
        variant_set_name = ui.vs_name_input.text()
        vset = self.createVariantSet(variant_set_name)
        material_path = self.get_material_path()

        # create transformation variant for set
        v_name_input_widget = ui.findChild(QLineEdit, f"variant_input_{row_number}")
        v_name_input = v_name_input_widget.text().strip()
        self.createAMaterialVariant(vset, v_name_input, material_path)

        self.reset_binding()
        self.apply_pipeline_tag(variant_set_name)

        # if successful, change pinned icon
        set_button = ui.findChild(QPushButton, f"set_button_{row_number}")
        set_button.setIcon(QIcon(str(self.pinned_icon)))

        # set as read only
        v_name_input_widget.setReadOnly(True)

    def get_material_path(self):
        binding_api = UsdShade.MaterialBindingAPI(self.targetPrim)
        
        material, relationship = binding_api.ComputeBoundMaterial()
        
        if material:
            return material.GetPath() # returns something similar to '/mtl/UsdPreviewSurface1'
        else:
            return "No material bound to this Prim."


    def createAMaterialVariant(self, vset, variant_name, material_path):
        # Create/select the new variant and author the values
        vset.AddVariant(variant_name)
        vset.SetVariantSelection(variant_name)
        
        proxy_shape_path = "|stage1|stageShape1"
        stage = mayaUsd.ufe.getStage(proxy_shape_path)

        with vset.GetVariantEditContext():
            binding_api = UsdShade.MaterialBindingAPI.Apply(self.targetPrim)
            material_path = Sdf.Path(material_path)
            
            # Create the relationship pointing to your material
            binding_api.Bind(UsdShade.Material.Get(stage, material_path))

    def reset_binding(self):
        rel = self.targetPrim.GetRelationship("material:binding")
        
        if rel:
            if rel.HasAuthoredTargets():
                print("Clearing materal:binding relationships...")
                rel.ClearTargets(True) 
            else:
                print("Relationship exists but is already empty.")

    def apply_pipeline_tag(self, variant_set_name):
        vset = self.targetPrim.GetVariantSet(variant_set_name)
        attr = self.targetPrim.GetAttribute("variant_set_pipeline_tag")
        variant_names = vset.GetVariantNames()

        stage = self.targetPrim.GetStage()
        target_layer = stage.GetRootLayer()

        for var_name in variant_names:
            vset.SetVariantSelection(var_name)

            with vset.GetVariantEditContext(target_layer):
                attr = self.targetPrim.GetAttribute("variant_set_pipeline_tag")

                if (attr):
                    attr.Set("material")
                else:
                    attr = self.targetPrim.CreateAttribute("variant_set_pipeline_tag", Sdf.ValueTypeNames.String)
                    attr.Set("material")   

