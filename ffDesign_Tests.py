import unittest

import FreeCAD as App
import Part

import ffDesign_AutoFillet as AutoFillet
import ffDesign_RoofBridge as RoofBridge
import ffDesign_Utils as Utils
import ffDesign_ZipTieChannels as ZipTieChannels


class DocumentTestCase(unittest.TestCase):
    document_name = "FusedFilamentDesignTests"

    def setUp(self):
        if self.document_name in App.listDocuments():
            App.closeDocument(self.document_name)
        self.document = App.newDocument(self.document_name)

    def tearDown(self):
        if self.document_name in App.listDocuments():
            App.closeDocument(self.document_name)

    def make_body(self):
        return self.document.addObject("PartDesign::Body", "Body")


class GeometryTests(DocumentTestCase):
    def test_get_sketch_locations_ignores_construction_geometry(self):
        body = self.make_body()
        sketch = body.newObject("Sketcher::SketchObject", "Locations")
        sketch.addGeometry(Part.Point(App.Vector(1, 2, 0)), False)
        sketch.addGeometry(Part.Circle(App.Vector(3, 4, 0), App.Vector(0, 0, 1), 1), False)
        construction_index = sketch.addGeometry(Part.Point(App.Vector(5, 6, 0)), True)

        locations = Utils.get_sketch_locations(
            sketch,
            Utils.MASK_PROFILE_POINTS | Utils.MASK_PROFILE_CIRCLES,
        )

        self.assertTrue(sketch.getConstruction(construction_index))
        self.assertEqual(len(locations), 2)
        self.assertEqual(locations[0].x_expr, "Locations.Geometry[0].X * 1mm")
        self.assertEqual(locations[1].vector_expr, "Locations.Geometry[1].Center")

    def test_auto_fillet_creates_a_valid_feature(self):
        body = self.make_body()
        source = body.newObject("PartDesign::Feature", "Box")
        source.Shape = Part.makeBox(10, 10, 10)
        self.document.recompute()

        AutoFillet.make_auto_fillets(body, axis="Z", radius="1 mm")
        self.document.recompute()

        result = body.Tip
        self.assertEqual(result.TypeId, "PartDesign::Fillet")
        self.assertFalse(result.Shape.isNull())
        self.assertTrue(result.Shape.isValid())
        self.assertGreater(result.Shape.Volume, 0)
        self.assertLess(result.Shape.Volume, source.Shape.Volume)

    def test_zip_tie_template_has_the_expected_profile(self):
        body = self.make_body()
        original = body.newObject("Sketcher::SketchObject", "Locations")

        template = ZipTieChannels.make_zip_tie_channel_template(
            body,
            original,
            thickness="1.5 mm",
            bridge_dia="2.5 mm",
        )
        self.document.recompute()

        radii = sorted(geometry.Radius for geometry in template.Geometry if hasattr(geometry, "Radius"))
        self.assertEqual(len(template.Geometry), 4)
        self.assertEqual(len(template.Constraints), 12)
        self.assertEqual(len(radii), 2)
        self.assertAlmostEqual(radii[0], 1.25)
        self.assertAlmostEqual(radii[1], 2.75)
        self.assertFalse(template.Shape.isNull())
        self.assertTrue(template.Shape.isValid())

    def test_roof_bridge_profile_recomputes(self):
        body = self.make_body()
        sketch = body.newObject("Sketcher::SketchObject", "RoofBridge")
        location = Utils.LocationExprSet(
            vector_expr="vector(0 mm, 0 mm, 0 mm)",
            x_expr="0 mm",
            y_expr="0 mm",
        )

        RoofBridge.make_parametric_roof_bridge(
            sketch,
            hole_loc=location,
            diameter_expr="6 mm",
            angle_expr="45 deg",
            rotation_expr="90 deg",
            clearance_expr="0.2 mm",
        )
        self.document.recompute()

        self.assertEqual(len(sketch.Geometry), 5)
        self.assertEqual(len(sketch.Constraints), 13)
        self.assertFalse(sketch.Shape.isNull())
        self.assertTrue(sketch.Shape.isValid())


if __name__ == "__main__":
    unittest.main()
