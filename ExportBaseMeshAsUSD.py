import maya.cmds as cmds

"""
-------------------------------------------------------------------------------
Given a base mesh outside a USD stage, export as a USD file, without materials.
This USD file can then be used to import the base mesh as a GEO variant

Inputs:
- variable: export_path - where the USD file will be saved
- variable: rootPrim - name of the rootPrim and variant
- maya viewport: a selected mesh for export

How to use: 
1. Set export_path and rootPrim
2. Select mesh to be exported
3. Run the script

Note: 
- There are several other export options avaialable. Not currently exploring
these options for the sake of time but could be customizable


-------------------------------------------------------------------------------

"""

def exportBaseMeshAsUSD(export_path, rootPrim):
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
        f"rootPrim={rootPrim};"
        f"rootPrimType=scope;"
        f"exportMaterials=0;"
        f"shadingMode={shadingMode};"
        f"convertMaterialsTo=[{convertMaterialsTo}];"
        f"jobContext=[{jobContext}]"
    )

    # Execute the export
    cmds.file(export_path, force=True, options=opts, type="USD Export", preserveReferences=True, exportSelected=True)

    #--------------------------------------------------------------------------------