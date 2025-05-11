import math

from PySide import QtCore, QtGui

import FreeCADGui as Gui
import FreeCAD as App
import Part
import Sketcher

import ffDesign_Utils as Utils


def make_parametric_teardrop(sketch, *, center_expr: str, diameter_expr: str, angle_expr: str, rotation_expr: str):
    Utils.assert_sketch(sketch)

    last_geo_id = len(sketch.Geometry)
    new_geo = [
        Part.ArcOfCircle(
            Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 1),
            math.pi / 4 * 3,
            math.pi / 4 * 1,
        ),
        Part.LineSegment(App.Vector(-1, 1, 0), App.Vector(0, 2, 0)),
        Part.LineSegment(App.Vector(1, 1, 0), App.Vector(0, 2, 0)),
        Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0, 2, 0)),
    ]
    sketch.addGeometry(new_geo, False)
    sketch.toggleConstruction(last_geo_id + 3)

    new_constraints = [
        Sketcher.Constraint("Coincident", last_geo_id + 1, 2, last_geo_id + 2, 2),
        Sketcher.Constraint("Coincident", last_geo_id + 1, 2, last_geo_id + 3, 2),
        Sketcher.Constraint("Coincident", last_geo_id + 0, 3, last_geo_id + 3, 1),
        Sketcher.Constraint("Tangent", last_geo_id + 0, 1, last_geo_id + 1, 1),
        Sketcher.Constraint("Tangent", last_geo_id + 0, 2, last_geo_id + 2, 1),
    ]
    sketch.addConstraint(new_constraints)

    last_c = len(sketch.Constraints)
    new_constraints = [
        Sketcher.Constraint("DistanceX", last_geo_id + 0, 3, 0),
        Sketcher.Constraint("DistanceY", last_geo_id + 0, 3, 0),
        Sketcher.Constraint("Diameter", last_geo_id + 0, 2),
        Sketcher.Constraint("Angle", last_geo_id + 1, 2, last_geo_id + 2, 2, math.pi / 2),
        Sketcher.Constraint("Angle", last_geo_id + 3, math.pi / 2),
    ]
    sketch.addConstraint(new_constraints)
    sketch.setExpression(f"Constraints[{last_c + 0}]", f"{center_expr}.x * 1mm")
    sketch.setExpression(f"Constraints[{last_c + 1}]", f"{center_expr}.y * 1mm")
    sketch.setExpression(f"Constraints[{last_c + 2}]", f"{diameter_expr}")
    sketch.setExpression(f"Constraints[{last_c + 3}]", f"{angle_expr}")
    sketch.setExpression(f"Constraints[{last_c + 4}]", f"{rotation_expr}")

    sketch.recompute()


def make_teardrops(body, hole, angle: App.Units.Quantity, rotation: App.Units.Quantity):
    Utils.assert_body(body)
    Utils.assert_hole(hole)

    angle = App.Units.Quantity(angle)
    assert angle.Unit.Type == "Angle"
    rotation = App.Units.Quantity(rotation)
    assert rotation.Unit.Type == "Angle"

    if "TeardropAngle" not in hole.PropertiesList:
        hole.addProperty("App::PropertyAngle", "TeardropAngle", group="FusedFilamentDesign")
    hole.TeardropAngle = angle

    if "TeardropRotation" not in hole.PropertiesList:
        hole.addProperty("App::PropertyAngle", "TeardropRotation", group="FusedFilamentDesign")
    hole.TeardropRotation = rotation

    profile_sketch = Utils.get_hole_profile_sketch(hole)
    teardrop_sketch = Utils.make_derived_sketch(body, profile_sketch, "_Teardrops")

    for index, circle in enumerate(profile_sketch.Geometry):
        if circle.TypeId != "Part::GeomCircle":
            continue

        make_parametric_teardrop(
            teardrop_sketch,
            center_expr=f"{profile_sketch.Name}.Geometry[{index}].Center",
            diameter_expr=f"{hole.Name}.Diameter",
            angle_expr=f"{hole.Name}.TeardropAngle",
            rotation_expr=f"{hole.Name}.TeardropRotation",
        )

    pocket = body.newObject("PartDesign::Pocket", f"{hole.Name}_Teardrops")
    pocket.Profile = (teardrop_sketch, "")
    pocket.ReferenceAxis = (teardrop_sketch, ["N_Axis"])
    pocket.Reversed = hole.Reversed
    teardrop_sketch.Visibility = False
    pocket.setExpression("Type", f"{hole.Name}.DepthType")
    pocket.setExpression("Length", f"{hole.Name}.Depth")
    pocket.Label = f"{hole.Label}_Teardrops"
    pocket.recompute()


class TeardropTaskPanel:
    def __init__(self, body, hole):
        Utils.assert_body(body)
        Utils.assert_hole(hole)

        self.body = body
        self.hole = hole
        self.form = Gui.PySideUic.loadUi(Utils.Resources.get_panel("ffDesign_Teardrop.ui"))

        # Default is 120° teardrop angle
        self.form.Angle120.toggle()

    def accept(self):
        try:
            angle = "120 deg"
            if self.form.Angle90.isChecked():
                angle = "90 deg"
            elif self.form.Angle120.isChecked():
                angle = "120 deg"

            Gui.Control.closeDialog()

            try:
                App.ActiveDocument.openTransaction("Add teardrop hole")
                make_teardrops(self.body, self.hole, angle=angle, rotation="90 deg")
                App.ActiveDocument.recompute()
            except Exception as e:
                App.ActiveDocument.abortTransaction()
                raise e from None
            else:
                App.ActiveDocument.commitTransaction()
        except Utils.ffDesignError:
            pass

    def reject(self):
        Gui.Control.closeDialog()


class TeardropCommand:
    def GetResources(self):
        return {
            "Pixmap": "icons:ffDesign_Teardrop.svg",
            "MenuText": App.Qt.translate("ffDesign", "Add teardrop shape"),
            "ToolTip": App.Qt.translate(
                "ffDesign",
                "Add a teardrop shape to a hole.\n"
                "1. Select a Hole feature with a counterbore in the active body.\n"
                "2. Run this command.\n",
            ),
        }

    def Activated(self):
        try:
            hole = Utils.get_selected_hole()
            body = Utils.get_active_part_design_body_for_feature(hole)

            dialog = TeardropTaskPanel(body, hole)
            Gui.Control.showDialog(dialog)
        except Utils.ffDesignError:
            pass

    def IsActive(self):
        return Utils.check_hole_tool_preconditions()


Gui.addCommand("ffDesign_Teardrop", TeardropCommand())
