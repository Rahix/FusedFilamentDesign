import math

from PySide import QtCore

import FreeCADGui as Gui
import FreeCAD as App
import Part
import Sketcher

import ffDesign_Utils as Utils


HEX_SIDES = 6


def make_parametric_hex_nut(
    sketch,
    *,
    hole_loc: Utils.LocationExprSet,
    radius_expr: str,
    rotation: float = 0.0,
):
    Utils.assert_sketch(sketch)

    last_geo_id = len(sketch.Geometry)
    points = []
    for i in range(HEX_SIDES):
        angle = 2 * math.pi / HEX_SIDES * i + rotation
        points.append(App.Vector(math.cos(angle), math.sin(angle), 0))

    new_geo = [Part.LineSegment(points[i], points[(i + 1) % HEX_SIDES]) for i in range(HEX_SIDES)]
    sketch.addGeometry(new_geo, False)

    new_constraints = []
    for i in range(HEX_SIDES):
        new_constraints.append(
            Sketcher.Constraint("Coincident", last_geo_id + i, 2, last_geo_id + (i + 1) % HEX_SIDES, 1)
        )
    sketch.addConstraint(new_constraints)

    # Fix every vertex directly.  Equal sides plus points on a circle also
    # allows a collapsed hexagon, so all vertices get their own coordinates.
    x = hole_loc.x_expr
    y = hole_loc.y_expr
    r = f"({radius_expr})"
    vertex_offsets = []
    for i in range(HEX_SIDES):
        angle = 2 * math.pi / HEX_SIDES * i + rotation
        vertex_offsets.append((f"{r} * {math.cos(angle)!r}", f"{r} * {math.sin(angle)!r}"))

    expressions = []
    for dx, dy in vertex_offsets:
        expressions.append(f"{x} + ({dx})")
        expressions.append(f"{y} + ({dy})")

    last_c = len(sketch.Constraints)
    new_constraints = []
    for i in range(HEX_SIDES):
        new_constraints.append(Sketcher.Constraint("DistanceX", last_geo_id + i, 1, 0))
        new_constraints.append(Sketcher.Constraint("DistanceY", last_geo_id + i, 1, 0))
    sketch.addConstraint(new_constraints)
    for i, expr in enumerate(expressions):
        sketch.setExpression(f"Constraints[{last_c + i}]", expr)

    sketch.recompute()


def _get_far_face_offset(body, hole, profile_sketch, hole_loc):
    """
    Distance from the profile plane to the opposite face of the part.

    The result is signed along the profile sketch's local Z axis, so it can be
    used as the attachment offset of a sketch on the opposite face.
    """
    Utils.assert_body(body)
    Utils.assert_hole(hole)
    Utils.assert_sketch(profile_sketch)

    if hole_loc.center is None:
        raise Utils.ffDesignError("Could not determine the position of a hole.")

    profile_placement = profile_sketch.Placement
    normal = profile_placement.Rotation.multVec(App.Vector(0, 0, 1))
    direction = normal if hole.Reversed else normal * -1
    entry = profile_placement.multVec(hole_loc.center)

    # The hole axis itself is empty, so probe the material just next to the
    # hole wall and look for the last point that is still inside the part.
    radius = hole.Diameter.Value / 2
    radial_a = direction.cross(App.Vector(1, 0, 0))
    if radial_a.Length < 1e-6:
        radial_a = direction.cross(App.Vector(0, 1, 0))
    radial_a.normalize()
    radial_b = direction.cross(radial_a)
    radial_b.normalize()

    bound = body.Shape.BoundBox.DiagonalLength * 2 + 10
    entry_proj = entry.dot(direction)
    distances = []
    for radial in (radial_a, radial_a * -1, radial_b, radial_b * -1):
        offset = radial * (radius + 0.05)
        start = entry + offset - direction * (radius + 3)
        end = entry + offset + direction * bound
        common = body.Shape.common(Part.makeLine(start, end))
        if not common.Vertexes:
            continue
        far_proj = max(vertex.Point.dot(direction) for vertex in common.Vertexes)
        distances.append(far_proj - entry_proj)

    if not distances or max(distances) <= 0:
        raise Utils.ffDesignError(
            "Could not find the opposite face of this hole. The hex nut recess was not created."
        )

    distance = max(distances)
    return distance if hole.Reversed else -distance


def _make_hex_nut_pocket(body, hole, hex_sketch, *, reversed_, suffix):
    pocket = body.newObject("PartDesign::Pocket", f"{hole.Name}{suffix}")
    pocket.Profile = (hex_sketch, "")
    pocket.ReferenceAxis = (hex_sketch, ["N_Axis"])
    pocket.Reversed = reversed_
    hex_sketch.Visibility = False
    pocket.setExpression("Length", f"{hole.Name}.HexNutDepth")
    pocket.Label = f"{hole.Label}{suffix}"
    pocket.recompute()


def make_hex_nuts(
    body,
    hole,
    *,
    nut_radius: App.Units.Quantity,
    nut_depth: App.Units.Quantity,
    far_side: bool = False,
    vertex_up: bool = False,
):
    Utils.assert_body(body)
    Utils.assert_hole(hole)

    # A regular hexagon has 6-fold symmetry, so a 60 degree turn looks the
    # same.  Turning it by 30 degrees is what swaps a flat side and a vertex.
    rotation = math.radians(30) if vertex_up else 0.0

    nut_radius = App.Units.Quantity(nut_radius)
    assert nut_radius.Unit.Type == "Length"
    nut_depth = App.Units.Quantity(nut_depth)
    assert nut_depth.Unit.Type == "Length"

    if "HexNutRadius" not in hole.PropertiesList:
        hole.addProperty("App::PropertyLength", "HexNutRadius", group="FusedFilamentDesign")
    hole.HexNutRadius = nut_radius

    if "HexNutDepth" not in hole.PropertiesList:
        hole.addProperty("App::PropertyLength", "HexNutDepth", group="FusedFilamentDesign")
    hole.HexNutDepth = nut_depth

    profile_sketch, profile_partial = Utils.get_hole_profile_sketch(hole)
    hole_locations = Utils.get_sketch_locations(profile_sketch, Utils.get_hole_profile_type(hole), profile_partial)

    if not far_side:
        hex_sketch = Utils.make_derived_sketch(body, profile_sketch, "_HexNut")
        for hole_loc in hole_locations:
            make_parametric_hex_nut(
                hex_sketch,
                hole_loc=hole_loc,
                radius_expr=f"{hole.Name}.HexNutRadius",
                rotation=rotation,
            )
        _make_hex_nut_pocket(body, hole, hex_sketch, reversed_=hole.Reversed, suffix="_HexNut")
        return

    # Each hole can exit through a face at a different distance, and a sketch
    # is planar.  So on the opposite side, every hole gets its own sketch.
    offsets = [
        (hole_loc, _get_far_face_offset(body, hole, profile_sketch, hole_loc)) for hole_loc in hole_locations
    ]
    multiple = len(offsets) > 1
    for i, (hole_loc, offset) in enumerate(offsets):
        suffix = f"_HexNut{i + 1}" if multiple else "_HexNut"
        hex_sketch = Utils.make_derived_sketch(body, profile_sketch, suffix)
        hex_sketch.AttachmentOffset = App.Placement(App.Vector(0, 0, offset), App.Rotation())
        hex_sketch.recompute()
        make_parametric_hex_nut(
            hex_sketch,
            hole_loc=hole_loc,
            radius_expr=f"{hole.Name}.HexNutRadius",
            rotation=rotation,
        )
        _make_hex_nut_pocket(body, hole, hex_sketch, reversed_=not hole.Reversed, suffix=suffix)


class HexNutTaskPanel:
    def __init__(self, body, hole):
        Utils.assert_body(body)
        Utils.assert_hole(hole)

        self.body = body
        self.hole = hole
        self.form = Gui.PySideUic.loadUi(Utils.Resources.get_panel("ffDesign_HexNut.ui"))

        self.form.HexNutRadius.setProperty("rawValue", 3.2)
        self.form.HexNutDepth.setProperty("rawValue", 3.0)

    def accept(self):
        try:
            nut_radius = self.form.HexNutRadius.property("value")
            nut_depth = self.form.HexNutDepth.property("value")
            far_side = self.form.FarSide.checkState() == QtCore.Qt.CheckState.Checked
            vertex_up = self.form.VertexUp.checkState() == QtCore.Qt.CheckState.Checked

            Gui.Control.closeDialog()

            try:
                App.ActiveDocument.openTransaction("Add hex nut hole")
                make_hex_nuts(
                    self.body,
                    self.hole,
                    nut_radius=nut_radius,
                    nut_depth=nut_depth,
                    far_side=far_side,
                    vertex_up=vertex_up,
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


class HexNutCommand:
    def GetResources(self):
        return {
            "Pixmap": "icons:ffDesign_HexNut.svg",
            "MenuText": App.Qt.translate("ffDesign", "Add hex nut hole"),
            "ToolTip": App.Qt.translate(
                "ffDesign",
                "Add a hexagonal recess to the end of a hole to hold a hex nut.\n"
                "1. Select a Hole feature in the active body.\n"
                "2. Run this command.\n",
            ),
        }

    def Activated(self):
        try:
            hole = Utils.get_selected_hole()
            body = Utils.get_active_part_design_body_for_feature(hole)

            dialog = HexNutTaskPanel(body, hole)
            Gui.Control.showDialog(dialog)
        except Utils.ffDesignError as e:
            e.emit_to_user()

    def IsActive(self):
        return Utils.check_hole_tool_preconditions()


Gui.addCommand("ffDesign_HexNut", HexNutCommand())
