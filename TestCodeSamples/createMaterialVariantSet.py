import ufe
import mayaUsd.ufe
from pxr import Usd, UsdGeom, Gf, UsdShade, Sdf

"""
----------------------------------------------------------------------
This is for creating a material variant set for an Xform

How to use: 
1. Assign XForm to desired material via Assign Material
2. Set material_path, variant set name and variant name (manually)
3. With XForm selected, run this script
----------------------------------------------------------------------

"""

def get_selected_usd_prim():
    selection = ufe.GlobalSelection.get()
    if selection.empty():
        print("Nothing selected.")
        return None
    
    selected_item = list(selection)[-1]
    ufe_path_string = ufe.PathString.string(selected_item.path())
    prim = mayaUsd.ufe.ufePathToPrim(ufe_path_string)
    
    if (not prim.IsA(UsdGeom.Xform)):
        print("XForm prim must be selected.")
        return None
    return prim

def reset_binding(xform_prim):
    rel = xform_prim.GetRelationship("material:binding")
    
    if rel:
        if rel.HasAuthoredTargets():
            print("Clearing materal:binding relationships...")
            rel.ClearTargets(True) 
        else:
            print("Relationship exists but is already empty.")

def createVariantSet(Xf_selected, in_vset_name):
    print(f"Created Variant Set: {in_vset_name} for {Xf_selected}")
    return Xf_selected.GetVariantSets().AddVariantSet(in_vset_name)

def createAMaterialVariantSet(Xf_prim, vset, variant_name):
    # Create/select the new variant and author the values
    vset.AddVariant(variant_name)
    vset.SetVariantSelection(variant_name)
    

    proxy_shape_path = "|stage1|stageShape1"
    stage = mayaUsd.ufe.getStage(proxy_shape_path)

    with vset.GetVariantEditContext():
        binding_api = UsdShade.MaterialBindingAPI.Apply(Xf_prim)
        # INFO: The material should be set by the user
        material_path = Sdf.Path('/mtl/UsdPreviewSurface1')
        
        # Create the relationship pointing to your material
        binding_api.Bind(UsdShade.Material.Get(stage, material_path))

Xf_selected = get_selected_usd_prim()

if Xf_selected:

    # Create the variant sets
    # INFO: Variant set name and variant name should come from user
    vset = createVariantSet(Xf_selected, "CubeMat")
    createAMaterialVariantSet(Xf_selected, vset, "Blue")

    reset_binding(Xf_selected)


#----------------------------------------------------------------------------------------------------------------