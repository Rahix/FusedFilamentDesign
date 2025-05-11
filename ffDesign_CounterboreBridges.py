import math

import FreeCADGui as Gui
import FreeCAD as App
import Part
import Sketcher

import ffDesign_Utils as Utils


LAYER_HEIGHT = "0.2 mm"


def make_parametric_square(sketch, center_expr: str, size_expr: str):
    Utils.assert_sketch(sketch)

    last_geo_id = len(sketch.Geometry)
    new_geo = [
        Part.LineSegment(App.Vector(-1, 1, 0), App.Vector(1, 1, 0)),
        Part.LineSegment(App.Vector(1, 1, 0), App.Vector(1, -1, 0)),
        Part.LineSegment(App.Vector(1, -1, 0), App.Vector(-1, -1, 0)),
        Part.LineSegment(App.Vector(-1, -1, 0), App.Vector(-1, 1, 0)),
    ]
    sketch.addGeometry(new_geo, False)
    new_constraints = [
        Sketcher.Constraint("Coincident", last_geo_id + 0, 2, last_geo_id + 1, 1),
        Sketcher.Constraint("Coincident", last_geo_id + 1, 2, last_geo_id + 2, 1),
        Sketcher.Constraint("Coincident", last_geo_id + 2, 2, last_geo_id + 3, 1),
        Sketcher.Constraint("Coincident", last_geo_id + 3, 2, last_geo_id + 0, 1),
        Sketcher.Constraint("Horizontal", last_geo_id + 0),
        Sketcher.Constraint("Horizontal", last_geo_id + 2),
        Sketcher.Constraint("Vertical", last_geo_id + 1),
        Sketcher.Constraint("Vertical", last_geo_id + 3),
    ]
    sketch.addConstraint(new_constraints)
    last_c = len(sketch.Constraints)
    new_constraints = [
        Sketcher.Constraint("DistanceX", last_geo_id + 0, 1, -1),
        Sketcher.Constraint("DistanceY", last_geo_id + 0, 1, 1),
        Sketcher.Constraint("DistanceX", last_geo_id + 2, 1, 1),
        Sketcher.Constraint("DistanceY", last_geo_id + 2, 1, -1),
    ]
    sketch.addConstraint(new_constraints)
    sketch.setExpression(f"Constraints[{last_c + 0}]", f"{center_expr}.x * 1mm - {size_expr} / 2")
    sketch.setExpression(f"Constraints[{last_c + 1}]", f"{center_expr}.y * 1mm + {size_expr} / 2")
    sketch.setExpression(f"Constraints[{last_c + 2}]", f"{center_expr}.x * 1mm + {size_expr} / 2")
    sketch.setExpression(f"Constraints[{last_c + 3}]", f"{center_expr}.y * 1mm - {size_expr} / 2")
    sketch.recompute()


def make_parametric_y_cutout(sketch, center_expr: str, size_inner_expr: str, size_outer_expr: str):
    Utils.assert_sketch(sketch)

    last_geo_id = len(sketch.Geometry)
    new_geo = [
        Part.ArcOfCircle(
            Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 1),
            math.pi / 4 * 1,
            math.pi / 4 * 3,
        ),
        Part.ArcOfCircle(
            Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 1),
            math.pi / 4 * 5,
            math.pi / 4 * 7,
        ),
        Part.LineSegment(App.Vector(-1, 1, 0), App.Vector(-1, -1, 0)),
        Part.LineSegment(App.Vector(1, 1, 0), App.Vector(1, -1, 0)),
    ]
    sketch.addGeometry(new_geo, False)
    new_constraints = [
        Sketcher.Constraint("Coincident", last_geo_id + 0, 1, last_geo_id + 3, 1),
        Sketcher.Constraint("Coincident", last_geo_id + 0, 2, last_geo_id + 2, 1),
        Sketcher.Constraint("Coincident", last_geo_id + 1, 1, last_geo_id + 2, 2),
        Sketcher.Constraint("Coincident", last_geo_id + 1, 2, last_geo_id + 3, 2),
    ]
    sketch.addConstraint(new_constraints)
    last_c = len(sketch.Constraints)
    new_constraints = [
        Sketcher.Constraint("DistanceX", last_geo_id + 0, 1, 1),
        Sketcher.Constraint("DistanceX", last_geo_id + 1, 1, 1),
        Sketcher.Constraint("DistanceX", last_geo_id + 0, 2, 1),
        Sketcher.Constraint("DistanceX", last_geo_id + 1, 2, 1),
        Sketcher.Constraint("DistanceY", last_geo_id + 0, 1, 1),
        Sketcher.Constraint("DistanceY", last_geo_id + 0, 2, 1),
        Sketcher.Constraint("DistanceY", last_geo_id + 1, 1, -1),
        Sketcher.Constraint("DistanceY", last_geo_id + 1, 2, -1),
        Sketcher.Constraint("DistanceY", last_geo_id + 0, 3, 0),
        Sketcher.Constraint("DistanceY", last_geo_id + 1, 3, 0),
    ]
    sketch.addConstraint(new_constraints)
    y_offset_expr = f"sqrt(({size_outer_expr} / 2)^2 - ({size_inner_expr} / 2)^2)"
    sketch.setExpression(f"Constraints[{last_c + 0}]", f"{center_expr}.x * 1mm + {size_inner_expr} / 2")
    sketch.setExpression(f"Constraints[{last_c + 1}]", f"{center_expr}.x * 1mm - {size_inner_expr} / 2")
    sketch.setExpression(f"Constraints[{last_c + 2}]", f"{center_expr}.x * 1mm - {size_inner_expr} / 2")
    sketch.setExpression(f"Constraints[{last_c + 3}]", f"{center_expr}.x * 1mm + {size_inner_expr} / 2")
    sketch.setExpression(f"Constraints[{last_c + 4}]", f"{center_expr}.y * 1mm + {y_offset_expr}")
    sketch.setExpression(f"Constraints[{last_c + 5}]", f"{center_expr}.y * 1mm + {y_offset_expr}")
    sketch.setExpression(f"Constraints[{last_c + 6}]", f"{center_expr}.y * 1mm - {y_offset_expr}")
    sketch.setExpression(f"Constraints[{last_c + 7}]", f"{center_expr}.y * 1mm - {y_offset_expr}")
    sketch.setExpression(f"Constraints[{last_c + 8}]", f"{center_expr}.y")
    sketch.setExpression(f"Constraints[{last_c + 9}]", f"{center_expr}.y")
    sketch.recompute()


def make_upside_down_counterbores(body, hole):
    Utils.assert_body(body)
    Utils.assert_hole(hole)

    if not Utils.hole_has_counterbore_sure(hole):
        Utils.warning_confirm_proceed("Selected Hole does not seem to have a known counterbore type.")

    profile_sketch = Utils.get_hole_profile_sketch(hole)

    sketch_bridges_y = Utils.make_derived_sketch(body, profile_sketch, "_BridgesY")
    sketch_bridges_x = Utils.make_derived_sketch(body, profile_sketch, "_BridgesX")

    for index, circle in enumerate(profile_sketch.Geometry):
        if circle.TypeId != "Part::GeomCircle":
            continue

        # Create parametric y bridges cutout for this circle
        make_parametric_y_cutout(
            sketch_bridges_y,
            f"{profile_sketch.Name}.Geometry[{index}].Center",
            f"{hole.Name}.Diameter",
            f"{hole.Name}.HoleCutDiameter",
        )

        # Create parametric x bridges cutout for this circle
        make_parametric_square(
            sketch_bridges_x,
            f"{profile_sketch.Name}.Geometry[{index}].Center",
            f"{hole.Name}.Diameter",
        )

    Utils.hole_prepare_layer_height_property(hole)

    pocket_bridges_y = body.newObject("PartDesign::Pocket", f"{hole.Name}_BridgesY")
    pocket_bridges_y.Profile = (sketch_bridges_y, "")
    pocket_bridges_y.ReferenceAxis = (sketch_bridges_y, ["N_Axis"])
    pocket_bridges_y.Reversed = hole.Reversed
    sketch_bridges_y.Visibility = False
    pocket_bridges_y.setExpression("Length", f"{hole.Name}.HoleCutDepth + {hole.Name}.LayerHeight")
    pocket_bridges_y.Label = f"{hole.Label}_BridgesY"
    pocket_bridges_y.recompute()

    pocket_bridges_x = body.newObject("PartDesign::Pocket", f"{hole.Name}_BridgesX")
    pocket_bridges_x.Profile = (sketch_bridges_x, "")
    pocket_bridges_x.ReferenceAxis = (sketch_bridges_x, ["N_Axis"])
    pocket_bridges_x.Reversed = hole.Reversed
    sketch_bridges_x.Visibility = False
    pocket_bridges_x.setExpression("Length", f"{hole.Name}.HoleCutDepth + {hole.Name}.LayerHeight * 2")
    pocket_bridges_x.Label = f"{hole.Label}_BridgesX"
    pocket_bridges_x.recompute()


class CounterboreBridgesCommand:
    def GetResources(self):
        return {
            # TODO: Update icon
            "Pixmap": Utils.Resources.get_icon("ffDesign_HoleWizard.svg"),
            "MenuText": App.Qt.translate("ffDesign", "Add counterbore bridges"),
            "ToolTip": App.Qt.translate(
                "ffDesign",
                "Add bridges to a counterbored Hole so it can be printed upside down.\n"
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
                make_upside_down_counterbores(body, hole)
            except Exception as e:
                App.ActiveDocument.abortTransaction()
                raise e from None
            else:
                App.ActiveDocument.commitTransaction()
        except Utils.ffDesignError:
            pass

    def IsActive(self):
        return Utils.check_hole_tool_preconditions()


Gui.addCommand("ffDesign_CounterboreBridges", CounterboreBridgesCommand())
