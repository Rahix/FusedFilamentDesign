import math

from PySide import QtCore, QtGui

import FreeCADGui as Gui
import FreeCAD as App
import Part
import Sketcher

import ffDesign_Utils as Utils


def make_parametric_roof_bridge(
    sketch, *, center_expr: str, diameter_expr: str, angle_expr: str, rotation_expr: str, clearance_expr: str
):
    Utils.assert_sketch(sketch)

    last_geo_id = len(sketch.Geometry)
    new_geo = [
        Part.ArcOfCircle(
            Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 1),
            math.pi / 4 * 3,
            math.pi / 4 * 1,
        ),
        Part.LineSegment(App.Vector(-1, 1, 0), App.Vector(-0.5, 2, 0)),
        Part.LineSegment(App.Vector(1, 1, 0), App.Vector(0.5, 2, 0)),
        Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0, 2, 0)),
        Part.LineSegment(App.Vector(-0.5, 2, 0), App.Vector(0.5, 2, 0)),
    ]
    sketch.addGeometry(new_geo, False)
    sketch.toggleConstruction(last_geo_id + 3)

    new_constraints = [
        Sketcher.Constraint("Coincident", last_geo_id + 1, 2, last_geo_id + 4, 1),
        Sketcher.Constraint("Coincident", last_geo_id + 2, 2, last_geo_id + 4, 2),
        Sketcher.Constraint("Coincident", last_geo_id + 0, 3, last_geo_id + 3, 1),
        Sketcher.Constraint("Tangent", last_geo_id + 0, 1, last_geo_id + 1, 1),
        Sketcher.Constraint("Tangent", last_geo_id + 0, 2, last_geo_id + 2, 1),
        Sketcher.Constraint("Symmetric", last_geo_id + 4, 1, last_geo_id + 4, 2, last_geo_id + 3, 2),
        Sketcher.Constraint("Perpendicular", last_geo_id + 4, last_geo_id + 3),
    ]
    sketch.addConstraint(new_constraints)

    last_c = len(sketch.Constraints)
    new_constraints = [
        Sketcher.Constraint("DistanceX", last_geo_id + 0, 3, 0),
        Sketcher.Constraint("DistanceY", last_geo_id + 0, 3, 0),
        Sketcher.Constraint("Diameter", last_geo_id + 0, 2),
        Sketcher.Constraint("Angle", last_geo_id + 1, 2, last_geo_id + 2, 2, math.pi / 2),
        Sketcher.Constraint("Angle", last_geo_id + 3, math.pi / 2),
        Sketcher.Constraint("Distance", last_geo_id + 3, 1, last_geo_id + 3, 2, 2),
    ]
    sketch.addConstraint(new_constraints)
    sketch.setExpression(f"Constraints[{last_c + 0}]", f"{center_expr}.x * 1mm")
    sketch.setExpression(f"Constraints[{last_c + 1}]", f"{center_expr}.y * 1mm")
    sketch.setExpression(f"Constraints[{last_c + 2}]", f"{diameter_expr}")
    sketch.setExpression(f"Constraints[{last_c + 3}]", f"{angle_expr} * 2")
    sketch.setExpression(f"Constraints[{last_c + 4}]", f"{rotation_expr}")
    sketch.setExpression(f"Constraints[{last_c + 5}]", f"{diameter_expr} / 2 + {clearance_expr}")

    sketch.recompute()


def make_roof_bridges(
    body,
    hole,
    *,
    angle: App.Units.Quantity,
    rotation: App.Units.Quantity,
    do_counterbore: bool,
    bridge_clearance: App.Units.Quantity,
):
    Utils.assert_body(body)
    Utils.assert_hole(hole)

    angle = App.Units.Quantity(angle)
    assert angle.Unit.Type == "Angle"
    rotation = App.Units.Quantity(rotation)
    assert rotation.Unit.Type == "Angle"
    bridge_clearance = App.Units.Quantity(bridge_clearance)
    assert bridge_clearance.Unit.Type == "Length"

    if "RoofBridgeOverhangAngle" not in hole.PropertiesList:
        hole.addProperty("App::PropertyAngle", "RoofBridgeOverhangAngle", group="FusedFilamentDesign")
    hole.RoofBridgeOverhangAngle = angle

    if "RoofBridgeRotation" not in hole.PropertiesList:
        hole.addProperty("App::PropertyAngle", "RoofBridgeRotation", group="FusedFilamentDesign")
    hole.RoofBridgeRotation = rotation

    if "RoofBridgeClearance" not in hole.PropertiesList:
        hole.addProperty("App::PropertyLength", "RoofBridgeClearance", group="FusedFilamentDesign")
    hole.RoofBridgeClearance = bridge_clearance

    profile_sketch = Utils.get_hole_profile_sketch(hole)
    roofbridge_sketch = Utils.make_derived_sketch(body, profile_sketch, "_RoofBridge")

    for index in Utils.get_sketch_circle_indices(profile_sketch):
        make_parametric_roof_bridge(
            roofbridge_sketch,
            center_expr=f"{profile_sketch.Name}.Geometry[{index}].Center",
            diameter_expr=f"{hole.Name}.Diameter",
            angle_expr=f"{hole.Name}.RoofBridgeOverhangAngle",
            rotation_expr=f"{hole.Name}.RoofBridgeRotation",
            clearance_expr=f"{hole.Name}.RoofBridgeClearance",
        )

    pocket = body.newObject("PartDesign::Pocket", f"{hole.Name}_RoofBridge")
    pocket.Profile = (roofbridge_sketch, "")
    pocket.ReferenceAxis = (roofbridge_sketch, ["N_Axis"])
    pocket.Reversed = hole.Reversed
    roofbridge_sketch.Visibility = False
    pocket.setExpression("Type", f"{hole.Name}.DepthType")
    pocket.setExpression("Length", f"{hole.Name}.Depth")
    pocket.Label = f"{hole.Label}_RoofBridge"
    pocket.recompute()

    if not do_counterbore or not Utils.hole_has_counterbore_maybe(hole):
        return

    roofbridge_cb_sketch = Utils.make_derived_sketch(body, profile_sketch, "_RoofBridgeCb")

    for index in Utils.get_sketch_circle_indices(profile_sketch):
        make_parametric_roof_bridge(
            roofbridge_cb_sketch,
            center_expr=f"{profile_sketch.Name}.Geometry[{index}].Center",
            diameter_expr=f"{hole.Name}.HoleCutDiameter",
            angle_expr=f"{hole.Name}.RoofBridgeOverhangAngle",
            rotation_expr=f"{hole.Name}.RoofBridgeRotation",
            clearance_expr=f"{hole.Name}.RoofBridgeClearance",
        )

    pocket = body.newObject("PartDesign::Pocket", f"{hole.Name}_RoofBridgeCb")
    pocket.Profile = (roofbridge_cb_sketch, "")
    pocket.ReferenceAxis = (roofbridge_cb_sketch, ["N_Axis"])
    pocket.Reversed = hole.Reversed
    roofbridge_cb_sketch.Visibility = False
    pocket.setExpression("Length", f"{hole.Name}.HoleCutDepth")
    pocket.Label = f"{hole.Label}_RoofBridgeCb"
    pocket.recompute()


class RoofBridgeTaskPanel:
    def __init__(self, body, hole):
        Utils.assert_body(body)
        Utils.assert_hole(hole)

        self.body = body
        self.hole = hole
        self.form = Gui.PySideUic.loadUi(Utils.Resources.get_panel("ffDesign_RoofBridge.ui"))

        has_counterbore = Utils.hole_has_counterbore_maybe(hole)
        self.form.DoCounterbore.setEnabled(has_counterbore)

        if Utils.hole_has_counterbore_sure(hole):
            self.form.DoCounterbore.setCheckState(QtCore.Qt.CheckState.Checked)

        self.form.BridgeClearance.setProperty("rawValue", 0.2)

        # Default is 45° overhang angle
        self.form.Angle45.toggle()

    def accept(self):
        try:
            angle = "45 deg"
            if self.form.Angle45.isChecked():
                angle = "45 deg"
            elif self.form.Angle60.isChecked():
                angle = "60 deg"

            do_counterbore = self.form.DoCounterbore.checkState() == QtCore.Qt.CheckState.Checked
            bridge_clearance = self.form.BridgeClearance.property("value")

            Gui.Control.closeDialog()

            try:
                App.ActiveDocument.openTransaction("Add roof bridge")
                make_roof_bridges(
                    self.body,
                    self.hole,
                    angle=angle,
                    rotation="90 deg",
                    do_counterbore=do_counterbore,
                    bridge_clearance=bridge_clearance,
                )
                App.ActiveDocument.recompute()
            except Exception as e:
                App.ActiveDocument.abortTransaction()
                raise e from None
            else:
                App.ActiveDocument.commitTransaction()
        except Utils.ffDesignError as e:
            e.emit_to_user()

    def reject(self):
        Gui.Control.closeDialog()


class RoofBridgeCommand:
    def GetResources(self):
        return {
            "Pixmap": "icons:ffDesign_RoofBridge.svg",
            "MenuText": App.Qt.translate("ffDesign", "Add roof bridge"),
            "ToolTip": App.Qt.translate(
                "ffDesign",
                "Add a roof bridge to a hole to avoid a steep overhang.\n"
                "1. Select a Hole feature in the active body.\n"
                "2. Run this command.\n",
            ),
        }

    def Activated(self):
        try:
            hole = Utils.get_selected_hole()
            body = Utils.get_active_part_design_body_for_feature(hole)

            dialog = RoofBridgeTaskPanel(body, hole)
            Gui.Control.showDialog(dialog)
        except Utils.ffDesignError as e:
            e.emit_to_user()

    def IsActive(self):
        return Utils.check_hole_tool_preconditions()


Gui.addCommand("ffDesign_RoofBridge", RoofBridgeCommand())
