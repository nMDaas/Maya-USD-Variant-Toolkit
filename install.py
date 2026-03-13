import os
import sys
import shutil
import maya.cmds as cmds

tool_root = cmds.fileDialog2(dialogStyle=2, fileMode=3, caption="Select Root Directory folder")[0]
script_folder = os.path.join(tool_root, "src")
icon_folder = os.path.join(tool_root, "icons")

# Add scripts to sys.path -------------------------------------------------------------------------
if script_folder not in sys.path:
    sys.path.append(script_folder)

# Copy icons --------------------------------------------------------------------------------------
maya_icon_folder = os.path.join(cmds.internalVar(userPrefDir=True), "icons")
os.makedirs(maya_icon_folder, exist_ok=True)
for icon in os.listdir(icon_folder):
    shutil.copy2(os.path.join(icon_folder, icon), maya_icon_folder)

# Create a shelf if it doesn't exist --------------------------------------------------------------
shelf_name = "Maya_USD_Variant_Toolkit"
if not cmds.shelfLayout(shelf_name, exists=True):
    cmds.shelfLayout(shelf_name, parent="ShelfLayout")

# Add buttons -------------------------------------------------------------------------------------
import importlib

# Add button for UsdFileVariantAuthor_exec_tool.py ------------------------------------------------
import UsdFileVariantAuthor_exec_tool # your main script

# Remove button if it exists
buttons = cmds.shelfLayout(shelf_name, q=True, ca=True) or []
for btn in buttons:
    if cmds.shelfButton(btn, q=True, label=True) == "Usd_File_Variant_Author":
        cmds.deleteUI(btn)

cmds.shelfButton(
    parent=shelf_name,
    label="Usd_File_Variant_Author",
    imageOverlayLabel="",
    image="UsdFileVariant_AIcon.png",
    command=f'''
import sys
tool_root = r"{tool_root}"
if tool_root not in sys.path:
    sys.path.append(tool_root)

import src.UsdFileVariantAuthor_exec_tool as tool
tool.run()
''',
    annotation="USD File Variant Manager",
    sourceType="Python"
)

# Add button TransformVariantAuthor_exec_tool.py ----------------------------------------------------
import TransformVariantAuthor_exec_tool # your main script

# Remove button if it exists
buttons = cmds.shelfLayout(shelf_name, q=True, ca=True) or []
for btn in buttons:
    if cmds.shelfButton(btn, q=True, label=True) == "Transform_Variant_Author":
        cmds.deleteUI(btn)

cmds.shelfButton(
    parent=shelf_name,
    label="Transform_Variant_Author",
    imageOverlayLabel="",
    image="TransformVariant_AIcon.png",
    command=f'''
import sys
tool_root = r"{tool_root}"
if tool_root not in sys.path:
    sys.path.append(tool_root)

import src.TransformVariantAuthor_exec_tool as tool
tool.run()
''',
    annotation="Transform Variant Manager",
    sourceType="Python"
)

# Add button MaterialVariantAuthor_exec_tool.py ----------------------------------------------------
import MaterialVariantAuthor_exec_tool # your main script

# Remove button if it exists
buttons = cmds.shelfLayout(shelf_name, q=True, ca=True) or []
for btn in buttons:
    if cmds.shelfButton(btn, q=True, label=True) == "Material_Variant_Author":
        cmds.deleteUI(btn)

cmds.shelfButton(
    parent=shelf_name,
    label="Material_Variant_Author",
    imageOverlayLabel="",
    image="MaterialVariant_AIcon.png",
    command=f'''
import sys
tool_root = r"{tool_root}"
if tool_root not in sys.path:
    sys.path.append(tool_root)

import src.MaterialVariantAuthor_exec_tool as tool
tool.run()
''',
    annotation="Material Variant Manager",
    sourceType="Python"
)

# Add button ModelVariantAuthor_exec_tool.py ----------------------------------------------------
import ModelVariantAuthor_exec_tool # your main script

# Remove button if it exists
buttons = cmds.shelfLayout(shelf_name, q=True, ca=True) or []
for btn in buttons:
    if cmds.shelfButton(btn, q=True, label=True) == "Model_Variant_Author":
        cmds.deleteUI(btn)

cmds.shelfButton(
    parent=shelf_name,
    label="Model_Variant_Author",
    imageOverlayLabel="",
    image="ModelVariant_AIcon.png",
    command=f'''
import sys
tool_root = r"{tool_root}"
if tool_root not in sys.path:
    sys.path.append(tool_root)

import src.ModelVariantAuthor_exec_tool as tool
tool.run()
''',
    annotation="Modeling Variant Manager",
    sourceType="Python"
)

# Add button USDSwitchboard_exec_tool.py ----------------------------------------------------
import UsdVariantSwitchboard_exec_tool # your main script

# Remove button if it exists
buttons = cmds.shelfLayout(shelf_name, q=True, ca=True) or []
for btn in buttons:
    if cmds.shelfButton(btn, q=True, label=True) == "USDVariantSwitchboard":
        cmds.deleteUI(btn)

cmds.shelfButton(
    parent=shelf_name,
    label="USDVariantSwitchboard",
    imageOverlayLabel="",
    image="VariantSwitchboard_AIcon.png",
    command=f'''
import sys
tool_root = r"{tool_root}"
if tool_root not in sys.path:
    sys.path.append(tool_root)

import src.UsdVariantSwitchboard_exec_tool as tool
tool.run()
''',
    annotation="USD Variant Switchboard",
    sourceType="Python"
)

print("✅ Maya_USD_Variant_Toolkit")


