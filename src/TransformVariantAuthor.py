import sys
from PySide6.QtCore import * 
from PySide6.QtGui import *
from PySide6.QtUiTools import *
from PySide6.QtWidgets import *
from PySide6.QtWidgets import QPushButton
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

my_script_dir = "/Users/natashadaas/USD_Switchboard/src" 
if my_script_dir not in sys.path:
    sys.path.append(my_script_dir)

from VariantAuthoringTool import VariantAuthoringTool

# ------------------------------------------------------------------------------------------

class TransformVariantAuthor(VariantAuthoringTool):

    def __init__(self, _tool_name):
        super().__init__(_tool_name)

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
            # add radio buttons
            exists, existing_vsets = self.find_authoring_variant_sets("transform")
            newVariantOptionButton = QRadioButton("Create New Variant")
            ui.gridLayout_vs_options.addWidget(newVariantOptionButton, 0, 0)
            newVariantOptionButton.setEnabled(True)
            newVariantOptionButton.setChecked(True)
            newVariantOptionButton.clicked.connect(partial(self.setupUserInterface_NewVariant, ui))
            if exists: # only if existing variant sets of type "transform" on targetPrim
                existingVariantOptionButton = QRadioButton("Edit Existing Variant")
                ui.gridLayout_vs_options.addWidget(existingVariantOptionButton, 0, 1)  
                existingVariantOptionButton.setEnabled(True)
                existingVariantOptionButton.clicked.connect(partial(self.setupUserInterface_ExistingVariant, ui))
        
            remove_widget = ui.findChild(QPushButton, "vs_remove")
            if (remove_widget):
                remove_widget.hide() 

            ui.final_button.setText("Close")
            ui.final_button.clicked.connect(partial(self.close, ui))

            return True

    def setupUserInterface_ExistingVariant(self, ui):
        # Check if the targetPrim already has a variant of this type (transform)
        exists, existing_vsets = self.find_authoring_variant_sets("transform")
        if exists:
            self.creatingNewVariant = False
            self.populateExistingVariantSetInUI(ui, existing_vsets)

        remove_widget = ui.findChild(QPushButton, "vs_remove")
        if (remove_widget):
            remove_widget.show() 

    def setupUserInterface_NewVariant(self, ui):
        self.resetUI(ui)
        widget = ui.findChild(QComboBox, "vs_name_dropdown")
        widget.hide() 

        remove_widget = ui.findChild(QPushButton, "vs_remove")
        if (remove_widget):
            remove_widget.hide() 

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

        setButton.clicked.connect(lambda checked=False, r=rowIndex: self.setTransformVariant(ui, r))

    # VARIANT AUTHORING SPECIFIC FUNCTIONS -------------------------------------------------------

    # set XForm transform as variant for that row - linked to row number
    def setTransformVariant(self, ui, row_number):
        # create set
        variant_set_name = ui.vs_name_input.text()
        vset = self.createVariantSet(variant_set_name)

        # create transformation variant for set
        v_name_input_widget = ui.findChild(QLineEdit, f"variant_input_{row_number}")
        v_name_input = v_name_input_widget.text().strip()
        self.createATransformationVariantSet(self.targetPrim, vset, v_name_input)

        self.apply_permanent_order()
        self.apply_pipeline_tag(variant_set_name)

        # if successful, change pinned icon
        set_button = ui.findChild(QPushButton, f"set_button_{row_number}")
        set_button.setIcon(QIcon(str(self.pinned_icon)))

        # set as read only
        v_name_input_widget.setReadOnly(True)

    def createATransformationVariantSet(self, targetPrim, vset, variant_name):
        # Get the manual overrides currently on the prim
        recorded_values = {}
        attrs_to_clear = []
        
        for attr in targetPrim.GetAttributes():
            if attr.IsAuthored() and attr.Get() is not None:
                attr_name = attr.GetName()
                recorded_values[attr_name] = attr.Get()
                attrs_to_clear.append(attr)

        # Create/select the new variant and author the values
        vset.AddVariant(variant_name)
        vset.SetVariantSelection(variant_name)

        with vset.GetVariantEditContext():
            for attr_name, val in recorded_values.items():            
                attr = targetPrim.GetAttribute(attr_name)
                if (attr):
                    attr.Set(val)
        # Clear the top-level overrides so the variant can take over
        for attr in attrs_to_clear:
            attr.Clear()

        vset.SetVariantSelection("") 
            
        print(f"Recorded variant '{variant_name}' and cleared top-level overrides.")

    def apply_permanent_order(self):
        attr = self.targetPrim.GetAttribute("xformOpOrder")
        if attr.HasValue():
            print(f"Prim already has attribute")
            return
        
        else:
            stage = self.targetPrim.GetStage()
            
            target_layer = stage.GetRootLayer()

            with Usd.EditContext(stage, target_layer):
                xformable = UsdGeom.Xformable(self.targetPrim)

                tOp = xformable.AddTranslateOp()
                rOp = xformable.AddRotateXYZOp()
                sOp = xformable.AddScaleOp()

                xformable.SetXformOpOrder([tOp, rOp, sOp])
                
            print(f"Authored xformOpOrder to layer: {target_layer.identifier}")

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
                    attr.Set("transform")
                else:
                    attr = self.targetPrim.CreateAttribute("variant_set_pipeline_tag", Sdf.ValueTypeNames.String)
                    attr.Set("transform")    
            

    

