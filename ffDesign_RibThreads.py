import math
from dataclasses import dataclass

import FreeCADGui as Gui
import FreeCAD as App
import Part
import Sketcher

import ffDesign_Utils as Utils


@dataclass
class RibParameters:
    # Thread General
    name: str
    normative: float
    core_diameter: float
    core_bore: float

    # Rib Specific
    entrance_depth: float
    outer_diameter: float
    rib_engagement: float
    rib_diameter: float


# Following are a bunch of known-okay default parameters for certain thread
# sizes.  These will be suggested to a user when they try to generate ribs for
# the respective thread size.
#
# If you have run more experiments with other thread sizes, feel free to
# contribute more default parameter sets.

# fmt: off
RIB_PARAMETERS = {
    "M3": RibParameters(name="M3", normative=3, core_diameter=2.39, core_bore=2.5, entrance_depth=0.6, outer_diameter=3.4, rib_engagement=0.2, rib_diameter=1.4),
    "M4": RibParameters(name="M4", normative=4, core_diameter=3.14, core_bore=3.3, entrance_depth=0.8, outer_diameter=4.4, rib_engagement=0.3, rib_diameter=1.6),
    "M5": RibParameters(name="M5", normative=5, core_diameter=4.02, core_bore=4.2, entrance_depth=1.0, outer_diameter=5.4, rib_engagement=0.4, rib_diameter=2.0),
    "M6": RibParameters(name="M6", normative=6, core_diameter=4.77, core_bore=5.0, entrance_depth=1.2, outer_diameter=6.4, rib_engagement=0.5, rib_diameter=2.2),
    "M8": RibParameters(name="M8", normative=8, core_diameter=6.47, core_bore=6.8, entrance_depth=1.4, outer_diameter=8.5, rib_engagement=0.5, rib_diameter=2.6),
}
# fmt: on

# Aliases for newer FreeCAD versions
RIB_PARAMETERS["M3x0.5"] = RIB_PARAMETERS["M3"]
RIB_PARAMETERS["M4x0.7"] = RIB_PARAMETERS["M4"]
RIB_PARAMETERS["M5x0.8"] = RIB_PARAMETERS["M5"]
RIB_PARAMETERS["M6x1.0"] = RIB_PARAMETERS["M6"]
RIB_PARAMETERS["M6x1"] = RIB_PARAMETERS["M6"]
RIB_PARAMETERS["M8x1.25"] = RIB_PARAMETERS["M8"]


def make_parametric_circle(sketch, center_expr: str, size_expr: str):
    Utils.assert_sketch(sketch)

    last_geo_id = len(sketch.Geometry)
    new_geo = [
        Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 2),
    ]
    sketch.addGeometry(new_geo, False)
    last_c = len(sketch.Constraints)
    new_constraints = [
        Sketcher.Constraint("DistanceX", last_geo_id + 0, 3, 0),
        Sketcher.Constraint("DistanceY", last_geo_id + 0, 3, 0),
        Sketcher.Constraint("Diameter", last_geo_id + 0, 2),
    ]
    sketch.addConstraint(new_constraints)
    sketch.setExpression(f"Constraints[{last_c + 0}]", f"{center_expr}.x * 1mm")
    sketch.setExpression(f"Constraints[{last_c + 1}]", f"{center_expr}.y * 1mm")
    sketch.setExpression(f"Constraints[{last_c + 2}]", f"{size_expr}")
    sketch.recompute()


class RibThreadsTaskPanel:
    def __init__(self, body, hole):
        Utils.assert_body(body)
        Utils.assert_hole(hole)

        self.body = body
        self.hole = hole
        self.form = Gui.PySideUic.loadUi(Utils.Resources.get_panel("ffDesign_RibThreads.ui"))

        self.form.InfoMessage.setText("Creating a new rib template sketch...")

        self.form.ThreadNormative.setText(str(self.hole.ThreadSize))
        self.form.ThreadNormative.setEnabled(False)

        if self.hole.ThreadSize in RIB_PARAMETERS:
            rib_param = RIB_PARAMETERS[self.hole.ThreadSize]

            self.form.ThreadCore.setProperty("rawValue", rib_param.core_bore)
            self.form.ThreadCore.setEnabled(False)

            self.form.EntranceDepth.setProperty("rawValue", rib_param.entrance_depth)
            self.form.OuterDiameter.setProperty("rawValue", rib_param.outer_diameter)
            self.form.RibEngagement.setProperty("rawValue", rib_param.rib_engagement)
            self.form.RibDiameter.setProperty("rawValue", rib_param.rib_diameter)

    def accept(self):
        Gui.Control.closeDialog()

    def reject(self):
        Gui.Control.closeDialog()


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

            dialog = RibThreadsTaskPanel(body, hole)
            Gui.Control.showDialog(dialog)

            # try:
            #     App.ActiveDocument.openTransaction("Add counterbores bridges")
            #     raise Utils.ffDesignError("Not implemented yet")
            # except Exception as e:
            #     App.ActiveDocument.abortTransaction()
            #     raise e from None
            # else:
            #     App.ActiveDocument.commitTransaction()
        except Utils.ffDesignError:
            pass

    def IsActive(self):
        return Utils.check_hole_tool_preconditions()


Gui.addCommand("ffDesign_RibThreads", RibThreadsCommand())
