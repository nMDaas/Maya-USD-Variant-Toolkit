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

class GeoVariantAuthor(VariantAuthoringTool):

    def __init__(self, _tool_name):
        super().__init__(_tool_name)

        # Dictionary to store where usd files for geometry will be stored
        self.usd_filepath_dict = {} # stores [row, filepath]
        self.geo_dict = {} # stores [row, geo]

        # icon paths
        self.open_folder_icon = Path(__file__).parent / "icons" / "open-folder.png"
        self.folder_chosen_icon  = Path(__file__).parent / "icons" / "open-folder-confirmed.png"
        self.pin_icon = Path(__file__).parent / "icons" / "pin.png"
        self.pinned_icon  = Path(__file__).parent / "icons" / "pin-confirmed.png"

    # UI FUNCTIONS -------------------------------------------------------------------------

    def apply(self, ui):
        variant_set_name = ui.vs_name_input.text()
        vset = self.createVariantSet(variant_set_name)
        
        self.createVariantsForSet(ui, vset)

        self.apply_pipeline_tag(variant_set_name)

        ui.close()

    def setupUserInterface(self, ui):
        successful = super().setupUserInterface(ui)

        if successful is False:
            return False
        else:
            # Check if the targetPrim already has a variant of this type (geo)
            exists, existing_vsets = self.find_authoring_variant_sets("geo")
            remove_widget = ui.findChild(QPushButton, "vs_remove")
            if exists:
                self.creatingNewVariant = False
                self.handle_vs_selection_change(ui, existing_vsets[0].GetName()) # populate
                if (remove_widget):
                    remove_widget.show() 
            else:
                remove_widget.hide() 

            return False

        # Populate selected objects into rows
        selected_objects = cmds.ls(selection=True, long=True)
        for obj in selected_objects:
            self.add_variant_row(ui, obj)

        ui.final_button.setText("Create Variants")
        ui.final_button.clicked.connect(partial(self.apply, ui))
        

    def add_variant_row(self, ui, targetGeo_long=None):
        # Create widgets
        label = QLabel(f"Variant: ")
        variant_name_line_edit = QLineEdit()

        setButton = QPushButton()
        folderButton = QPushButton()

        # Get new row index
        rowIndex = ui.gridLayout.rowCount()

        # Setting setButton settings
        setButton.setIconSize(QSize(22,22))
        setButton.setFlat(True)
        # Populate names automatically if targetGeos selected
        if targetGeo_long is not None:
            variantName = targetGeo_long.split("|")[-1]
            variant_name_line_edit.setText(variantName)
            setButton.setIcon(QIcon(str(self.pinned_icon)))
            # Add obj to dictionary
            self.geo_dict[rowIndex] = targetGeo_long
        else:
            setButton.setIcon(QIcon(str(self.pin_icon))) 

        # Setting folderButton settings
        folderButton.setIcon(QIcon(str(self.open_folder_icon)))
        folderButton.setIconSize(QSize(22,22))
        folderButton.setFlat(True)

        if (rowIndex == 1 and targetGeo_long is None):
            variant_name_line_edit.setText("Default")

        # Setting object names
        variant_name_line_edit.setObjectName(f"variant_input_{rowIndex}")
        folderButton.setObjectName(f"select_button_{rowIndex}")
        setButton.setObjectName(f"set_button_{rowIndex}")

        # Add to the grid layout in new row
        ui.gridLayout.addWidget(label, rowIndex, 0)
        ui.gridLayout.addWidget(variant_name_line_edit, rowIndex, 1)    
        ui.gridLayout.addWidget(setButton, rowIndex, 2)   
        ui.gridLayout.addWidget(folderButton, rowIndex, 3)   

        setButton.clicked.connect(lambda checked=False, r=rowIndex: self.setGeo(ui, r))
        folderButton.clicked.connect(lambda checked=False, r=rowIndex: self.showDialogForUSDFileSelection(ui, r))  

    # Set which geo is connected to the row for variant creation
    def setGeo(self, ui, row_number):
        selection = cmds.ls(selection=True, long=True)
        targetGeo_long = selection[0]
        self.geo_dict[row_number] = targetGeo_long

        # if successful, change pinned icon
        set_button = ui.findChild(QPushButton, f"set_button_{row_number}")
        set_button.setIcon(QIcon(str(self.pinned_icon)))

    # open dialog for user to select USD file - linked to row number
    def showDialogForUSDFileSelection(self, ui, row_number):
        if self.settings.value("defaultDirectory") is None:
            self.settings.setValue(
                "defaultDirectory",
                cmds.workspace(query=True, rootDirectory=True)
            )

        initial_directory = self.settings.value("defaultDirectory")
        select_button = ui.findChild(QPushButton, f"select_button_{row_number}")

        file_selected, _ = QFileDialog.getSaveFileName(
            ui,
            "Save As USD File",
            initial_directory,
            "USD Files (*.usd *.usda *.usdc)"
        )

        if file_selected:
            # Ensure extension exists (optional but recommended)
            if not file_selected.lower().endswith((".usd", ".usda", ".usdc")):
                file_selected += ".usd"

            self.settings.setValue(
                "defaultDirectory",
                str(Path(file_selected).parent)
            )

            self.usd_filepath_dict[row_number] = file_selected
            select_button.setIcon(QIcon(str(self.folder_chosen_icon)))
        else:
            select_button.setIcon(QIcon(str(self.open_folder_icon)))

    # VARIANT AUTHORING SPECIFIC FUNCTIONS -------------------------------------------------------

    # Creates all the variants for the set
    def createVariantsForSet(self, ui, vset):
        # Iterate through all num_variants
        # num_variants = ui.gridLayout.rowCount() - 1
        for i in range(1, ui.gridLayout.rowCount()):
            v_name_input_widget = ui.findChild(QLineEdit, f"variant_input_{i}")

            # Only make variants for NEW variants (ones that do not have object name pattern of variant_input_x)
            # This works because when populating existing variants, I didn't give it object names
            if v_name_input_widget:
                v_name_input = v_name_input_widget.text().strip() # strip white spaces just in case
                file_selected = self.usd_filepath_dict[i]
                targetGeo_long = self.geo_dict[i]
                self.createVariant(vset, v_name_input, targetGeo_long, file_selected)

        # set default variant as the first variant, only if the variant set is new
        if self.creatingNewVariant:
            v_name_input_widget_1 = ui.findChild(QLineEdit, f"variant_input_1")
            v_name_input_1 = v_name_input_widget_1.text().strip() 
            vset.SetVariantSelection(v_name_input_1)

    # Creates a singular variant for a set
    def createVariant(self, vset, variant_name, targetGeo_long, file_selected):
        # Export targetGeo to USD file
        self.exportBaseMeshAsUSD(targetGeo_long, file_selected)
        print(f"{targetGeo_long} exported to {file_selected}")

        # Create variant for set
        vset.AddVariant(variant_name)
        vset.SetVariantSelection(variant_name)
        # Go inside the variant and add the file reference
        with vset.GetVariantEditContext():
            self.targetPrim.GetPayloads().AddPayload(file_selected)
        print(f"Variant '{variant_name}' authored with reference to: {file_selected}")   

    def exportBaseMeshAsUSD(self, targetGeo_long, export_path):
        targetGeo = targetGeo_long.split("|")[-1]

        # These inputs CAN come from the user and can be customizable
        # However, for now, these are set in stone
        exportUVS = 1
        exportSkels = "none"
        exportSkin = "none"
        exportBlendShapes = 0
        exportDisplayColor = 0
        exportColorSets = 1
        exportComponentTags = 1
        defaultMeshScheme = "catmullClark"
        animation = 0
        shadingMode = "useRegistry"
        convertMaterialsToArray = ["MaterialX"]
        jobContextArray = ["Arnold"]

        # Convert arrays to strings
        convertMaterialsTo = ",".join(convertMaterialsToArray)
        jobContext = ",".join(jobContextArray)

        # defaultUSDFormat, rootPrimType, and exportMaterials are not customizable
        # This is because these settings are required to export the base mesh as USD without any other settings
        opts = (
            f"exportUVs={exportUVS};"
            f"exportSkels={exportSkels};"
            f"exportSkin={exportSkin};"
            f"exportBlendShapes={exportBlendShapes};"
            f"exportDisplayColor={exportDisplayColor};"
            f"exportColorSets={exportColorSets};"
            f"exportComponentTags={exportComponentTags};"
            f"defaultMeshScheme={defaultMeshScheme};"
            f"animation={animation};"
            f"defaultUSDFormat=usda;"
            f"rootPrim={targetGeo};"
            f"rootPrimType=scope;"
            f"exportMaterials=0;"
            f"shadingMode={shadingMode};"
            f"convertMaterialsTo=[{convertMaterialsTo}];"
            f"jobContext=[{jobContext}]"
        )

        # Select geometry to be exported
        cmds.select(targetGeo_long)

        # Execute the export
        # TODO: Check if something is selected by the user and raise a warning if not
        cmds.file(export_path, force=True, options=opts, type="USD Export", preserveReferences=True, exportSelected=True)

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
                    attr.Set("geo")
                else:
                    attr = self.targetPrim.CreateAttribute("variant_set_pipeline_tag", Sdf.ValueTypeNames.String)
                    attr.Set("geo")    
