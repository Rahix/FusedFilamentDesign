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


def warning_confirm_proceed(message: str):
    Log.warning(message)
    reply = QtGui.QMessageBox.question(None, Log.addon, f"[{Log.addon}] {message}\nProceed anyway?")
    if reply != QtGui.QMessageBox.Yes:
        raise ffDesignError("Aborted on user request due to previous warning", dialog=False)


def assert_body(obj):
    assert obj.TypeId == "PartDesign::Body"


def assert_hole(obj):
    assert obj.TypeId == "PartDesign::Hole"


def assert_sketch(obj):
    assert obj.TypeId == "Sketcher::SketchObject"


def check_hole_tool_preconditions() -> bool:
    if not App.ActiveDocument:
        return False
    sel = Gui.Selection.getSelection()
    if len(sel) != 1:
        return False
    return sel[0].TypeId == "PartDesign::Hole"


def get_active_part_design_body_for_feature(obj):
    active_body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
    if active_body is None:
        raise ffDesignError("No active PartDesign Body")
    assert_body(active_body)

    if obj.getParent() != active_body:
        raise ffDesignError("Selected feature is not part of the active PartDesign body!")

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


Resources.register_search_paths()
