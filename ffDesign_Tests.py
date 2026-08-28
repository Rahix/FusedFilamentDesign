import abc
import unittest
import pathlib
import os

import FreeCAD as App
import FreeCADGui as Gui
import BOPTools.SplitFeatures

from PySide import QtCore

import ffDesign_Utils as Utils

import ffDesign_CounterboreBridges
import ffDesign_RibThreads
import ffDesign_RoofBridge

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


class PartialHoleProfiles(ffDesignTestCase_Fc11):
    test_document = "PartialHoleProfile.FCStd"

    @unittest.expectedFailure
    def test_plausibility(self):
        self.prepare_regression_test()
        self.assert_expected_body()

    def test_partial_profile(self):
        """
        Test that a PartDesign_Hole using a partial sketch as its profile is
        correctly handled by the counterbore bridges tool.
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


class RibThreads_Fc11(ffDesignTestCase_Fc11):
    test_document = "TapHoles.FCStd"

    def thread_test(self, thread_type: str, thread_size: str):
        # Prep for the next test
        App.closeDocument(self.doc.Name)
        self.setUp()

        try:
            self.prepare_regression_test()

            hole = self.body.Tip
            Utils.assert_hole(hole)

            hole.ThreadType = thread_type
            hole.ThreadSize = thread_size
            App.ActiveDocument.recompute()

            dialog = ffDesign_RibThreads.RibThreadsTaskPanel(self.body, hole)
            Gui.Control.showDialog(dialog)
            dialog.accept()
        except Exception as e:
            Utils.Log.warning(f"Test failure during thread {thread_type} {thread_size}")
            raise e from None

    def test_known_metric(self):
        for thread in ffDesign_RibThreads.RIB_PARAMETERS["ISOMetricProfile"]:
            if "x" not in thread or thread == "M6x1":
                # This is one of the legacy thread names, skip
                continue

            self.thread_test("ISOMetricProfile", thread)

    def test_known_unc(self):
        for thread in ffDesign_RibThreads.RIB_PARAMETERS["UNC"]:
            self.thread_test("UNC", thread)


class RoofBridges(ffDesignTestCase):
    test_document = "RoofBridges.FCStd"

    def apply_roof_bridge_for_hole(
        self,
        hole_name: str,
        *,
        double_sided=None,
        include_counterbore=None,
        clearance=None,
        angle_60=False,
        ignore_missing=False,
    ):
        hole = self.body.getObject(hole_name)
        Utils.assert_hole(hole)

        dialog = ffDesign_RoofBridge.RoofBridgeTaskPanel(self.body, hole)
        Gui.Control.showDialog(dialog)

        if double_sided is not None:
            if double_sided:
                dialog.form.DoubleSided.setCheckState(QtCore.Qt.CheckState.Checked)
            else:
                dialog.form.DoubleSided.setCheckState(QtCore.Qt.CheckState.Unchecked)

        if include_counterbore is not None:
            if include_counterbore:
                dialog.form.DoCounterbore.setCheckState(QtCore.Qt.CheckState.Checked)
            else:
                dialog.form.DoCounterbore.setCheckState(QtCore.Qt.CheckState.Unchecked)

        if clearance is not None:
            dialog.form.BridgeClearance.setProperty("rawValue", clearance)

        if angle_60:
            dialog.form.Angle60.toggle()

        dialog.accept()

    def test_roof_bridges(self):
        self.prepare_regression_test()

        self.apply_roof_bridge_for_hole("Hole")
        self.apply_roof_bridge_for_hole("Hole001", double_sided=True, angle_60=True)
        self.apply_roof_bridge_for_hole("Hole002", double_sided=True)
        self.apply_roof_bridge_for_hole("Hole003", include_counterbore=False, clearance=0.6)

        self.body.getObject("Hole002").RoofBridgeRotation = "0deg"
        App.ActiveDocument.recompute()

        self.assert_expected_body()
