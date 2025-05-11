import os

import FreeCADGui
import FreeCAD


mod_path = os.path.dirname(__file__)
icons_path = os.path.join(mod_path, "Resources", "icons")
panels_path = os.path.join(mod_path, "Resources", "panels")


class HoleWizardTaskPanel:
    def __init__(self, hole):
        assert hole.TypeId == "PartDesign::Hole"
        self.hole = hole
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(panels_path, "ffDesign_HoleWizard.ui"))

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
        print("[ffDesign] TODO: Add counterbore bridges")
        FreeCADGui.Control.closeDialog()

    def addRibThreads(self):
        print("[ffDesign] TODO: Add rib threads")
        FreeCADGui.Control.closeDialog()

    def addRoofBridge(self):
        print("[ffDesign] TODO: Add roof bridge")
        FreeCADGui.Control.closeDialog()

    def addTeardropShape(self):
        print("[ffDesign] TODO: Add teardrop shape")
        FreeCADGui.Control.closeDialog()

    def accept(self):
        FreeCADGui.Control.closeDialog()

    def reject(self):
        FreeCADGui.Control.closeDialog()


class HoleWizardCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(icons_path, "ffDesign_HoleWizard.svg"),
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
        if not FreeCAD.ActiveDocument:
            print("[ffDesign] No active document.")
            return
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) != 1:
            print("[ffDesign] Exactly one Hole feature must be selected")
            return
        if sel[0].TypeId != "PartDesign::Hole":
            print("[ffDesign] Selected object is not a PartDesign Hole feature")
            return
        dialog = HoleWizardTaskPanel(sel[0])
        FreeCADGui.Control.showDialog(dialog)

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) != 1:
            return False
        return sel[0].TypeId == "PartDesign::Hole"


FreeCADGui.addCommand("ffDesign_HoleWizard", HoleWizardCommand())
