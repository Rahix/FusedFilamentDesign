import FreeCAD
import FreeCADGui

import ffDesign_HoleWizard


def register_pd_toolbar():
    """Register the PrintDesign toolbar in the PartDesign workbench."""
    pd_toolbars = FreeCAD.ParamGet("User parameter:BaseApp/Workbench/PartDesignWorkbench/Toolbar")
    all_bars = pd_toolbars.GetGroups()
    print(f"[ffDesign] All PartDesign Toolbars: {all_bars!r}")

    for tb_name in pd_toolbars.GetGroups():
        if pd_toolbars.GetGroup(tb_name).GetString("Name") == "FusedFilamentDesign":
            break
    else:
        # Create the FusedFilamentDesign toolbar
        ff_toolbar = pd_toolbars.GetGroup("ffDesign")
        ff_toolbar.SetString("Name", "FusedFilamentDesign")
        # Commands to be added:
        ff_toolbar.SetString("ffDesign_HoleWizard", "ffDesign")
        ff_toolbar.SetString("Separator1", "Separator")
        ff_toolbar.SetString("Part_Boolean", "Part")
        ff_toolbar.SetBool("Active", 1)


register_pd_toolbar()
