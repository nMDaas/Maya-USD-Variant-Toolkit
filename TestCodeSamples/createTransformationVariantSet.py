import ufe
import mayaUsd.ufe
from pxr import Usd, UsdGeom, Gf

"""
----------------------------------------------------------------------
This is for creating a transformation variant set for an Xform

How to use: 
1. Select the XForm under which the prim exists
2. With the Xform selected, move it to a desired position
3. Set the variant set name and variant name
4. Run the script
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

def apply_permanent_order(prim):
    attr = prim.GetAttribute("xformOpOrder")
    if attr.HasValue():
        print(f"Prim already has attribute")
        return
    
    else:
        stage = prim.GetStage()
        
        target_layer = stage.GetRootLayer()

        with Usd.EditContext(stage, target_layer):
            xformable = UsdGeom.Xformable(prim)

            tOp = xformable.AddTranslateOp()
            rOp = xformable.AddRotateXYZOp()
            sOp = xformable.AddScaleOp()

            xformable.SetXformOpOrder([tOp, rOp, sOp])
            
        print(f"Authored xformOpOrder to layer: {target_layer.identifier}")

def createVariantSet(Xf_selected, in_vset_name):
    print(f"Created Variant Set: {in_vset_name} for {Xf_selected}")
    return Xf_selected.GetVariantSets().AddVariantSet(in_vset_name)

def createATransformationVariantSet(Xf_prim, vset, variant_name):
    # Get the manual overrides currently on the prim
    recorded_values = {}
    attrs_to_clear = []
    
    for attr in Xf_prim.GetAttributes():
        if attr.IsAuthored() and attr.Get() is not None:
            attr_name = attr.GetName()
            recorded_values[attr_name] = attr.Get()
            attrs_to_clear.append(attr)

    # Create/select the new variant and author the values
    vset.AddVariant(variant_name)
    vset.SetVariantSelection(variant_name)

    with vset.GetVariantEditContext():
        for attr_name, val in recorded_values.items():            
            attr = Xf_prim.GetAttribute(attr_name)
            attr.Set(val)

    # Clear the top-level overrides so the variant can take over
    for attr in attrs_to_clear:
        attr.Clear()

    vset.SetVariantSelection("") 
        
    print(f"Recorded variant '{variant_name}' and cleared top-level overrides.")

Xf_selected = get_selected_usd_prim()

if Xf_selected:

    # Create the variant sets
    vset = createVariantSet(Xf_selected, "SizeVariantSet")
    createATransformationVariantSet(Xf_selected, vset, "Default")

    apply_permanent_order(Xf_selected)


#----------------------------------------------------------------------------------------------------------------