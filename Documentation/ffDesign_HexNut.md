![ffDesign_HexNut](../Resources/icons/ffDesign_HexNut.svg)
## Command: Hex Nut Hole
This command cuts a hexagonal recess at one end of a hole, so that a hex nut
can be captured inside the part.  This is useful for embedding nuts in printed
parts without a press fit.

## Prerequisites
- A [PartDesign Hole][pd-hole] feature must be selected or the tip of the
  active body must be a [PartDesign Hole][pd-hole].

## Usage
Run this command to generate a hex nut recess for the selected Hole feature.  A
dialog will open in the [Task Panel][task-panel] where you can control the
generation.

- **Hex Nut Radius**: The radius from the hole center to a corner of the hex
  nut.  This is the radius of the circle around the hexagon, not the distance
  across the flats.
- **Hex Hole Depth**: The depth of the hexagonal recess, measured from the
  selected face.
- **Start on the opposite face**: When checked, the recess starts on the
  opposite face of the part instead of on the hole entry face.  The tool
  determines the location of this face from the shape of the part.
- **Rotate by 30 degrees**: When checked, the hexagon turns
  by 30 degrees.  A vertex then points where a flat side faces in the default
  orientation.  A regular hexagon looks the same after a 60 degree turn, so 30
  degrees is the useful angle.

Click "OK" to then proceed generating the recess.  This will create the
following features:

- A pocket for the hex nut recesses of all holes in this Hole feature.  When
  the recess starts on the opposite face, each hole gets its own pocket.

Additionally, two properties will be added to the original Hole feature which
can be used to parametrically control the recesses:

- `HexNutRadius` is the radius from the hole center to a corner of the hex nut.
- `HexNutDepth` is the depth of the hexagonal recess.

## Parametricity
This feature is parametric with respect to the following variables:

- Hole
  * The position of the circles in the supporting sketch of the original Hole feature.
  * The position of the supporting sketch itself.
- Hex Nut Properties of the Hole
  * Hex nut radius (`HexNutRadius` property)
  * Hex nut recess depth (`HexNutDepth` property)

This feature is **not** parametric with respect to the following variables.
You will need to delete the feature and recreate it to update these variables:

- Supporting Sketch
  * The number of circles in the supporting sketch of the original Hole feature.
- Hole
  * The direction of the hole (`Reversed` property).
  * The choice between the hole entry face and the opposite face.
  * The rotation of the hexagon (vertex up or side up).

[pd-hole]: https://wiki.freecad.org/PartDesign_Hole
[task-panel]: https://wiki.freecad.org/Task_panel
