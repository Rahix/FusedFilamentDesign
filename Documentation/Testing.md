## Running the ffDesign Testsuite
FusedFilamentDesign has a small testsuite to check correct behavior of the
commands. This testsuite uses a lot of prepared FreeCAD documents which are
stored separately in the [ffDesign_TestData] repository.

### Test Architecture
The tests are mainly regression tests where a prepared body is modified by one
of ffDesign's commands and then the resulting shape is compared against a
reference.

This comparison is done by performing an XOR of the Body shapes and checking
that the remaining shape is empty.

Each test document for such regression tests contains one Body named
`BodyUnderTest` (the prepared one) and one Body named `BodyExpected` (the
expected final shape).

### Downloading test documents
Before running the testsuite, you must download the test documents from
[ffDesign_TestData].

The ffDesign_TestData repository uses [git-lfs] for storing the FreeCAD
documents. If you do not yet have git-lfs installed, download it from the
project homepage: <https://git-lfs.com/>

Then run this command to enable git-lfs for your user account:

```bash
git lfs install
```

You are now ready to download the ffDesign_TestData. Navigate to the addon
directory of FusedFilamentDesign and clone the test data:

```bash
# May differ for your system
cd ~/.FreeCAD/Mod/FusedFilamentDesign/

git clone https://github.com/Rahix/ffDesign_TestData
```

You are now ready to run the testsuite:

### Running the testsuite
Run the full testsuite using the following command:

```bash
FreeCAD -t ffDesign_Tests
```

FreeCAD will show failing tests in the terminal output.

### Troubleshooting failing tests
If you want to see why a specific test failed, you can instruct FreeCAD to stay
open and tell the testsuite to not discard the test document. **This only works
when running a single test at a time!**

```bash
FFDESIGN_KEEP_TEST_DOC=1 FreeCAD -r ffDesign_Tests.HoleLocations.test_construction_and_non_defining
```

(Note the `-r` instead of `-t`)


[ffDesign_TestData]: https://github.com/Rahix/ffDesign_TestData
[git-lfs]: https://git-lfs.com/
