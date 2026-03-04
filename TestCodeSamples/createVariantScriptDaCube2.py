import ufe
import mayaUsd.ufe
from pxr import Usd, UsdGeom, Gf

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

def createVariantSet(Xf_selected, in_vset_name):
    return Xf_selected.GetVariantSets().AddVariantSet(in_vset_name)

def createColorVariant(Xf_prim, vset, variant_name, color_rgb):
    vset.AddVariant(variant_name)
    vset.SetVariantSelection(variant_name)

    # Assuming the mesh under XForm is called CubeMesh
    child_prim = Xf_prim.GetChild("CubeMesh") 
    
    if not child_prim:
        print(f"Error: No child named 'CubeMesh' found under {Xf_prim.GetPath()}")
        return

    with vset.GetVariantEditContext():
        mesh_geom = UsdGeom.Gprim(child_prim)
        color_attr = mesh_geom.CreateDisplayColorAttr()
        
        color_attr.Set([Gf.Vec3f(*color_rgb)])
    
    print(f"Variant '{variant_name}' authored with color: {color_rgb}")

def createSizeVariantSet(Xf_prim, vset, variant_name, scale_xyz):
    vset.AddVariant(variant_name)
    vset.SetVariantSelection(variant_name)

    # Assuming the mesh under XForm is called CubeMesh
    child_prim = Xf_prim.GetChild("CubeMesh") 
    
    if not child_prim:
        print(f"Error: No child named 'CubeMesh' found under {Xf_prim.GetPath()}")
        return

    with vset.GetVariantEditContext():
        mesh_geom = UsdGeom.Gprim(child_prim)
        scale_attr = mesh_geom.AddScaleOp()
        
        scale_attr.Set(Gf.Vec3f(*scale_xyz))
    
    print(f"Variant '{variant_name}' authored with size: {scale_xyz}")

Xf_selected = get_selected_usd_prim()

if Xf_selected:
    # Create the variant sets
    vset = createVariantSet(Xf_selected, "ColorVariantSet")
    vset2 = createVariantSet(Xf_selected, "SizeVariantSet")
 
    # Author variants 
    createColorVariant(Xf_selected, vset, "Pink", (1.0, 0.4, 0.7))
    createColorVariant(Xf_selected, vset, "Blue", (0.2, 0.5, 1.0))
    createColorVariant(Xf_selected, vset, "Green", (0.3, 0.8, 0.3))

    createSizeVariantSet(Xf_selected, vset2, "Small", (0.5, 0.5, 0.5))
    createSizeVariantSet(Xf_selected, vset2, "Big", (2.0, 2.0, 2.0))