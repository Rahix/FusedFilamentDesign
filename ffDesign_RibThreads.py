import math
import dataclasses

from PySide import QtCore, QtGui

import FreeCADGui as Gui
import FreeCAD as App
import Part
import Sketcher

import ffDesign_Utils as Utils


@dataclasses.dataclass
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


def make_rib_template(sketch, rib_param: RibParameters):
    Utils.assert_sketch(sketch)

    if len(sketch.Geometry) != 0:
        Utils.Log.warning("Sketch for the rib thread template is not empty before generation?!")

    center_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), rib_param.outer_diameter / 2)
    rib_center_radius = (rib_param.normative - rib_param.rib_engagement * 2 + rib_param.rib_diameter) / 2
    rib_center_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), rib_center_radius)

    rib_center_circle_id = len(sketch.Geometry)
    sketch.addGeometry(rib_center_circle)
    sketch.toggleConstruction(rib_center_circle_id)

    normative_circle_id = len(sketch.Geometry)
    sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), rib_param.normative / 2))
    sketch.toggleConstruction(normative_circle_id)

    core_circle_id = len(sketch.Geometry)
    sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), rib_param.core_diameter / 2))
    sketch.toggleConstruction(core_circle_id)

    rib_arc_ids = len(sketch.Geometry)
    center_angles = []
    for i in range(3):
        a = i * math.pi * 2 / 3
        rib_center = App.Vector(math.cos(a) * rib_center_radius, math.sin(a) * rib_center_radius, 0)
        rib_circle = Part.Circle(
            rib_center,
            App.Vector(0, 0, 1),
            rib_param.rib_diameter / 2,
        )
        intersections = center_circle.intersect(rib_circle)
        if len(intersections) != 2:
            raise Utils.ffDesignError("ribs do not intersect outer diameter, cannot proceed!")

        center_angles += [math.atan2(p.Y, p.X) for p in intersections]

        rib_intersections = [App.Vector(p.X, p.Y, 0) - rib_center for p in intersections]
        rib_angles = [math.atan2(p.y, p.x) for p in rib_intersections]

        sketch.addGeometry(Part.ArcOfCircle(rib_circle, rib_angles[0], rib_angles[1]))

    assert len(center_angles) == 6
    center_angles.sort()

    center_arc_ids = len(sketch.Geometry)
    new_geo = [
        Part.ArcOfCircle(center_circle, center_angles[1], center_angles[2]),
        Part.ArcOfCircle(center_circle, center_angles[3], center_angles[4]),
        Part.ArcOfCircle(center_circle, center_angles[5], center_angles[0]),
    ]
    sketch.addGeometry(new_geo, False)

    new_constraints = [
        # Arc End Coincidences
        Sketcher.Constraint("Coincident", center_arc_ids + 0, 2, rib_arc_ids + 0, 2),
        Sketcher.Constraint("Coincident", center_arc_ids + 1, 1, rib_arc_ids + 0, 1),
        Sketcher.Constraint("Coincident", center_arc_ids + 1, 2, rib_arc_ids + 1, 2),
        Sketcher.Constraint("Coincident", center_arc_ids + 2, 1, rib_arc_ids + 1, 1),
        Sketcher.Constraint("Coincident", center_arc_ids + 2, 2, rib_arc_ids + 2, 2),
        Sketcher.Constraint("Coincident", center_arc_ids + 0, 1, rib_arc_ids + 2, 1),
        # Arc Centers
        Sketcher.Constraint("Coincident", rib_center_circle_id, 3, -1, 1),
        Sketcher.Constraint("Coincident", normative_circle_id, 3, -1, 1),
        Sketcher.Constraint("Coincident", core_circle_id, 3, -1, 1),
        Sketcher.Constraint("Coincident", center_arc_ids + 0, 3, -1, 1),
        Sketcher.Constraint("Coincident", center_arc_ids + 1, 3, -1, 1),
        Sketcher.Constraint("Coincident", center_arc_ids + 2, 3, -1, 1),
        Sketcher.Constraint("PointOnObject", rib_arc_ids + 0, 3, rib_center_circle_id),
        Sketcher.Constraint("PointOnObject", rib_arc_ids + 1, 3, rib_center_circle_id),
        Sketcher.Constraint("PointOnObject", rib_arc_ids + 2, 3, rib_center_circle_id),
        # Arc Equalities
        Sketcher.Constraint("Equal", center_arc_ids + 0, center_arc_ids + 1),
        Sketcher.Constraint("Equal", center_arc_ids + 0, center_arc_ids + 2),
        Sketcher.Constraint("Equal", rib_arc_ids + 0, rib_arc_ids + 1),
        Sketcher.Constraint("Equal", rib_arc_ids + 0, rib_arc_ids + 2),
    ]
    sketch.addConstraint(new_constraints)

    dia_constraint_ids = len(sketch.Constraints)
    new_constraints = [
        # Diameters
        Sketcher.Constraint("Diameter", rib_center_circle_id, rib_center_radius * 2),
        Sketcher.Constraint("Diameter", center_arc_ids + 0, rib_param.outer_diameter),
        Sketcher.Constraint("Diameter", rib_arc_ids + 0, rib_param.rib_diameter),
        Sketcher.Constraint("Diameter", normative_circle_id, rib_param.normative),
        Sketcher.Constraint("Diameter", core_circle_id, rib_param.core_diameter),
    ]
    sketch.addConstraint(new_constraints)
    sketch.renameConstraint(dia_constraint_ids + 1, "outer_diameter")
    sketch.renameConstraint(dia_constraint_ids + 2, "rib_diameter")
    sketch.renameConstraint(dia_constraint_ids + 3, "normative_diameter")
    sketch.renameConstraint(dia_constraint_ids + 4, "core_diameter")

    # Lines for distance between ribs
    line_ids = len(sketch.Geometry)
    for i in range(3):
        center1 = sketch.Geometry[rib_arc_ids + i].Center
        center2 = sketch.Geometry[rib_arc_ids + ((i + 1) % 3)].Center

        line_id = len(sketch.Geometry)
        sketch.addGeometry(Part.LineSegment(center1, center2))
        sketch.toggleConstruction(line_id)
        new_constraints = [
            Sketcher.Constraint("Coincident", line_id, 1, rib_arc_ids + i, 3),
            Sketcher.Constraint("Coincident", line_id, 2, rib_arc_ids + ((i + 1) % 3), 3),
        ]
        sketch.addConstraint(new_constraints)

    # Constrain distance between ribs to be equal
    new_constraints = [
        Sketcher.Constraint("Equal", line_ids + 0, line_ids + 1),
        Sketcher.Constraint("Equal", line_ids + 0, line_ids + 2),
    ]
    sketch.addConstraint(new_constraints)

    # Finally, constrain rotation of the ribs around the center
    new_constraints = [
        Sketcher.Constraint("PointOnObject", rib_arc_ids + 0, 3, -1),
    ]
    sketch.addConstraint(new_constraints)
    sketch.recompute()


def write_rib_param_properties(template, rib_param: RibParameters):
    Utils.assert_sketch(template)

    if "EntranceDepth" not in template.PropertiesList:
        template.addProperty("App::PropertyLength", "EntranceDepth", group="RibParameters")
    if "OuterDiameter" not in template.PropertiesList:
        template.addProperty("App::PropertyLength", "OuterDiameter", group="RibParameters")
    if "RibEngagement" not in template.PropertiesList:
        template.addProperty("App::PropertyLength", "RibEngagement", group="RibParameters")
    if "RibDiameter" not in template.PropertiesList:
        template.addProperty("App::PropertyLength", "RibDiameter", group="RibParameters")

    template.EntranceDepth = rib_param.entrance_depth
    template.OuterDiameter = rib_param.outer_diameter
    template.RibEngagement = rib_param.rib_engagement
    template.RibDiameter = rib_param.rib_diameter

    # Make properties read-only
    template.setEditorMode("EntranceDepth", 1)
    template.setEditorMode("OuterDiameter", 1)
    template.setEditorMode("RibEngagement", 1)
    template.setEditorMode("RibDiameter", 1)


def rib_template_name(hole, global_template: bool):
    if global_template:
        return f"RibThread_{hole.ThreadSize}_Template"
    else:
        return f"{hole.Name}_RibThread_Template"


def find_rib_template(body, hole, global_template: bool):
    name = rib_template_name(hole, global_template)
    if global_template:
        return body.Document.getObject(name)
    else:
        return body.getObject(name)


def has_rib_template(body, hole, global_template: bool) -> bool:
    return find_rib_template(body, hole, global_template) is not None


def get_or_create_rib_template(body, hole, global_template: bool, rib_param: RibParameters):
    template = find_rib_template(body, hole, global_template)
    if template is not None:
        return template

    name = rib_template_name(hole, global_template)
    if global_template:
        template = body.Document.addObject("Sketcher::SketchObject", name)
    else:
        template = body.newObject("Sketcher::SketchObject", name)
        template.Label = f"{hole.Label}_RibThread_Template"

    template.Visibility = False

    make_rib_template(template, rib_param)
    write_rib_param_properties(template, rib_param)

    return template


def make_rib_threads(body, hole, global_template: bool, rib_param: RibParameters):
    Utils.assert_body(body)
    Utils.assert_hole(hole)

    profile_sketch = Utils.get_hole_profile_sketch(hole)

    template = get_or_create_rib_template(body, hole, global_template, rib_param)

    # Only generate the varset if it does not exist yet
    varset = body.getObject(f"{hole.Name}_RibThread_Settings")
    if varset is None:
        varset = body.newObject("App::VarSet", f"{hole.Name}_RibThread_Settings")
        varset.Label = f"{hole.Label}_RibThread"
        varset.addProperty("App::PropertyLength", "EntranceDepth", "Base")
        varset.addProperty("App::PropertyLength", "EntranceDiameter", "Base")
        varset.addProperty("App::PropertyAngle", "Rotation", "Base")
        varset.EntranceDepth = f"{rib_param.entrance_depth} mm"
        varset.EntranceDiameter = f"{rib_param.outer_diameter} mm"
        varset.Rotation = "0 deg"
        varset.recompute()

    sketch_entrance = Utils.make_derived_sketch(body, profile_sketch, "_ThreadEntrance")

    shape_binders = []
    for index in Utils.get_sketch_circle_indices(profile_sketch):
        make_parametric_circle(
            sketch_entrance,
            f"{profile_sketch.Name}.Geometry[{index}].Center",
            f"{varset.Name}.EntranceDiameter",
        )

        binder = Utils.make_sketch_offset_shape_binder(
            body=body,
            template=template,
            sketch=profile_sketch,
            suffix=f"_RibThread{index + 1:03}",
            center_expr=f"{profile_sketch.Name}.Geometry[{index}].Center",
            rotation_expr=f"rotation({varset.Name}.Rotation; 0; 0)",
        )
        shape_binders.append(binder)

    if len(shape_binders) == 1:
        merged_binder = shape_binders[0]
    else:
        # When we have more than one shape binder, we first have to merge them
        # all before we can make a pocket from them.
        merged_binder = body.newObject("PartDesign::SubShapeBinder", f"{hole.Name}_RibThreads")
        merged_binder.Support = [(b, "") for b in shape_binders]
        merged_binder.Relative = True
        Utils.set_shape_binder_styles(merged_binder)
        merged_binder.recompute()

    pocket_ribs = body.newObject("PartDesign::Pocket", f"{hole.Name}_ThreadRibs")
    pocket_ribs.Profile = (merged_binder, "")
    pocket_ribs.Reversed = hole.Reversed
    merged_binder.Visibility = False
    pocket_ribs.setExpression("Type", f"{hole.Name}.DepthType")
    pocket_ribs.setExpression("Length", f"{hole.Name}.Depth")
    pocket_ribs.Label = f"{hole.Label}_ThreadRibs"
    pocket_ribs.recompute()

    if hole.Reversed:
        sketch_entrance.setExpression(".AttachmentOffset.Base.z", f"{varset.Name}.EntranceDepth")
    else:
        sketch_entrance.setExpression(".AttachmentOffset.Base.z", f"-{varset.Name}.EntranceDepth")
    sketch_entrance.recompute()

    pocket_entrance = body.newObject("PartDesign::Pocket", f"{hole.Name}_ThreadEntrance")
    pocket_entrance.Profile = (sketch_entrance, "")
    pocket_entrance.ReferenceAxis = (sketch_entrance, ["N_Axis"])
    pocket_entrance.Reversed = hole.Reversed
    pocket_entrance.Type = "TwoLengths"
    pocket_entrance.TaperAngle = "-20 deg"
    sketch_entrance.Visibility = False
    # 2.8 is roughly the tan(90 - 20 deg), so the taper will be complete
    pocket_entrance.setExpression("Length", f"({varset.Name}.EntranceDiameter - {hole.Name}.Diameter) * 2.8")
    pocket_entrance.setExpression("Length2", f"{varset.Name}.EntranceDepth")
    pocket_entrance.Label = f"{hole.Label}_ThreadEntrance"
    pocket_entrance.recompute()


class RibThreadsTaskPanel:
    def __init__(self, body, hole):
        Utils.assert_body(body)
        Utils.assert_hole(hole)

        self.body = body
        self.hole = hole
        self.global_template = False
        self.template_exists = False
        self.form = Gui.PySideUic.loadUi(Utils.Resources.get_panel("ffDesign_RibThreads.ui"))

        self.form.UseGlobalTemplate.setCheckState(QtCore.Qt.CheckState.Checked)
        self.form.UseGlobalTemplate.stateChanged.connect(self.onUseGlobalTemplate)
        self.onUseGlobalTemplate()

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
        else:
            self.form.ThreadCore.setProperty("rawValue", hole.Diameter)

    def onUseGlobalTemplate(self):
        self.global_template = self.form.UseGlobalTemplate.checkState() == QtCore.Qt.CheckState.Checked
        self.updateTemplatePresence()

    def updateTemplatePresence(self):
        template = find_rib_template(self.body, self.hole, self.global_template)
        self.template_exists = template is not None

        if template is not None:
            if "EntranceDepth" in template.PropertiesList:
                self.form.EntranceDepth.setProperty("rawValue", template.EntranceDepth.Value)
            if "OuterDiameter" in template.PropertiesList:
                self.form.OuterDiameter.setProperty("rawValue", template.OuterDiameter.Value)
            if "RibEngagement" in template.PropertiesList:
                self.form.RibEngagement.setProperty("rawValue", template.RibEngagement.Value)
            if "RibDiameter" in template.PropertiesList:
                self.form.RibDiameter.setProperty("rawValue", template.RibDiameter.Value)

        self.updateEditability()
        self.updateInfoMessage()

    def updateEditability(self):
        self.form.EntranceDepth.setEnabled(not self.template_exists)
        self.form.OuterDiameter.setEnabled(not self.template_exists)
        self.form.RibEngagement.setEnabled(not self.template_exists)
        self.form.RibDiameter.setEnabled(not self.template_exists)

    def updateInfoMessage(self):
        self.form.InfoMessage.setTextFormat(QtCore.Qt.TextFormat.RichText)
        if self.global_template and self.template_exists:
            self.form.InfoMessage.setText(f'<font color="#008000">Using existing global template...</font>')
        elif self.global_template and not self.template_exists:
            self.form.InfoMessage.setText(
                f'<font color="#008000">Creating new global template for {self.hole.ThreadSize}...</font>'
            )
        elif not self.global_template and self.template_exists:
            self.form.InfoMessage.setText(f'<font color="#008000">Reusing existing template for this hole...</font>')
        else:
            self.form.InfoMessage.setText(f'<font color="#008000">Creating new template...</font>')

    def build_rib_parameters(self):
        if self.hole.ThreadSize in RIB_PARAMETERS:
            rib_param = dataclasses.replace(
                RIB_PARAMETERS[self.hole.ThreadSize],
                entrance_depth=self.form.EntranceDepth.property("rawValue"),
                outer_diameter=self.form.OuterDiameter.property("rawValue"),
                rib_engagement=self.form.RibEngagement.property("rawValue"),
                rib_diameter=self.form.RibDiameter.property("rawValue"),
            )
        else:
            # Pull the normative diameter from the thread size string
            normative_diameter = float(self.hole.ThreadSize[1:].split("x", 1)[0])

            rib_param = RibParameters(
                name=self.hole.ThreadSize,
                normative=normative_diameter,
                core_bore=self.form.ThreadCore.property("rawValue"),
                core_diameter=self.form.ThreadCore.property("rawValue"),
                entrance_depth=self.form.EntranceDepth.property("rawValue"),
                outer_diameter=self.form.OuterDiameter.property("rawValue"),
                rib_engagement=self.form.RibEngagement.property("rawValue"),
                rib_diameter=self.form.RibDiameter.property("rawValue"),
            )

        # Now make sure that these parameter sets are consistent
        if self.hole.Diameter > rib_param.normative:
            raise Utils.ffDesignError("Hole diameter exceeds normative thread diameter.  Something is way off...")

        if self.hole.Diameter > (rib_param.normative - rib_param.rib_engagement * 2):
            Utils.warning_confirm_proceed("Drill diameter of Hole is too big for ribs - they will get cut off!")

        return rib_param

    def accept(self):
        try:
            rib_param = self.build_rib_parameters()
            Gui.Control.closeDialog()

            try:
                App.ActiveDocument.openTransaction("Add thread forming ribs")
                make_rib_threads(self.body, self.hole, self.global_template, rib_param)
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


def verify_rib_thread_suitability(hole):
    Utils.assert_hole(hole)

    if Utils.hole_has_counterbore_maybe(hole):
        Utils.Log.warning(
            "Making thread forming ribs on a hole with counterbore.  The result will probably be unexpected..."
        )

    if not hole.Threaded:
        raise Utils.ffDesignError("Cannot make thread forming ribs on a hole that is not threaded!")

    if hole.ModelThread:
        raise Utils.ffDesignError("Cannot make thread forming ribs on a hole with modelled threads!")

    if hole.Tapered:
        raise Utils.ffDesignError("Cannot make thread forming ribs on a tapered hole!")


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

            verify_rib_thread_suitability(hole)

            dialog = RibThreadsTaskPanel(body, hole)
            Gui.Control.showDialog(dialog)
        except Utils.ffDesignError:
            pass

    def IsActive(self):
        return Utils.check_hole_tool_preconditions()


Gui.addCommand("ffDesign_RibThreads", RibThreadsCommand())
