import unittest

import FreeCAD as App
import FreeCADGui as Gui
import Part

import ffDesign_AutoFillet as AutoFillet
import ffDesign_CounterboreBridges as CounterboreBridges
import ffDesign_HoleWizard as HoleWizard
import ffDesign_RibThreads as RibThreads
import ffDesign_RoofBridge as RoofBridge
import ffDesign_Teardrop as Teardrop
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

    def make_solid_body(self):
        body = self.make_body()
        base = body.newObject("PartDesign::Feature", "Base")
        base.Shape = Part.makeBox(20, 20, 10, App.Vector(-10, -10, 0))
        self.document.recompute()
        self.assert_valid_shape(base)
        return body, base

    def make_supported_sketch(self, body, base, name, geometry):
        sketch = body.newObject("Sketcher::SketchObject", name)
        sketch.AttachmentSupport = [(base, "Face6")]
        sketch.MapMode = "FlatFace"
        sketch.addGeometry(geometry, False)
        self.document.recompute()
        return sketch

    def make_hole(
        self,
        *,
        counterbore=False,
        locations=((0, 0),),
        diameter="4 mm",
        thread_size=None,
    ):
        body, base = self.make_solid_body()
        circles = [
            Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1), 2)
            for x, y in locations
        ]
        profile = self.make_supported_sketch(body, base, "HoleProfile", circles)

        hole = body.newObject("PartDesign::Hole", "Hole")
        hole.Profile = profile
        hole.Diameter = diameter
        hole.Depth = "8 mm"
        if thread_size is not None:
            hole.ThreadType = "ISOMetricProfile"
            matching_sizes = [
                size
                for size in hole.getEnumerationsOfProperty("ThreadSize")
                if size == thread_size or size.startswith(thread_size + "x")
            ]
            self.assertTrue(matching_sizes, thread_size)
            hole.ThreadSize = matching_sizes[0]
            hole.Threaded = True
        if counterbore:
            hole.HoleCutType = "Counterbore"
            hole.HoleCutDiameter = "8 mm"
            hole.HoleCutDepth = "2 mm"
        self.document.recompute()

        self.assert_valid_shape(hole)
        return body, hole

    def assert_valid_shape(self, feature):
        self.assertFalse(feature.Shape.isNull(), feature.Name)
        self.assertTrue(feature.Shape.isValid(), feature.Name)
        self.assertGreater(feature.Shape.Volume, 0, feature.Name)

    def assert_valid_features(self, *features):
        self.document.recompute()
        for feature in features:
            self.assertIsNotNone(feature)
            self.assert_valid_shape(feature)


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

    def test_zip_tie_channels_create_one_valid_pocket_per_point(self):
        body, base = self.make_solid_body()
        sketch = self.make_supported_sketch(
            body,
            base,
            "Locations",
            [
                Part.Point(App.Vector(-4, 0, 0)),
                Part.Point(App.Vector(4, 0, 0)),
            ],
        )

        ZipTieChannels.make_zip_tie_channels_from_sketch(
            body,
            sketch,
            width="3.5 mm",
            thickness="1.5 mm",
            bridge_dia="2.5 mm",
        )

        settings = body.getObject("Locations_ZipTieChannel_Settings")
        first = body.getObject("Locations_ZipTieChannel001")
        second = body.getObject("Locations_ZipTieChannel002")
        self.assertIsNotNone(settings)
        self.assertAlmostEqual(settings.ChannelWidth.Value, 3.5)
        self.assert_valid_features(first, second)
        self.assertLess(second.Shape.Volume, base.Shape.Volume)

        settings.ChannelWidth = "4 mm"
        self.assert_valid_features(first, second)

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

    def test_counterbore_bridges_create_valid_part_design_features(self):
        body, hole = self.make_hole(counterbore=True)

        CounterboreBridges.make_upside_down_counterbores(body, hole)

        bridges_y = body.getObject("Hole_BridgesY")
        bridges_x = body.getObject("Hole_BridgesX")
        self.assertAlmostEqual(hole.LayerHeight.Value, 0.2)
        self.assert_valid_features(bridges_y, bridges_x)
        self.assertLess(bridges_x.Shape.Volume, hole.Shape.Volume)

        hole.LayerHeight = "0.3 mm"
        self.assert_valid_features(bridges_y, bridges_x)

    def test_teardrops_cover_double_sided_and_counterbore_paths(self):
        body, hole = self.make_hole(counterbore=True)

        Teardrop.make_teardrops(
            body,
            hole,
            angle="120 deg",
            rotation="90 deg",
            do_counterbore=True,
            double_sided=True,
        )

        through_hole = body.getObject("Hole_Teardrops")
        counterbore = body.getObject("Hole_TeardropsCb")
        self.assertAlmostEqual(hole.TeardropAngle.Value, 120)
        self.assertAlmostEqual(hole.TeardropRotation.Value, 90)
        self.assert_valid_features(through_hole, counterbore)
        self.assertLess(counterbore.Shape.Volume, hole.Shape.Volume)

        hole.TeardropAngle = "100 deg"
        self.assert_valid_features(through_hole, counterbore)

    def test_roof_bridges_cover_double_sided_and_counterbore_paths(self):
        body, hole = self.make_hole(counterbore=True)

        RoofBridge.make_roof_bridges(
            body,
            hole,
            angle="45 deg",
            rotation="90 deg",
            do_counterbore=True,
            do_doublesided=True,
            bridge_clearance="0.2 mm",
        )

        features = [
            body.getObject("Hole_RoofBridge"),
            body.getObject("Hole_RoofBridge2"),
            body.getObject("Hole_RoofBridgeCb"),
            body.getObject("Hole_RoofBridgeCb2"),
        ]
        self.assertAlmostEqual(hole.RoofBridgeOverhangAngle.Value, 45)
        self.assertAlmostEqual(hole.RoofBridgeClearance.Value, 0.2)
        self.assert_valid_features(*features)
        self.assertLess(features[-1].Shape.Volume, hole.Shape.Volume)

        hole.RoofBridgeRotation = "80 deg"
        self.assert_valid_features(*features)

    def test_rib_thread_template_and_local_generator_recompute(self):
        body, hole = self.make_hole(diameter="3.3 mm", thread_size="M4")
        rib_parameters = RibThreads.RIB_PARAMETERS["ISOMetricProfile"]["M4"]

        RibThreads.make_rib_threads(
            body,
            hole,
            global_template=False,
            rib_param=rib_parameters,
        )

        template = body.getObject("Hole_RibThread_Template")
        ribs = body.getObject("Hole_ThreadRibs")
        entrance = body.getObject("Hole_ThreadEntrance")
        self.assertEqual(len(template.Geometry), 12)
        self.assertAlmostEqual(template.OuterDiameter.Value, 4.4)
        self.assert_valid_features(ribs, entrance)
        self.assertLess(entrance.Shape.Volume, hole.Shape.Volume)

        settings = body.getObject("Hole_RibThread_Settings")
        settings.Rotation = "15 deg"
        self.assert_valid_features(ribs, entrance)

    def test_rib_threads_support_multiple_holes_and_global_template(self):
        body, hole = self.make_hole(
            locations=((-4, 0), (4, 0)),
            diameter="3.3 mm",
            thread_size="M4",
        )
        rib_parameters = RibThreads.RIB_PARAMETERS["ISOMetricProfile"]["M4"]

        RibThreads.make_rib_threads(
            body,
            hole,
            global_template=True,
            rib_param=rib_parameters,
        )

        template = RibThreads.find_rib_template(body, hole, global_template=True)
        merged_profile = body.getObject("Hole_RibThreads")
        ribs = body.getObject("Hole_ThreadRibs")
        entrance = body.getObject("Hole_ThreadEntrance")
        self.assertIsNotNone(
            template,
            [(obj.Name, obj.Label) for obj in self.document.Objects if "RibThread" in obj.Name],
        )
        self.assertEqual(merged_profile.TypeId, "PartDesign::SubShapeBinder")
        self.assert_valid_features(ribs, entrance)
        self.assertIs(
            RibThreads.get_or_create_rib_template(
                body,
                hole,
                global_template=True,
                rib_param=rib_parameters,
            ),
            template,
        )

    def test_all_workbench_commands_and_task_panels_are_registered(self):
        expected_commands = {
            "ffDesign_About",
            "ffDesign_AutoFillet",
            "ffDesign_CounterboreBridges",
            "ffDesign_HoleWizard",
            "ffDesign_RibThreads",
            "ffDesign_RoofBridge",
            "ffDesign_Teardrop",
            "ffDesign_ZipTieChannels",
        }

        self.assertTrue(expected_commands.issubset(set(Gui.listCommands())))
        for panel in (
            "ffDesign_AutoFillet.ui",
            "ffDesign_HoleWizard.ui",
            "ffDesign_RibThreads.ui",
            "ffDesign_RoofBridge.ui",
            "ffDesign_Teardrop.ui",
            "ffDesign_ZipTieChannels.ui",
        ):
            self.assertTrue(Utils.Resources.get_panel(panel).endswith(panel))


if __name__ == "__main__":
    unittest.main()
