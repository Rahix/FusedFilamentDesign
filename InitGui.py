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

    PD_TOOLBAR_COMMANDS = ["ffDesign_About", "ffDesign_HoleWizard", "ffDesign_ZipTieChannels"]

    for tb_name in pd_toolbars.GetGroups():
        tb = pd_toolbars.GetGroup(tb_name)
        if tb.GetString("Name") == "FusedFilamentDesign":
            # Install any new commands that we now provide into the existing toolbar
            missing = [cmd for cmd in PD_TOOLBAR_COMMANDS if tb.GetString(cmd) == ""]
            if len(missing) > 0:
                Utils.Log.info(f"Updating toolbar to include new {', '.join(missing)} as well!")

                # First remove them all
                for s in tb.GetStrings():
                    if s not in ["Active", "Name"]:
                        tb.RemString(s)

                # Then add them back
                for cmd in PD_TOOLBAR_COMMANDS:
                    tb.SetString(cmd, "ffDesign")

            break
    else:
        Utils.Log.info(f"Registering toolbar into PartDesign workbench...")

        # Create the FusedFilamentDesign toolbar
        ff_toolbar = pd_toolbars.GetGroup("ffDesign")
        ff_toolbar.SetString("Name", "FusedFilamentDesign")

        # Commands to be added:
        for cmd in PD_TOOLBAR_COMMANDS:
            ff_toolbar.SetString(cmd, "ffDesign")

        ff_toolbar.SetBool("Active", 1)


register_pd_toolbar()
