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
from pxr import Usd, UsdGeom, Sdf
from PySide6.QtCore import QSettings
from abc import ABC, abstractmethod
import re

my_script_dir = "/Users/natashadaas/USD_Switchboard/src" 
if my_script_dir not in sys.path:
    sys.path.append(my_script_dir)

from usd_utils import get_selected_usd_xform_prim
from errorDialog_exec_tool import errorDialog_exec_tool

# ------------------------------------------------------------------------------------------

class VariantAuthoringTool(ABC):
    @abstractmethod
    def __init__(self, _tool_name):
        self.tool_name = _tool_name
        self.targetPrim = get_selected_usd_xform_prim() # set targetPrim - the XForm that will have the variant
        self.proxy_shape_path = "|stage1|stageShape1"
        self.stage = mayaUsd.ufe.getStage(self.proxy_shape_path)
        
        self.creatingNewVariant = True # keeps track of whether we are creating a new variant or not

        # Set 
        self.settings = QSettings("USD_Switchboard", "VariantAuthoringTool")

        # icon paths
        self.remove_icon  = Path(__file__).parent / "icons" / "remove.png"

        self.screen = QApplication.primaryScreen().geometry()
        self.width = self.screen.width()
        self.height = self.screen.height()

    # GETTERS ------------------------------------------------------------------------------

    def getToolName(self):
        return self.tool_name
    
    def getTargetPrimPath(self):
        return self.targetPrim.GetPath()
    
    # UI SETUP -----------------------------------------------------------------------------

    @abstractmethod
    def setupUserInterface(self, ui):
        ui.setWindowTitle(self.getToolName())
        ui.setObjectName(self.getToolName())

        if self.targetPrim is None:
            errorTitle = "Error: No Target Prim Selected"
            errorMessage = """
            A target prim of type Xform must be selected to create a variant set.
            """
            errorDialog_exec_tool(errorTitle, errorMessage)
            return False

        ui.targetPrim.setText(f"Target Prim: {self.getTargetPrimPath()}")

        # Set the icon for the variant set remove button
        ui.vs_remove.setIcon(QIcon(str(self.remove_icon)))
        ui.vs_remove.setIconSize(QSize(self.width*0.025, self.height*0.025))
        ui.vs_remove.setFlat(True)
        ui.vs_remove.clicked.connect(lambda checked=False: self.deleteVariantSet(ui))
        ui.vs_remove.setToolTip("Delete Variant Set")
        ui.vs_remove.setCursor(Qt.PointingHandCursor)

        return True

        pass
    
    def find_authoring_variant_sets(self, targetValue):
        attr = self.targetPrim.GetAttribute("variant_set_pipeline_tag")
        # Get all places where this attribute is authored
        property_stack = attr.GetPropertyStack()

        existing_vsets = [] # where variant_set_pipeline_tag = targetValue

        for p in property_stack:
            path = str(p.path)
            value = p.default
            
            if (value == targetValue):
                match = re.search(r"\{([^=]+)=", path)
                if match:
                    print(match.group(1))
                    vset_name = match.group(1)
                    vsets = self.getVariantSetsOfTargetPrim()
                    variant_set = vsets.GetVariantSet(vset_name)
                    existing_vsets.append(variant_set)

        if (len(existing_vsets) > 0):
            return True, existing_vsets
        else:             
            return False, None
    
    # UI FUNCTIONS -------------------------------------------------------------------------

    def open_folder(self, ui, row_number):
        print(f"Opening folder for row: {row_number}")
        # Now you can find the specific LineEdit for this row:
        line_edit = ui.findChild(QLineEdit, f"variant_input_{row_number}")
        if line_edit:
            print(f"Current text is: {line_edit.text()}")

    @abstractmethod
    def add_variant_row(self, ui):
        pass

    def add_existing_variant_row(self, ui, v_name):
        label = QLabel(f"Variant: ")
        variant_name_label = QLineEdit()
        removeButton = QPushButton()

        # Set name of variant name and as read only
        variant_name_label.setText(v_name)
        variant_name_label.setReadOnly(True)

        # Setting removeButton settings
        removeButton.setIcon(QIcon(str(self.remove_icon)))
        ui.vs_remove.setIconSize(QSize(self.width*0.025, self.height*0.025))
        removeButton.setFlat(True)
        removeButton.setToolTip("Delete Variant")
        removeButton.setCursor(Qt.PointingHandCursor)
        
        # Get new row index
        rowIndex = ui.gridLayout.rowCount()

        # set object names
        variant_name_label.setObjectName(f"variant_label_{rowIndex}")

        # Add to the grid layout in new row
        ui.gridLayout.addWidget(label, rowIndex, 0)
        ui.gridLayout.addWidget(variant_name_label, rowIndex, 1) 
        ui.gridLayout.addWidget(removeButton, rowIndex, 2) 

        # Connect buttons
        removeButton.clicked.connect(lambda checked=False, r=rowIndex: self.removeVariantFromSet(ui, r))

    def handle_vs_selection_change(self, ui, vset_selection_name):
        self.resetUI(ui)
        vset_selection = self.targetPrim.GetVariantSet(vset_selection_name)
        ui.vs_name_input.setText(vset_selection_name)
        ui.vs_name_input.setReadOnly(True)
        variants = vset_selection.GetVariantNames()
        for v in variants:
            self.add_existing_variant_row(ui, v)

    def populateExistingVariantSetInUI(self, ui, vsets):
        vs_name_dropdown = ui.findChild(QComboBox, "vs_name_dropdown")

        if vs_name_dropdown is None:
            vs_name_dropdown = QComboBox()

        for i in range(len(vsets)):
            vs_name_dropdown.addItem(vsets[i].GetName())

        ui.gridLayout_vs_options.addWidget(vs_name_dropdown, 0, 2)
        vs_name_dropdown.setObjectName("vs_name_dropdown")

        vs_name_dropdown.currentTextChanged.connect(
            lambda text: self.handle_vs_selection_change(ui, text)
        )

        self.handle_vs_selection_change(ui, vsets[0].GetName())

    def resetUI(self, ui):
        ui.vs_name_input.setReadOnly(False)
        ui.vs_name_input.setText("")
        for i in reversed(range(1, ui.gridLayout.count())):
            item = ui.gridLayout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()

    @abstractmethod
    def manage_delete_variant_set(self, ui):
        pass
    
    # VARIANT AUTHORING SPECIFIC FUNCTIONS -------------------------------------------------------

    # Get number variant sets for XForm
    def getVariantSetsOfTargetPrim(self):
        vsets = self.targetPrim.GetVariantSets()
        return vsets
    
    def removeVariantFromSet(self, ui, row_number):
        # Get variant set
        vs_name = ui.vs_name_input.text()

        # Get variant to delete
        v_name_input_widget = ui.findChild(QLineEdit, f"variant_label_{row_number}")
        v_name = v_name_input_widget.text().strip()

        targetPrim_path = self.targetPrim.GetPath()

        for layer in self.stage.GetLayerStack():
            prim_spec = layer.GetPrimAtPath(targetPrim_path)
            if prim_spec and vs_name in prim_spec.variantSets:
                vset_spec = prim_spec.variantSets[vs_name]
                
                if v_name in vset_spec.variants:
                    vset_spec.RemoveVariant(vset_spec.variants[v_name])
                    print(f"Successfully deleted '{v_name}' from layer: {layer.identifier}")

        self.handle_vs_selection_change(ui, vs_name)
    
    # Creates a variant set of a given name for a given XForm
    def createVariantSet(self, ui):
        variant_set_name = ui.vs_name_input.text()

        if not variant_set_name:
            ui.error_label.setText(f"ERROR: Variant set name is empty.")
            ui.error_label.show()
            return False, None

        vset = self.targetPrim.GetVariantSets().AddVariantSet(variant_set_name)
        ui.error_label.hide()
        return True, vset
    
    def deleteVariantSet(self, ui):
        # Get variant set
        vs_name = ui.vs_name_input.text()
        targetPrim_path = self.targetPrim.GetPath()

        layer = self.stage.GetRootLayer()
        self.stage.SetEditTarget(Usd.EditTarget(layer))

        prim_spec = self.stage.GetRootLayer().GetPrimAtPath(targetPrim_path)

        if prim_spec and vs_name in prim_spec.variantSets:
            # 4. Use the Python del keyword to remove the variant set from the prim spec's variantSets
            del prim_spec.variantSets[vs_name]
            
            vset_names = prim_spec.variantSetNameList
            if vs_name in vset_names.prependedItems:
                vset_names.prependedItems.remove(vs_name)
            if vs_name in vset_names.appendedItems:
                vset_names.appendedItems.remove(vs_name)
            if vs_name in vset_names.explicitItems:
                vset_names.explicitItems.remove(vs_name)
                
            print(f"Completely scrubbed variant set: {vs_name}")

        self.manage_delete_variant_set(ui)

    def apply_pipeline_tag(self, ui, tag_name):
        variant_set_name = ui.vs_name_input.text()
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
                    attr.Set(tag_name)
                else:
                    attr = self.targetPrim.CreateAttribute("variant_set_pipeline_tag", Sdf.ValueTypeNames.String)
                    attr.Set(tag_name) 


