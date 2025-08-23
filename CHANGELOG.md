# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to

- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
- [0 Versioning](https://0ver.org)
- [Calendar Versioning](https://calver.org/) with the scheme `0.YY.WW#` (with `#` being the patch version)

## [Unreleased]
### Added
- Added the `ffDesign_AutoFillet` command to automatically create fillets on
  all vertical edges of a part ([#30]).

[#30]: https://github.com/rahix/FusedFilamentDesign/pull/30


## [0.25.250] - 2025-06-17
### Fixed
- Fixed the tools from the _Hole Wizard_ not using points and arcs in FreeCAD
  1.1, when the Hole feature's `Base Profile Type` was set to such a value.


## [0.25.220] - 2025-05-30
### Fixed
- Fixed the layout of the buttons in the _Hole Wizard_, making them more consistent.
- Fixed `check_freecad_version()` failing on FreeCAD versions that have an
  `Unknown` git version (Gentoo for example).


## [0.25.200] - 2025-05-15
Initial release 🎉

[Unreleased]: https://github.com/rahix/FusedFilamentDesign/compare/v0.25.250...HEAD
[0.25.250]: https://github.com/rahix/FusedFilamentDesign/compare/v0.25.220...v0.25.250
[0.25.220]: https://github.com/rahix/FusedFilamentDesign/compare/v0.25.200...v0.25.220
[0.25.200]: https://github.com/rahix/FusedFilamentDesign/releases/tag/v0.25.200
