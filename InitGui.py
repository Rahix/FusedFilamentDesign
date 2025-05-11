import FreeCAD
import FreeCADGui

import ffDesign_HoleWizard
import ffDesign_CounterboreBridges
import ffDesign_RibThreads
import ffDesign_Teardrop
import ffDesign_ZipTieChannels


def register_pd_toolbar():
    import ffDesign_Utils as Utils

    """Register the PrintDesign toolbar in the PartDesign workbench."""
    pd_toolbars = FreeCAD.ParamGet("User parameter:BaseApp/Workbench/PartDesignWorkbench/Toolbar")

    # all_bars = pd_toolbars.GetGroups()
    # Utils.Log.info(f"All PartDesign Toolbars: {all_bars!r}")

    for tb_name in pd_toolbars.GetGroups():
        if pd_toolbars.GetGroup(tb_name).GetString("Name") == "FusedFilamentDesign":
            break
    else:
        Utils.Log.info(f"Registering {Utils.Log.addon} toolbar into PartDesign workbench...")

        # Create the FusedFilamentDesign toolbar
        ff_toolbar = pd_toolbars.GetGroup("ffDesign")
        ff_toolbar.SetString("Name", "FusedFilamentDesign")

        # Commands to be added:
        ff_toolbar.SetString("ffDesign_HoleWizard", "ffDesign")

        ff_toolbar.SetBool("Active", 1)


register_pd_toolbar()
