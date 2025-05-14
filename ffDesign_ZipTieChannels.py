import math

from PySide import QtCore, QtGui

import FreeCADGui as Gui
import FreeCAD as App
import Part
import Sketcher

import ffDesign_Utils as Utils


def make_zip_tie_channel_settings(
    body,
    original,
    *,
    width: App.Units.Quantity,
):
    Utils.assert_body(body)

    width = App.Units.Quantity(width)
    assert width.Unit.Type == "Length"

    varset = body.newObject("App::VarSet", f"{original.Name}_ZipTieChannel_Settings")
    varset.Label = f"{original.Label}_ZipTieChannel_Settings"

    varset.addProperty("App::PropertyLength", "ChannelWidth", group="Base")
    varset.ChannelWidth = width
    varset.addProperty("App::PropertyAngle", "ChannelRotation", group="Base")
    varset.ChannelRotation = "90 deg"
    varset.recompute()

    return varset


def make_zip_tie_channel_template(
    body,
    original,
    *,
    thickness: App.Units.Quantity,
    bridge_dia: App.Units.Quantity,
):
    Utils.assert_body(body)
    sketch = body.newObject("Sketcher::SketchObject", f"{original.Name}_ZipTieChannel_Template")
    sketch.Label = f"{original.Label}_ZipTieChannel_Template"
    sketch.Visibility = False

    thickness = App.Units.Quantity(thickness)
    assert thickness.Unit.Type == "Length"
    bridge_dia = App.Units.Quantity(bridge_dia)
    assert bridge_dia.Unit.Type == "Length"

    dist_inner = bridge_dia.Value / 2
    dist_outer = dist_inner + thickness.Value

    last_geo_id = len(sketch.Geometry)
    new_geo = [
        Part.ArcOfCircle(
            Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), dist_outer),
            math.pi * 1,
            math.pi * 0,
        ),
        Part.ArcOfCircle(
            Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), dist_inner),
            math.pi * 1,
            math.pi * 0,
        ),
        Part.LineSegment(App.Vector(-dist_inner, 0, 0), App.Vector(-dist_outer, 0, 0)),
        Part.LineSegment(App.Vector(dist_inner, 0, 0), App.Vector(dist_outer, 0, 0)),
    ]
    sketch.addGeometry(new_geo, False)

    new_constraints = [
        Sketcher.Constraint("Coincident", last_geo_id + 0, 1, last_geo_id + 2, 2),
        Sketcher.Constraint("Coincident", last_geo_id + 1, 1, last_geo_id + 2, 1),
        Sketcher.Constraint("Coincident", last_geo_id + 0, 2, last_geo_id + 3, 2),
        Sketcher.Constraint("Coincident", last_geo_id + 1, 2, last_geo_id + 3, 1),
        Sketcher.Constraint("Coincident", last_geo_id + 0, 3, -1, 1),
        Sketcher.Constraint("Coincident", last_geo_id + 1, 3, -1, 1),
        Sketcher.Constraint("PointOnObject", last_geo_id + 0, 1, -1),
        Sketcher.Constraint("PointOnObject", last_geo_id + 0, 2, -1),
        Sketcher.Constraint("PointOnObject", last_geo_id + 1, 1, -1),
        Sketcher.Constraint("PointOnObject", last_geo_id + 1, 2, -1),
    ]
    sketch.addConstraint(new_constraints)

    last_c = len(sketch.Constraints)
    new_constraints = [
        Sketcher.Constraint("Diameter", last_geo_id + 1, bridge_dia.Value),
        Sketcher.Constraint("DistanceX", last_geo_id + 0, 1, last_geo_id + 1, 1, thickness.Value),
    ]
    sketch.addConstraint(new_constraints)
    sketch.renameConstraint(last_c + 0, "ChannelBridgeDiameter")
    sketch.renameConstraint(last_c + 1, "ChannelThickness")

    sketch.recompute()
    return sketch


def make_zip_tie_channel(body, original, template, settings, suffix: str, center_expr: str):
    Utils.assert_body(body)
    Utils.assert_sketch(original)
    Utils.assert_sketch(template)
    Utils.assert_varset(settings)

    binder = Utils.make_sketch_offset_shape_binder(
        body,
        template,
        sketch=original,
        suffix=suffix + "_Binder",
        center_expr=center_expr,
        rotation_expr=f"rotation({settings.Name}.ChannelRotation; 0; 90 deg)",
    )

    pocket = body.newObject("PartDesign::Pocket", original.Name + suffix)
    pocket.Profile = (binder, "")
    pocket.Midplane = True
    binder.Visibility = False
    pocket.setExpression("Length", f"{settings.Name}.ChannelWidth")
    pocket.Label = original.Label + suffix
    pocket.recompute()


def find_points_in_sketch(sketch):
    Utils.assert_sketch(sketch)

    def is_valid_point(index, point):
        return point.TypeId == "Part::GeomPoint" and not sketch.getConstruction(index)

    return list(index for index, point in enumerate(sketch.Geometry) if is_valid_point(index, point))


def make_zip_tie_channels_from_sketch(
    body,
    sketch,
    *,
    width: App.Units.Quantity,
    thickness: App.Units.Quantity,
    bridge_dia: App.Units.Quantity,
):
    Utils.assert_body(body)
    Utils.assert_sketch(sketch)

    settings = make_zip_tie_channel_settings(body, sketch, width=width)
    template = make_zip_tie_channel_template(body, sketch, thickness=thickness, bridge_dia=bridge_dia)

    for point_idx in find_points_in_sketch(sketch):
        make_zip_tie_channel(
            body,
            sketch,
            template,
            settings,
            suffix=f"_ZipTieChannel{point_idx+1:03}",
            center_expr=f"vector({sketch.Name}.Geometry[{point_idx}].X; {sketch.Name}.Geometry[{point_idx}].Y; 0)",
        )

    sketch.Visibility = False


class ZipTieChannelsTaskPanel:
    def __init__(self, body, sketch):
        Utils.assert_body(body)
        Utils.assert_sketch(sketch)

        self.body = body
        self.sketch = sketch
        self.form = Gui.PySideUic.loadUi(Utils.Resources.get_panel("ffDesign_ZipTieChannels.ui"))

        # TODO: Implement line ends
        self.form.LineEnds.setEnabled(False)

        self.updateMessage()

    def updateMessage(self):
        n_points = len(find_points_in_sketch(self.sketch))
        color = "#008000" if n_points > 0 else "#800000"

        self.form.InfoMessage.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.form.InfoMessage.setText(f'<font color="{color}">Found {n_points} points in "{self.sketch.Label}"</font>')

        # Default values
        self.form.ChannelWidth.setProperty("rawValue", 3.5)
        self.form.ChannelThickness.setProperty("rawValue", 1.5)
        self.form.BridgeDiameter.setProperty("rawValue", 2.5)

    def accept(self):
        try:
            Gui.Control.closeDialog()

            if len(find_points_in_sketch(self.sketch)) == 0:
                raise Utils.ffDesignError("Cannot generate zip tie channels: No points were found in the sketch!")

            try:
                if Utils.undo_shapebinder_is_safe():
                    App.ActiveDocument.openTransaction("Add zip tie channels")
                make_zip_tie_channels_from_sketch(
                    self.body,
                    self.sketch,
                    width=self.form.ChannelWidth.property("value"),
                    thickness=self.form.ChannelThickness.property("value"),
                    bridge_dia=self.form.BridgeDiameter.property("value"),
                )
                App.ActiveDocument.recompute()
                if Utils.undo_shapebinder_is_safe():
                    App.ActiveDocument.commitTransaction()
            except Exception as e:
                if Utils.undo_shapebinder_is_safe():
                    App.ActiveDocument.abortTransaction()
                raise e from None
        except Utils.ffDesignError as e:
            e.emit_to_user()

    def reject(self):
        Gui.Control.closeDialog()


class ZipTieChannelsCommand:
    def GetResources(self):
        return {
            "Pixmap": "icons:ffDesign_ZipTieChannels.svg",
            "MenuText": App.Qt.translate("ffDesign", "Add zip tie channels"),
            "ToolTip": App.Qt.translate(
                "ffDesign",
                "Add zip tie channels for easily fastening wires to a part.\n"
                "1. Select a reference sketch which has points marking the locations of the zip tie channels.\n"
                "2. Run this command.\n",
            ),
        }

    def Activated(self):
        try:
            sketch = Utils.get_selected_sketch()
            body = Utils.get_active_part_design_body_for_feature(sketch)

            dialog = ZipTieChannelsTaskPanel(body, sketch)
            Gui.Control.showDialog(dialog)
        except Utils.ffDesignError as e:
            e.emit_to_user()

    def IsActive(self):
        return Utils.check_sketch_tool_preconditions()


Gui.addCommand("ffDesign_ZipTieChannels", ZipTieChannelsCommand())
