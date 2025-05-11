import os

from PySide import QtCore, QtGui

import FreeCADGui
import FreeCAD


class Resources:
    mod_path = os.path.dirname(__file__)
    icons_path = os.path.join(mod_path, "Resources", "icons")
    panels_path = os.path.join(mod_path, "Resources", "panels")

    @classmethod
    def get_icon(cls, name: str) -> str:
        return os.path.join(cls.icons_path, name)

    @classmethod
    def get_panel(cls, name: str) -> str:
        return os.path.join(cls.panels_path, name)


class Log:
    addon = "FusedFilamentDesign"

    @classmethod
    def error(cls, msg: str) -> None:
        FreeCAD.Console.PrintError(f"[{cls.addon}] {msg}\n")
        # Errors also get shown as a modal dialog
        QtGui.QMessageBox.warning(None, cls.addon, f"[{cls.addon}] {msg}")

    @classmethod
    def warning(cls, msg: str) -> None:
        FreeCAD.Console.PrintWarning(f"[{cls.addon}] {msg}\n")

    @classmethod
    def info(cls, msg: str) -> None:
        FreeCAD.Console.PrintMessage(f"[{cls.addon}] {msg}\n")


def check_hole_tool_preconditions() -> bool:
    if not FreeCAD.ActiveDocument:
        return False
    sel = FreeCADGui.Selection.getSelection()
    if len(sel) != 1:
        return False
    return sel[0].TypeId == "PartDesign::Hole"


def get_selected_hole():
    if not FreeCAD.ActiveDocument:
        Log.error("No active document.")
        return None
    sel = FreeCADGui.Selection.getSelection()
    if len(sel) != 1:
        Log.error("Exactly one Hole feature must be selected.")
        return None
    if sel[0].TypeId != "PartDesign::Hole":
        Log.error(f"Selected object is not a PartDesign Hole feature (is a {sel[0].TypeId!r} instead).")
        return None
    return sel[0]
