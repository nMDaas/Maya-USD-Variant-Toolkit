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
            newVariantOptionButton.setObjectName("radio_create_new_variant")
            ui.gridLayout_vs_options.addWidget(newVariantOptionButton, 0, 0)
            newVariantOptionButton.setEnabled(True)
            newVariantOptionButton.setChecked(True)
            newVariantOptionButton.clicked.connect(partial(self.setupUserInterface_NewVariant, ui))
            if exists: # only if existing variant sets of type "transform" on targetPrim
                existingVariantOptionButton = QRadioButton("Edit Existing Variant")
                existingVariantOptionButton.setObjectName("radio_edit_variant")
                ui.gridLayout_vs_options.addWidget(existingVariantOptionButton, 0, 1)  
                existingVariantOptionButton.setEnabled(True)
                existingVariantOptionButton.clicked.connect(partial(self.setupUserInterface_ExistingVariant, ui))
        
            remove_widget = ui.findChild(QPushButton, "vs_remove")
            if (remove_widget):
                remove_widget.hide() 

            ui.final_button.setText("Close")
            ui.final_button.clicked.connect(partial(self.close, ui))

            return True
        
    def manage_delete_variant_set(self, ui):
        self.resetUI(ui)
        exists, existing_vsets = self.find_authoring_variant_sets("transform")
        radio_create_new_variant_button = ui.findChild(QRadioButton, "radio_create_new_variant")
        radio__edit_variant_button = ui.findChild(QRadioButton, "radio_edit_variant")
        if not exists:
            radio_create_new_variant_button.setEnabled(True)
            radio_create_new_variant_button.setChecked(True)
            self.setupUserInterface_NewVariant(ui)
            widget = ui.findChild(QComboBox, "vs_name_dropdown")
            radio__edit_variant_button.hide() 
            widget.hide() 
            ui.vs_remove.hide()
        else:
            self.setupUserInterface_ExistingVariant(ui)

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
        setButton.setFlat(True)
        setButton.setToolTip("Set Xform For Transform Variant")
        setButton.setCursor(Qt.PointingHandCursor)
        setButton.setIconSize(QSize(self.width*0.015, self.height*0.015))

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
        ret, vset = self.createVariantSet(ui)

        if ret is True:
            # create transformation variant for set
            v_name_input_widget = ui.findChild(QLineEdit, f"variant_input_{row_number}")
            v_name_input = v_name_input_widget.text().strip()

            if (not v_name_input):
                ui.error_label.setText(f"Variant name not set")
                ui.error_label.show()
                return False
            
            self.createATransformationVariantSet(self.targetPrim, vset, v_name_input)

            self.apply_permanent_order()
            self.apply_pipeline_tag(ui, "transform")

            # if successful, change pinned icon
            set_button = ui.findChild(QPushButton, f"set_button_{row_number}")
            set_button.setIcon(QIcon(str(self.pinned_icon)))
            set_button.setToolTip("Xform Transform Applied To Variant")
            set_button.setEnabled(False)

            # set as read only
            v_name_input_widget.setReadOnly(True)

            ui.error_label.hide()
            return True
        else:
            return False

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
            

    

