![ffDesign_HoleWizard](../Resources/icons/ffDesign_HoleWizard.svg)
## Command: Hole Wizard
The _Hole Wizard_ is a convenient tool to improve [PartDesign Hole][pd-hole]
features for printability.  It is essentially just a simple entry-point for
selecting one of the following tools:

- [<img src="../Resources/icons/ffDesign_CounterboreBridges.svg" height="12" /> Counterbore Bridges](./ffDesign_CounterboreBridges.md)
- [<img src="../Resources/icons/ffDesign_RibThreads.svg" height="12" /> Thread Forming Ribs](./ffDesign_RibThreads.md)
- [<img src="../Resources/icons/ffDesign_Teardrop.svg" height="12" /> Teardrop Shape](./ffDesign_Teardrop.md)
- [<img src="../Resources/icons/ffDesign_RoofBridge.svg" height="12" /> Roof Bridge](./ffDesign_RoofBridge.md)

## Prerequisites
- A [PartDesign Hole][pd-hole] feature must be selected or the tip of the
  active body must be a [PartDesign Hole][pd-hole].

## Usage
Run this command, then select the appropriate tool in the [Task
Panel][task-panel].  Only tools whose prerequisites are met can be used.  The
tooltip of each button gives info on the respective prerequisites.

[pd-hole]: https://wiki.freecad.org/PartDesign_Hole
[task-panel]: https://wiki.freecad.org/Task_panel
