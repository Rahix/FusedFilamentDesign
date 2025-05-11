import FreeCADGui
import FreeCAD

import ffDesign_Utils as Utils


class CounterboreBridgesCommand:
    def GetResources(self):
        return {
            # TODO: Update icon
            "Pixmap": Utils.Resources.get_icon("ffDesign_HoleWizard.svg"),
            "MenuText": FreeCAD.Qt.translate("ffDesign", "Add counterbore bridges"),
            "ToolTip": FreeCAD.Qt.translate(
                "ffDesign",
                "Add bridges to a counterbored Hole so it can be printed upside down.\n"
                "1. Select a Hole feature with a counterbore in the active body.\n"
                "2. Run this command.\n",
            ),
        }

    def Activated(self):
        hole = Utils.get_selected_hole()
        if hole is not None:
            Utils.Log.error("TODO: CounterboreBridgesCommand not yet implemented")

    def IsActive(self):
        return Utils.check_hole_tool_preconditions()


FreeCADGui.addCommand("ffDesign_CounterboreBridges", CounterboreBridgesCommand())
