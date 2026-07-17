import os
import dataclasses

from PySide import QtCore, QtGui

import FreeCADGui as Gui
import FreeCAD as App
import Sketcher


class Resources:
    mod_path = os.path.dirname(__file__)
    icons_path = os.path.join(mod_path, "Resources", "icons")
    panels_path = os.path.join(mod_path, "Resources", "panels")

    @classmethod
    def get_panel(cls, name: str) -> str:
        path = os.path.join(cls.panels_path, name)
        if not os.path.exists(path):
            raise ffDesignError(f"Missing task panel {name!r}!")
        return path

    @classmethod
    def register_search_paths(cls):
        QtCore.QDir.addSearchPath("icons", cls.icons_path)


class Log:
    addon = "FusedFilamentDesign"

    @classmethod
    def error(cls, msg: str) -> None:
        App.Console.PrintError(f"[{cls.addon}] {msg}\n")

    @classmethod
    def warning(cls, msg: str) -> None:
        App.Console.PrintWarning(f"[{cls.addon}] {msg}\n")

    @classmethod
    def info(cls, msg: str) -> None:
        App.Console.PrintMessage(f"[{cls.addon}] {msg}\n")


# This can be changed by e.g. testsuites to avoid error dialogs
SKIP_ALL_DIALOGS = False


class ffDesignError(Exception):
    def __init__(self, message: str, *, dialog: bool = True):
        self.message = message
        self.dialog = dialog
        super().__init__(message)

    def emit_to_user(self):
        Log.error(self.message)
        if self.dialog and not SKIP_ALL_DIALOGS:
            # Also show as a modal dialog
            QtGui.QMessageBox.warning(None, Log.addon, f"[{Log.addon}] {self.message}")
        if SKIP_ALL_DIALOGS:
            # When skipping dialogs, we definitely want to bubble up the exception
            raise self


class ffDesignPreconditionError(ffDesignError):
    """A precondition for using a command was not met."""

    pass


def warning_confirm_proceed(message: str, question: str = "Proceed anyway?"):
    Log.warning(message)
    if SKIP_ALL_DIALOGS:
        raise ffDesignError("Not proceeding with SKIP_ALL_DIALOGS")
    reply = QtGui.QMessageBox.question(None, Log.addon, f"[{Log.addon}] {message}\n{question}")
    if reply != QtGui.QMessageBox.Yes:
        raise ffDesignError("Aborted on user request due to previous warning", dialog=False)


def assert_body(obj):
    assert obj.TypeId == "PartDesign::Body"


def assert_hole(obj):
    assert obj.TypeId == "PartDesign::Hole"


def assert_sketch(obj):
    assert obj.TypeId == "Sketcher::SketchObject"


def assert_varset(obj):
    assert obj.TypeId == "App::VarSet"


def get_active_part_design_body_for_feature(obj):
    parent_body = obj.getParent()
    active_body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")

    if active_body is None:
        warning_confirm_proceed(
            "No active PartDesign Body!",
            f'Make "{parent_body.Label}" active?',
        )
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", parent_body)
        active_body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")

    if parent_body != active_body:
        warning_confirm_proceed(
            "Selected feature is not part of the active PartDesign body!",
            f'Make "{parent_body.Label}" active?',
        )
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", parent_body)
        active_body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")

    assert_body(active_body)
    return active_body


def get_selected_hole():
    if not App.ActiveDocument:
        raise ffDesignPreconditionError("No active document")

    sel = Gui.Selection.getSelection()
    if len(sel) == 1:
        if sel[0].TypeId != "PartDesign::Hole":
            raise ffDesignPreconditionError(
                f"Selected object is not a PartDesign Hole feature (is a {sel[0].TypeId!r} instead)."
            )
        return sel[0]

    active_body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
    if len(sel) == 0 and active_body is not None:
        if active_body.Tip is not None:
            if active_body.Tip.TypeId != "PartDesign::Hole":
                raise ffDesignPreconditionError(f"Tip of the active body is not a PartDesign Hole feature.")
            return active_body.Tip

    raise ffDesignPreconditionError("Exactly one Hole feature must be selected.")


def check_hole_tool_preconditions() -> bool:
    try:
        get_selected_hole()
        return True
    except ffDesignPreconditionError:
        return False


def get_selected_sketch():
    if not App.ActiveDocument:
        raise ffDesignPreconditionError("No active document")

    sel = Gui.Selection.getSelection()
    if len(sel) != 1:
        raise ffDesignPreconditionError("Exactly one Sketch must be selected.")

    if sel[0].TypeId != "Sketcher::SketchObject":
        raise ffDesignPreconditionError(f"Selected object is not a Sketch (is a {sel[0].TypeId!r} instead).")

    return sel[0]


def check_sketch_tool_preconditions() -> bool:
    try:
        get_selected_sketch()
        return True
    except ffDesignPreconditionError:
        return False


def hole_has_counterbore_maybe(hole) -> bool:
    """
    Check if a Hole feature has a counterbore.

    This check is True if it maybe has a counterbore, but it could also be a
    countersink or counterdrill.

    If this check is False, the hole definitely does not have any counterbore.
    """
    assert_hole(hole)

    return hole.HoleCutType != "None"


def hole_has_counterbore_sure(hole) -> bool:
    """
    Check if a Hole feature has a counterbore.

    This check is True the hole for sure has some type of counterbore.

    If this check is False, the hole may still have a counterbore, but it could
    also be a countersink, counterdrill or none at all.
    """
    assert_hole(hole)

    return hole.HoleCutType in [
        "Counterbore",
        "ISO 4762",
        "ISO 14583 (partial)",
        "DIN 7984",
        "ISO 4762 + 7089",
        "ISO 14583",
        "ISO 12474",
    ]


def hole_prepare_layer_height_property(hole):
    assert_hole(hole)

    if "LayerHeight" not in hole.PropertiesList:
        hole.addProperty("App::PropertyLength", "LayerHeight", group="FusedFilamentDesign")
        # TODO: Add some configuration setting for the default layer height
        hole.LayerHeight = "0.2 mm"


def get_hole_profile_sketch(hole):
    assert_hole(hole)

    if len(hole.Profile) < 1:
        raise ffDesignError("Hole does not have a profile!")

    # TODO: Check for list of profiles

    profile_sketch = hole.Profile[0]
    if profile_sketch.TypeId != "Sketcher::SketchObject":
        raise ffDesignError("Hole profile must be a Sketch!")

    return profile_sketch


def make_derived_sketch(body, original, suffix: str):
    assert_body(body)
    assert_sketch(original)

    sketch = body.newObject("Sketcher::SketchObject", original.Name + suffix)
    sketch.AttachmentSupport = [(original, "")]
    sketch.MapMode = "ObjectXY"
    sketch.Label = original.Label + suffix
    sketch.recompute()
    return sketch


# The `BaseProfileType` property introduced for `PartDesign_Hole` in
# FreeCAD 1.1 is a mask of the sketch features to be used.  Any combination of
# the following bit-flags may be used.
MASK_PROFILE_POINTS = 1
MASK_PROFILE_CIRCLES = 2
MASK_PROFILE_ARCS = 4


def get_hole_profile_type(hole):
    assert_hole(hole)

    # In older FreeCAD versions where `BaseProfileType` did not exist, the
    # `PartDesign_Hole` feature only used circles.
    return getattr(hole, "BaseProfileType", MASK_PROFILE_CIRCLES)


def sketch_external_geo_is_defining(sketch, index):
    assert_sketch(sketch)

    obj = sketch.ExternalGeo[index]

    # TODO: Right now this seems to be the only way to figure out if
    # external geometry is defining (==non-construction)
    try:
        egf = Sketcher.ExternalGeometryFacade(obj)
        return egf.testFlag("Defining")
    except (AttributeError, TypeError):
        # When ExternalGeometryFacade or the Defining flag do not exist, return None
        Log.warning("This version of FreeCAD does not support checking for defining external geometry. Ignoring it...")
        return None


@dataclasses.dataclass
class LocationExprSet:
    vector_expr: str
    x_expr: str
    y_expr: str


def get_sketch_locations(sketch, profile_type):
    assert_sketch(sketch)

    def try_make_loc_expr_set(index, obj, kind):
        assert kind in ["Geometry", "ExternalGeo"]

        if (profile_type & MASK_PROFILE_POINTS) != 0:
            if obj.TypeId == "Part::GeomPoint":
                x_expr = f"{sketch.Name}.{kind}[{index}].X"
                y_expr = f"{sketch.Name}.{kind}[{index}].Y"
                return LocationExprSet(
                    vector_expr=f"vector({x_expr}, {y_expr}, 0)",
                    x_expr=f"{x_expr} * 1mm",
                    y_expr=f"{y_expr} * 1mm",
                )
        if (profile_type & MASK_PROFILE_CIRCLES) != 0:
            if obj.TypeId == "Part::GeomCircle":
                center = f"{sketch.Name}.{kind}[{index}].Center"
                return LocationExprSet(
                    vector_expr=center,
                    x_expr=f"{center}.x * 1mm",
                    y_expr=f"{center}.y * 1mm",
                )
        if (profile_type & MASK_PROFILE_ARCS) != 0:
            if obj.TypeId == "Part::GeomArcOfCircle":
                center = f"{sketch.Name}.{kind}[{index}].Center"
                return LocationExprSet(
                    vector_expr=center,
                    x_expr=f"{center}.x * 1mm",
                    y_expr=f"{center}.y * 1mm",
                )

        return None

    locations = []

    for i, obj in enumerate(sketch.Geometry):
        # Ignore geometry if it is construction geometry.
        if sketch.getConstruction(i):
            continue

        loc = try_make_loc_expr_set(i, obj, "Geometry")
        if loc is not None:
            locations.append(loc)

    for i, obj in enumerate(sketch.ExternalGeo):
        # If this external geometry is not defining, ignore it.
        if not sketch_external_geo_is_defining(sketch, i):
            continue

        loc = try_make_loc_expr_set(i, obj, "ExternalGeo")
        if loc is not None:
            locations.append(loc)

    return locations


def set_shape_binder_styles(binder):
    binder.ViewObject.LineColor = (1.0, 0.84, 0.0, 0.60)
    binder.ViewObject.PointColor = (1.0, 0.84, 0.0, 0.60)
    m = binder.ViewObject.ShapeAppearance[0]
    m.DiffuseColor = (1.0, 0.84, 0.0, 0.60)
    binder.ViewObject.ShapeAppearance = (m,)
    binder.ViewObject.Transparency = 60


def make_sketch_offset_shape_binder(body, template, sketch, suffix: str, location: LocationExprSet, rotation_expr: str):
    assert_body(body)
    assert_sketch(template)
    assert_sketch(sketch)

    shape_binder = body.newObject("PartDesign::SubShapeBinder", sketch.Name + suffix)
    shape_binder.Support = (template, "")
    shape_binder.Relative = False
    shape_binder.Visibility = False
    set_shape_binder_styles(shape_binder)
    shape_binder.setExpression(
        "Placement",
        f"{sketch.Name}.Placement * placement({location.vector_expr}; {rotation_expr})",
    )
    shape_binder.Label = sketch.Label + suffix
    return shape_binder


def int_or_zero(string) -> int:
    try:
        return int(string)
    except ValueError:
        return 0


def check_freecad_version(*, min_version) -> bool:
    current = [int_or_zero(v.split()[0]) for v in App.Version()[:4]]
    return current >= min_version


def undo_shapebinder_is_safe() -> bool:
    """
    Undoing transactions where shape-binders are created is broken in FreeCAD
    1.0 and a fix will be released in 1.1.
    """
    return check_freecad_version(min_version=[1, 1, 0])


def set_pocket_two_lengths(pocket):
    try:
        # In more recent versions, a two-length pocket is created using `SideType`
        # See https://github.com/FreeCAD/FreeCAD/pull/21794
        pocket.SideType = "Two sides"
        pocket.Type = "Length"
        pocket.Type2 = "Length"
    except AttributeError:
        # Legacy code for FreeCAD 1.0 and early 1.1 development builds
        pocket.Type = "TwoLengths"


def set_pocket_symmetric(pocket):
    try:
        # In more recent versions, a symmetric pocket is created using `SideType`
        # See https://github.com/FreeCAD/FreeCAD/pull/21794
        pocket.SideType = "Symmetric"
    except AttributeError:
        # Legacy code for FreeCAD 1.0 and early 1.1 development builds
        pocket.Midplane = True


class ffDesignAboutCommand:
    def GetResources(self):
        return {
            "Pixmap": "icons:ffDesign_Logo.svg",
            "MenuText": App.Qt.translate("ffDesign", "FusedFilamentDesign"),
            "ToolTip": App.Qt.translate("ffDesign", "About the FusedFilamentDesign addon."),
        }

    def Activated(self):
        QtGui.QMessageBox.information(
            None,
            Log.addon,
            "FusedFilamentDesign is a FreeCAD addon for FFF/FDM 3D-printing design. "
            "It includes various tools to generate geometry for better printability of a part.\n"
            "\n"
            "Check the tooltip for each command to understand how to use them.",
        )


Resources.register_search_paths()
Gui.addCommand("ffDesign_About", ffDesignAboutCommand())
