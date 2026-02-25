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

my_script_dir = "/Users/natashadaas/USD_Switchboard/src" 
if my_script_dir not in sys.path:
    sys.path.append(my_script_dir)

from VariantAuthoringTool import VariantAuthoringTool

# ------------------------------------------------------------------------------------------

class UsdFileVariantAuthor(VariantAuthoringTool):

    def __init__(self, _tool_name):
        super().__init__(_tool_name)

        self.usd_filepath_dict = {} # stores [row, filepath]

        # icon paths
        self.open_folder_icon = Path(__file__).parent / "icons" / "open-folder.png"
        self.folder_chosen_icon  = Path(__file__).parent / "icons" / "open-folder-confirmed.png"

    # UI FUNCTIONS -------------------------------------------------------------------------

    def apply(self, ui):
        variant_set_name = ui.vs_name_input.text()
        vset = self.createVariantSet(variant_set_name)
        
        self.createVariantsForSet(ui, vset)
        ui.close()

    def setupUserInterface(self, ui):
        successful = super().setupUserInterface(ui)

        if successful is False:
            return False
        else:
            # Check if the targetPrim already has a variant of this type (usd_file)
            exists, existing_vsets = self.find_authoring_variant_sets("usd_file")
            remove_widget = ui.findChild(QPushButton, "vs_remove")
            if exists:
                self.creatingNewVariant = False
                self.handle_vs_selection_change(ui, existing_vsets[0].GetName())
                if (remove_widget):
                    remove_widget.show() 
            else:
                remove_widget.hide() 

            ui.final_button.setText("Create Variants")
            ui.final_button.clicked.connect(partial(self.apply, ui))

            return True

    def open_folder(self, ui, row_number):
        print(f"Opening folder for row: {row_number}")
        # Now you can find the specific LineEdit for this row:
        line_edit = ui.findChild(QLineEdit, f"variant_input_{row_number}")
        if line_edit:
            print(f"Current text is: {line_edit.text()}")

    def add_variant_row(self, ui):
        # Create widgets
        label = QLabel(f"Variant: ")
        variant_name_line_edit = QLineEdit()
        folderButton = QPushButton()

        # Setting folderButton settings
        folderButton.setIcon(QIcon(str(self.open_folder_icon)))
        folderButton.setIconSize(QSize(22,22))
        folderButton.setFlat(True)
        folderButton.setToolTip("Select USD file")
        folderButton.setCursor(Qt.PointingHandCursor)

        # Get new row index
        rowIndex = ui.gridLayout.rowCount()

        if (rowIndex == 1):
            variant_name_line_edit.setText("Default")

        # Setting object names
        variant_name_line_edit.setObjectName(f"variant_input_{rowIndex}")
        folderButton.setObjectName(f"select_button_{rowIndex}")

        # Add to the grid layout in new row
        ui.gridLayout.addWidget(label, rowIndex, 0)
        ui.gridLayout.addWidget(variant_name_line_edit, rowIndex, 1)    
        ui.gridLayout.addWidget(folderButton, rowIndex, 2)   

        folderButton.clicked.connect(lambda checked=False, r=rowIndex: self.showDialogForUSDFileSelection(ui, r))

    # open dialog for user to select USD file - linked to row number
    def showDialogForUSDFileSelection(self, ui, row_number):
        if self.settings.value("defaultDirectory") is None:
            self.settings.setValue("defaultDirectory",  cmds.workspace(query=True, rootDirectory=True))

        initial_directory =  self.settings.value("defaultDirectory")
        select_button = ui.findChild(QPushButton, f"select_button_{row_number}")

        dialog = QFileDialog()
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setDirectory(initial_directory)
        dialog.setWindowTitle("Select USD File")

        # show which filename was selected if a folder was selected
        if dialog.exec_():
            file_selected = dialog.selectedFiles()[0]
            self.settings.setValue("defaultDirectory",  str(Path(file_selected).parent))
            self.usd_filepath_dict[row_number] = file_selected
            select_button.setIcon(QIcon(str(self.folder_chosen_icon)))
            select_button.setToolTip(file_selected)
        else:
            select_button.setIcon(QIcon(str(self.open_folder_icon))) 

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
                self.createVariant(vset, v_name_input, file_selected)

        # set default variant as the first variant, only if the variant set is new
        if self.creatingNewVariant:
            v_name_input_widget_1 = ui.findChild(QLineEdit, f"variant_input_1")
            v_name_input_1 = v_name_input_widget_1.text().strip() 
            vset.SetVariantSelection(v_name_input_1)

    #TODO: warning if file has not been selected
    #TODO: There should be error checking for if the variant_name already exists for the vset
    def createVariant(self, vset, variant_name, file_selected):
        vset.AddVariant(variant_name)

        vset.SetVariantSelection(variant_name)

        # Go inside the variant and add the file reference
        with vset.GetVariantEditContext():
            self.targetPrim.GetReferences().AddReference(file_selected)
            attr = self.targetPrim.CreateAttribute("variant_set_pipeline_tag", Sdf.ValueTypeNames.String)
            attr.Set("usd_file")
        
        print(f"Variant '{variant_name}' authored with reference to: {file_selected}")

