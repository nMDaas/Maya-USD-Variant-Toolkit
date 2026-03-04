import sys
my_script_dir = "/Users/natashadaas/USD_Switchboard/" 
if my_script_dir not in sys.path:
    sys.path.append(my_script_dir)

# Imports
import ExportBaseMeshAsUSD
import CreateGeoVariantFromUSDFile
import DuplicateAsMayaData

"""
-------------------------------------------------------------------------------
Workflow for creating base mesh GEO variants. 

Each step needs to be executed separately, one after another. This means that 
for each step, other steps must be commented.

STEP 1: Export Base Mesh As USD (base mesh can be from scratch or edited from another variant)
STEP 2: Create a variant for the GEO variant set using the exported USD file
STEP 3: Duplicate the prim of a desired GEO variant (to make edits)

How to use: Details provided in each step, but it is important that each step 
is executed separately. This means that for each step, other steps must be commented.

Note: 
- If the location of imported files or this file changes, update the 
sys.path.append() above

-------------------------------------------------------------------------------

"""

# Global Variables
# INFO: These inputs should come from user
EXPORT_PATH = "/Users/natashadaas/USD_Switchboard/Test/cubeBaseMesh3.usd"
ROOT_PRIM = "myCubeMesh3"

#------------------------------------------
# STEP 1: Export Base Mesh As USD (base mesh can be from scratch or edited from another variant)
# Create base mesh, outside a USD stage
# Select the base mesh, set export_path, set rootPrim (above)
# Call exportBaseMeshAsUSD() to export base mesh as a USD file

ExportBaseMeshAsUSD.exportBaseMeshAsUSD(EXPORT_PATH,ROOT_PRIM)

#------------------------------------------
# STEP 2: Create a variant for the GEO variant set using the exported USD file
# Create a USD stage. Under the USD stage shape, create an XForm Prim
# Select the XForm Prim
# Call createGeoVariantFromUSDFile() to create a variant set "GEO", if it doesn't already exist
CreateGeoVariantFromUSDFile.createGeoVariantFromUSDFile(ROOT_PRIM, EXPORT_PATH)

#------------------------------------------
# STEP 3: Duplicate the prim of a desired GEO variant (to make edits)
# Call duplicateAsMayaData to duplicate maya data of the variant geo just added
DuplicateAsMayaData.duplicateAsMayaData()

#------------------------------------------
