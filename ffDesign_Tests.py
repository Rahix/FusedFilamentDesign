import abc
import unittest
import pathlib
import os

import FreeCAD as App
import FreeCADGui as Gui
import BOPTools.SplitFeatures

import ffDesign_Utils as Utils

import ffDesign_CounterboreBridges
import ffDesign_RibThreads

TEST_DOCUMENTS_PATH = "ffDesign_TestData"


def get_test_dir() -> pathlib.Path:
    test_documents_repo = pathlib.Path(__file__).parent / TEST_DOCUMENTS_PATH

    if not test_documents_repo.is_dir():
        Utils.Log.error(f"""\
Test documents repository {test_documents_repo.name} does not exist! Maybe you need to download it first?

Full path: {test_documents_repo}

Please read the documentation of {Utils.Log.addon} to understand how to prepare for running this testsuite.""")
        raise Exception(f"{Utils.Log.addon} test documents directory is missing")

    # Depending on the FreeCAD version, we select the relevant subdirectory.
    subdir_name = "FreeCAD_1.0"
    if Utils.check_freecad_version(min_version=[1, 1, 0]):
        subdir_name = "FreeCAD_1.1"

    return test_documents_repo / subdir_name


class ffDesignTestCase(unittest.TestCase, abc.ABC):
    test_document = None  # Name of the test document for this testcase

    def setUp(self):
        # Skip all the ffDesign dialogs during test runs
        Utils.SKIP_ALL_DIALOGS = True

        test_document_path = get_test_dir() / self.test_document
        if not test_document_path.exists():
            Utils.Log.error(f"""\
Test document {test_document_path.name} is missing.

Do you have the latest version of the test documents repository?

Full path: {test_document_path}

Please read the documentation of {Utils.Log.addon} to understand how to prepare for running this testsuite.""")
            raise Exception(f"{test_document_path.name} is missing")

        self.doc = App.openDocument(str(test_document_path))

    def tearDown(self):
        # Re-enable ffDesign dialogs after the test completes
        Utils.SKIP_ALL_DIALOGS = False

        # You can use FFDESIGN_KEEP_TEST_DOC=1 to keep the test document open to inspect it.
        # Only makes sense when running tests with `-r` instead of `-t`.
        # You should probably only use this when running a single test case.
        if os.environ.get("FFDESIGN_KEEP_TEST_DOC", default="0") == "0":
            App.closeDocument(self.doc.Name)

    def prepare_regression_test(self):
        self.body = self.doc.getObjectsByLabel("BodyUnderTest")[0]
        self.body_expected = self.doc.getObjectsByLabel("BodyExpected")[0]

        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", self.body)

    def assert_expected_body(self):
        # Move the body_expected to the origin where the other body should already be
        self.body_expected.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 0, 1), 0))

        # Run a Part XOR operation between the two bodies to find differences
        xor_body = BOPTools.SplitFeatures.makeXOR(name="Comparison_XOR")
        xor_body.Objects = [self.body, self.body_expected]
        xor_body.Proxy.execute(xor_body)

        self.body_expected.ViewObject.hide()
        self.body.ViewObject.Transparency = 70
        # Make the xor_body bright red
        xor_body.ViewObject.ShapeAppearance = [App.Material(DiffuseColor=(255, 0, 0, 255))]

        # Check that the resulting shape is utterly empty
        self.assertEqual(xor_body.Shape.Volume, 0, "Detected differences between resulting and expected shape")
        self.assertEqual(len(xor_body.Shape.Vertexes), 0, "Detected differences between resulting and expected shape")


class ffDesignTestCase_Fc11(ffDesignTestCase):
    """A testcase that only runs on FreeCAD >1.1."""

    def setUp(self):
        if not Utils.check_freecad_version(min_version=[1, 1, 0]):
            raise unittest.SkipTest("This testcase only works on FreeCAD >=1.1")

        super().setUp()


class HoleLocations(ffDesignTestCase_Fc11):
    test_document = "HoleLocations.FCStd"

    @unittest.expectedFailure
    def test_plausibility(self):
        self.prepare_regression_test()
        self.assert_expected_body()

    def test_construction_and_non_defining(self):
        """
        Test that hole locations are correctly inferred from a sketch with both
        construction circles and non-defining external geometry.
        """
        self.prepare_regression_test()
        ffDesign_CounterboreBridges.CounterboreBridgesCommand().Activated()
        self.assert_expected_body()


class RibThreads(ffDesignTestCase):
    test_document = "TapHoles.FCStd"

    def test_generate_rib_threads(self):
        """
        Smoke tests that we can generate rib threads for the predefined metric M4 tap holes.
        """
        self.prepare_regression_test()

        # TODO: Use the command rather than directly generating using the addon function
        hole = self.body.Tip
        Utils.assert_hole(hole)

        ffDesign_RibThreads.verify_rib_thread_suitability(hole)

        dialog = ffDesign_RibThreads.RibThreadsTaskPanel(self.body, hole)
        Gui.Control.showDialog(dialog)
        dialog.accept()

        # The file expects an additional rotation of the rib threads to be present
        varset = self.body.getObject("Hole_RibThread_Settings")
        varset.Rotation = "90deg"
        App.ActiveDocument.recompute()

        self.assert_expected_body()
