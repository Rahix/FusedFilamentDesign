from PySide import QtCore, QtGui

import FreeCADGui as Gui
import FreeCAD as App
import Part

import ffDesign_Utils as Utils


def make_auto_fillets(
    body,
    *,
    axis: str = "X",
    radius: App.Units.Quantity,
):
    Utils.assert_body(body)

    radius = App.Units.Quantity(radius)
    assert radius.Unit.Type == "Length"

    tip = body.Tip
    if tip is None:
        raise Utils.ffDesignError("Active body has no tip feature!")

    def check_tangent_vertical(tangent) -> bool:
        if axis == "X":
            return abs(tangent.x) >= 0.5
        elif axis == "Y":
            return abs(tangent.y) >= 0.5
        elif axis == "Z":
            return abs(tangent.z) >= 0.5
        else:
            raise Utils.ffDesignError(f"Unknown axis {axis!r} (must be X, Y, or Z)")

    filtered_edges = []
    for idx, edge in enumerate(tip.Shape.Edges, start=1):
        param = edge.ParameterRange
        tangent_start = edge.tangentAt(param[0])
        tangent_mid = edge.tangentAt((param[0] + param[1]) / 2)
        tangent_end = edge.tangentAt(param[1])

        # We accept edges where all three tangents are more than 45°
        if (
            check_tangent_vertical(tangent_start)
            and check_tangent_vertical(tangent_mid)
            and check_tangent_vertical(tangent_end)
        ):
            filtered_edges.append(f"Edge{idx}")

    if filtered_edges == []:
        raise Utils.ffDesignError("Did not find any vertical edges in the active body!")

    fillet = body.newObject("PartDesign::Fillet", "VerticalFillets")
    fillet.Base = (tip, filtered_edges)
    fillet.Radius = radius
    fillet.Label = "VerticalFillets"
    fillet.recompute()


class AutoFilletTaskPanel:
    def __init__(self, body):
        Utils.assert_body(body)

        self.body = body
        self.form = Gui.PySideUic.loadUi(Utils.Resources.get_panel("ffDesign_AutoFillet.ui"))

        self.form.FilletRadius.setProperty("rawValue", 1.0)

        # Z axis is the default vertical axis
        self.form.AxisZ.toggle()

    def accept(self):
        try:
            Gui.Control.closeDialog()

            if self.form.AxisX.isChecked():
                axis = "X"
            elif self.form.AxisY.isChecked():
                axis = "Y"
            elif self.form.AxisZ.isChecked():
                axis = "Z"
            else:
                Utils.Log.warning("No axis radio-button selected? Defaulting to Z axis.")
                axis = "Z"

            try:
                App.ActiveDocument.openTransaction("Automatic vertical fillets")
                make_auto_fillets(self.body, axis=axis, radius=self.form.FilletRadius.property("value"))
                App.ActiveDocument.recompute()
                App.ActiveDocument.commitTransaction()
            except Exception as e:
                App.ActiveDocument.abortTransaction()
                raise e from None
        except Utils.ffDesignError as e:
            e.emit_to_user()

    def reject(self):
        Gui.Control.closeDialog()


class AutoFilletCommand:
    def GetResources(self):
        return {
            "Pixmap": "icons:ffDesign_AutoFillet.svg",
            "MenuText": App.Qt.translate("ffDesign", "Add fillets to all vertical edges"),
            "ToolTip": App.Qt.translate(
                "ffDesign",
                "Automatically add a fillet to all vertical edges of a part.\n"
                "An edge is considered vertical if it is angled upward more than 45°.\n"
                "1. Activate a PartDesign body.\n"
                "2. Run this command.\n"
                "3. Select 'vertical' axis (printer Z) of your body.\n"
                "4. Enter fillet radius.\n",
            ),
        }

    def Activated(self):
        try:
            active_body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
            if active_body is None:
                raise Utils.ffDesignError("No PartDesign body active!")

            dialog = AutoFilletTaskPanel(active_body)
            Gui.Control.showDialog(dialog)
        except Utils.ffDesignError as e:
            e.emit_to_user()

    def IsActive(self):
        return Gui.ActiveDocument.ActiveView.getActiveObject("pdbody") is not None


Gui.addCommand("ffDesign_AutoFillet", AutoFilletCommand())
