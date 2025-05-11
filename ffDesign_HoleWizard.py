import FreeCADGui
import FreeCAD

import ffDesign_Utils as Utils


class HoleWizardTaskPanel:
    def __init__(self, hole):
        assert hole.TypeId == "PartDesign::Hole"
        self.hole = hole
        self.form = FreeCADGui.PySideUic.loadUi(Utils.Resources.get_panel("ffDesign_HoleWizard.ui"))

        self.form.AddCounterboreBridges.clicked.connect(self.addCounterboreBridges)
        self.form.AddRibThreads.clicked.connect(self.addRibThreads)
        self.form.AddRoofBridge.clicked.connect(self.addRoofBridge)
        self.form.AddTeardropShape.clicked.connect(self.addTeardropShape)

        self.updateCommandAvailability()

    def updateCommandAvailability(self):
        has_counterbore_maybe = Utils.hole_has_counterbore_maybe(self.hole)
        is_threaded = self.hole.Threaded

        self.form.AddCounterboreBridges.setEnabled(has_counterbore_maybe)
        self.form.AddRibThreads.setEnabled(is_threaded)

        # TODO: These are not yet implemented, so always disable them for now
        self.form.AddTeardropShape.setEnabled(False)
        self.form.AddRoofBridge.setEnabled(False)

    def addCounterboreBridges(self):
        FreeCADGui.Control.closeDialog()
        FreeCADGui.runCommand("ffDesign_CounterboreBridges")

    def addRibThreads(self):
        FreeCADGui.Control.closeDialog()
        Utils.Log.error("TODO: Add rib threads")

    def addRoofBridge(self):
        FreeCADGui.Control.closeDialog()
        Utils.Log.error("TODO: Add roof bridge")

    def addTeardropShape(self):
        FreeCADGui.Control.closeDialog()
        Utils.Log.error("TODO: Add teardrop shape")

    def accept(self):
        FreeCADGui.Control.closeDialog()

    def reject(self):
        FreeCADGui.Control.closeDialog()


class HoleWizardCommand:
    def GetResources(self):
        return {
            "Pixmap": "icons:ffDesign_HoleWizard.svg",
            "MenuText": FreeCAD.Qt.translate("ffDesign", "Hole Wizard"),
            "ToolTip": FreeCAD.Qt.translate(
                "ffDesign",
                "A wizard for adding various FFF 3d-printing geometry to PartDesign Hole features.\n"
                "1. Select a Hole feature in the active body.\n"
                "2. Run this command.\n"
                "3. Select the kind of geometry you want to add in the task panel.",
            ),
        }

    def Activated(self):
        try:
            hole = Utils.get_selected_hole()
            dialog = HoleWizardTaskPanel(hole)
            FreeCADGui.Control.showDialog(dialog)
        except Utils.ffDesignError:
            pass

    def IsActive(self):
        return Utils.check_hole_tool_preconditions()


FreeCADGui.addCommand("ffDesign_HoleWizard", HoleWizardCommand())
