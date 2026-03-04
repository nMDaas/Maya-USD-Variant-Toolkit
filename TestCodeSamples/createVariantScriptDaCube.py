import ufe
import mayaUsd.ufe
from pxr import Usd, UsdGeom

# Gets the selected USD prim in the outliner
def get_selected_usd_prim():
    # Get the current UFE (Universal Front End) selection made by user in outliner
    selection = ufe.GlobalSelection.get()

    if selection.empty():
        print("Nothing selected.")
        return None
    
    # Get last item in the selection
    selected_item = list(selection)[-1]

    # Convert UFE path object to a string path
    ufe_path_obj = selected_item.path()
    ufe_path_string = ufe.PathString.string(ufe_path_obj)

    # Access prim via string path
    prim = mayaUsd.ufe.ufePathToPrim(ufe_path_string)
    
    # Ensure prim is an Xform
    if (not prim.IsA(UsdGeom.Xform)):
        print("XForm prim must be selected for variant set creation.")

    return prim

# Creates a variant set of a given name for a given XForm
def createVariantSet(Xf_selected, in_vset_name):
    vset = Xf_selected.GetVariantSets().AddVariantSet(in_vset_name)
    return vset

# Currently kind of a "dummy" implementation - num is to create spheres of different radii
def createVariantForSet(Xf_prim, vset, variant_name, file_path):
    vset.AddVariant(variant_name)

    vset.SetVariantSelection(variant_name)

    # Go inside the variant and add the file reference
    with vset.GetVariantEditContext():
        Xf_prim.GetReferences().AddReference(file_path)
    
    print(f"Variant '{variant_name}' authored with reference to: {file_path}")

# Get Xform selected
Xf_selected = get_selected_usd_prim()
Xf_path = Xf_selected.GetPath() # this is the path that is preceded by '/', so not the ufe path

# Create a variant set for the XForm prim selected
# INFO: The variant set name should come from the user 
vset = createVariantSet(Xf_selected, "ColorVariantSet")
vset2 = createVariantSet(Xf_selected, "SizeVariantSet")

# INFO: variant names should come from the user
# INFO: variant content should also come from the user (for now, file)
# Using test data from TestData/daCube - it is important the way these files are structured because property that is being changed in one variant cannot be in the other
createVariantForSet(Xf_selected, vset, "vs_color_pink", "/Users/natashadaas/USD_Switchboard/TestData/daCube/ColorVariantSet/daCubePink.usda")
createVariantForSet(Xf_selected, vset, "vs_color_blue", "/Users/natashadaas/USD_Switchboard/TestData/daCube/ColorVariantSet/daCubeBlue.usda")
createVariantForSet(Xf_selected, vset2, "vs_size_small", "/Users/natashadaas/USD_Switchboard/TestData/daCube/SizeVariantSet/daCubeSmall.usda")
createVariantForSet(Xf_selected, vset2, "vs_size_big", "/Users/natashadaas/USD_Switchboard/TestData/daCube/SizeVariantSet/daCubeBig.usda")
