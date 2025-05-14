import os

from PySide import QtCore, QtGui

import FreeCADGui as Gui
import FreeCAD as App


class Resources:
    mod_path = os.path.dirname(__file__)
    icons_path = os.path.join(mod_path, "Resources", "icons")
    panels_path = os.path.join(mod_path, "Resources", "panels")

    @classmethod
    def get_panel(cls, name: str) -> str:
        return os.path.join(cls.panels_path, name)

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


class ffDesignError(Exception):
    def __init__(self, message: str, *, dialog: bool = True):
        Log.error(message)
        if dialog:
            # Also show as a modal dialog
            QtGui.QMessageBox.warning(None, Log.addon, f"[{Log.addon}] {message}")
        super().__init__(message)


def warning_confirm_proceed(message: str, question: str = "Proceed anyway?"):
    Log.warning(message)
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


def check_hole_tool_preconditions() -> bool:
    if not App.ActiveDocument:
        return False
    sel = Gui.Selection.getSelection()
    if len(sel) != 1:
        return False
    return sel[0].TypeId == "PartDesign::Hole"


def check_sketch_tool_preconditions() -> bool:
    if not App.ActiveDocument:
        return False
    sel = Gui.Selection.getSelection()
    if len(sel) != 1:
        return False
    return sel[0].TypeId == "Sketcher::SketchObject"


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
        raise ffDesignError("No active document")
    sel = Gui.Selection.getSelection()
    if len(sel) != 1:
        raise ffDesignError("Exactly one Hole feature must be selected.")
    if sel[0].TypeId != "PartDesign::Hole":
        raise ffDesignError(f"Selected object is not a PartDesign Hole feature (is a {sel[0].TypeId!r} instead).")
    return sel[0]


def get_selected_sketch():
    if not App.ActiveDocument:
        raise ffDesignError("No active document")
    sel = Gui.Selection.getSelection()
    if len(sel) != 1:
        raise ffDesignError("Exactly one Sketch must be selected.")
    if sel[0].TypeId != "Sketcher::SketchObject":
        raise ffDesignError(f"Selected object is not a Sketch (is a {sel[0].TypeId!r} instead).")
    return sel[0]


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


def get_sketch_circle_indices(sketch):
    assert_sketch(sketch)

    def is_valid_circle(index, obj):
        return obj.TypeId == "Part::GeomCircle" and not sketch.getConstruction(index)

    return [i for i, obj in enumerate(sketch.Geometry) if is_valid_circle(i, obj)]


def set_shape_binder_styles(binder):
    binder.ViewObject.LineColor = (1.0, 0.84, 0.0, 0.60)
    binder.ViewObject.PointColor = (1.0, 0.84, 0.0, 0.60)
    m = binder.ViewObject.ShapeAppearance[0]
    m.DiffuseColor = (1.0, 0.84, 0.0, 0.60)
    binder.ViewObject.ShapeAppearance = (m,)
    binder.ViewObject.Transparency = 60


def make_sketch_offset_shape_binder(body, template, sketch, suffix: str, center_expr: str, rotation_expr: str):
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
        f"{sketch.Name}.Placement * placement({center_expr}; {rotation_expr})",
    )
    shape_binder.Label = sketch.Label + suffix
    return shape_binder


def check_freecad_version(*, min_version) -> bool:
    current = [int(v.split()[0]) for v in App.Version()[:4]]
    return current >= min_version


def undo_shapebinder_is_safe() -> bool:
    """
    Undoing transactions where shape-binders are created is broken in FreeCAD
    1.0 and a fix will be released in 1.1.
    """
    return check_freecad_version(min_version=[1, 1, 0])


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
