import math

import FreeCADGui as Gui
import FreeCAD as App
import Part
import Sketcher

import ffDesign_Utils as Utils


class RibThreadsCommand:
    def GetResources(self):
        return {
            "Pixmap": "icons:ffDesign_RibThreads.svg",
            "MenuText": App.Qt.translate("ffDesign", "Add thread forming ribs"),
            "ToolTip": App.Qt.translate(
                "ffDesign",
                "Add ribs to a hole that allow a screw to form its own thread.\n"
                "1. Select a Hole feature with a counterbore in the active body.\n"
                "2. Run this command.\n",
            ),
        }

    def Activated(self):
        try:
            hole = Utils.get_selected_hole()
            body = Utils.get_active_part_design_body_for_feature(hole)

            try:
                App.ActiveDocument.openTransaction("Add counterbores bridges")
                raise Utils.ffDesignError("Not implemented yet")
            except Exception as e:
                App.ActiveDocument.abortTransaction()
                raise e from None
            else:
                App.ActiveDocument.commitTransaction()
        except Utils.ffDesignError:
            pass

    def IsActive(self):
        return Utils.check_hole_tool_preconditions()


Gui.addCommand("ffDesign_RibThreads", RibThreadsCommand())
