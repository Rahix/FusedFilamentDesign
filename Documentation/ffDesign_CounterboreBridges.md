![ffDesign_CounterboreBridges](../Resources/icons/ffDesign_CounterboreBridges.svg)
## Command: Counterbore Bridges
This command is primarily accessed through the [Hole Wizard](./ffDesign_HoleWizard.md).

This command changes the bottom of a hole's counterbore to be constructed of
layered bridges.  This allows printing the counterbore upside down without
support material.  Check this image for a rough visualization:

![Visualization of upside down counterbore bridges](https://blog.rahix.de/design-for-3d-printing/counterbore.png)

If you want to learn more about this design technique, read [The Overhanging
Counterbore Trick][df3dp-counterbore] from my [Design for 3D-Printing][df3dp]
guide.


## Prerequisites
- A [PartDesign Hole][pd-hole] feature must be selected or the tip of the
  active body must be a [PartDesign Hole][pd-hole].
- The Hole must have a counterbore.

## Usage
Run this command to generate counterbore bridges.

This will generate two additional pockets to make the necessary cutouts,
leaving the intended bridges behind.

The original Hole feature gains a new `LayerHeight` property which can be used
to control the height of each bridge layer.  The default value for
`LayerHeight` is 0.2 mm.

## Parametricity
This feature is parametric with respect to the following variables:

- Hole
  * The depth of the counterbore (`HoleCutDepth` property)
  * The diameter of the counterbore (`HoleCutDiameter` property)
  * The diameter of the Hole itself (`Diameter` property)
  * The bridge layer height (custom `LayerHeight` property)
- Supporting Sketch
  * The position of the circles in the supporting sketch of the original Hole feature.
  * The position of the supporting sketch itself.

This feature is **not** parametric with respect to the following variables.
You will need to delete the feature and recreate it to update these variables:

- Supporting Sketch
  * The number of circles in the supporting sketch of the original Hole feature.

[pd-hole]: https://wiki.freecad.org/PartDesign_Hole
[df3dp-counterbore]: https://blog.rahix.de/design-for-3d-printing/#the-overhanging-counterbore-trick
[df3dp]: https://blog.rahix.de/design-for-3d-printing/
