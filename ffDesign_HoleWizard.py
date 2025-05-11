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
        has_counterbore = self.hole.HoleCutType in [
            "Counterbore",
            "ISO 4762",
            "ISO 14583 (partial)",
            "DIN 7984",
            "ISO 4762 + 7089",
            "ISO 14583",
            "ISO 12474",
        ]
        is_threaded = self.hole.Threaded

        self.form.AddCounterboreBridges.setEnabled(has_counterbore)
        self.form.AddRibThreads.setEnabled(is_threaded)

    def addCounterboreBridges(self):
        FreeCADGui.Control.closeDialog()
        FreeCADGui.runCommand("ffDesign_CounterboreBridges")

    def addRibThreads(self):
        Utils.Log.warning("TODO: Add rib threads")
        FreeCADGui.Control.closeDialog()

    def addRoofBridge(self):
        Utils.Log.warning("TODO: Add roof bridge")
        FreeCADGui.Control.closeDialog()

    def addTeardropShape(self):
        Utils.Log.warning("TODO: Add teardrop shape")
        FreeCADGui.Control.closeDialog()

    def accept(self):
        FreeCADGui.Control.closeDialog()

    def reject(self):
        FreeCADGui.Control.closeDialog()


class HoleWizardCommand:
    def GetResources(self):
        return {
            "Pixmap": Utils.Resources.get_icon("ffDesign_HoleWizard.svg"),
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
        hole = Utils.get_selected_hole()
        if hole is not None:
            dialog = HoleWizardTaskPanel(hole)
            FreeCADGui.Control.showDialog(dialog)

    def IsActive(self):
        return Utils.check_hole_tool_preconditions()


FreeCADGui.addCommand("ffDesign_HoleWizard", HoleWizardCommand())
