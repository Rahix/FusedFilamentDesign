# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to

- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
- [0 Versioning](https://0ver.org)
- [Calendar Versioning](https://calver.org/) with the scheme `0.YY.WW#` (with `#` being the patch version)

## [Unreleased]
### Added
- Rib threads now have slightly better support for UTS threads (UNC, UNF,
  UNEF).  We still do not ship many pre-defined parameters, but you can now use
  the dialog to define your own and will get guidance whether your parameters
  actually fit together ([#45]).

### Fixed
- Fixed rib threads not extracting the drill diameter from the selected
  `PartDesign_Hole` when no rib parameters are predefined ([#45]).

[#45]: https://github.com/rahix/FusedFilamentDesign/pull/45


## [0.26.100] - 2026-03-06
### Added
- Teardrop holes can now optionally also create a teardrop for a counterbore ([#40]).
- Teardrop holes can now optionally be double-sided ([#41]).  This is useful to
  make parts more independent of print orientation.
- Roof bridges can now optionally be double-sided ([#42]).  This is useful to
  make parts more independent of print orientation.

[#40]: https://github.com/rahix/FusedFilamentDesign/pull/40
[#41]: https://github.com/rahix/FusedFilamentDesign/pull/41
[#42]: https://github.com/rahix/FusedFilamentDesign/pull/42


## [0.25.510] - 2025-12-19
### Added
- Added rib thread parameters for 1/4-20 UNC thread ([#37]).

[#37]: https://github.com/rahix/FusedFilamentDesign/pull/37


## [0.25.480] - 2025-11-28
### Fixed
- Fixed zip-tie channels being off center from the supporting sketch on the
  latest FreeCAD 1.1 development builds ([#36]).

[#36]: https://github.com/rahix/FusedFilamentDesign/pull/36


## [0.25.380] - 2025-09-20
### Fixed
- Fixed rib-threads being broken on the latest FreeCAD 1.1 development builds ([#32]).

### Changed
- Optimized the default rib-thread parameters for M3 threads ([`81fa0e89311b`]).

[`81fa0e89311b`]: https://github.com/rahix/FusedFilamentDesign/commit/81fa0e89311b4497c465ada053637e44326a0a50
[#32]: https://github.com/rahix/FusedFilamentDesign/pull/32


## [0.25.350] - 2025-08-30
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

[Unreleased]: https://github.com/rahix/FusedFilamentDesign/compare/v0.26.100...HEAD
[0.26.100]: https://github.com/rahix/FusedFilamentDesign/compare/v0.25.510...v0.26.100
[0.25.510]: https://github.com/rahix/FusedFilamentDesign/compare/v0.25.480...v0.25.510
[0.25.480]: https://github.com/rahix/FusedFilamentDesign/compare/v0.25.380...v0.25.480
[0.25.380]: https://github.com/rahix/FusedFilamentDesign/compare/v0.25.350...v0.25.380
[0.25.350]: https://github.com/rahix/FusedFilamentDesign/compare/v0.25.250...v0.25.350
[0.25.250]: https://github.com/rahix/FusedFilamentDesign/compare/v0.25.220...v0.25.250
[0.25.220]: https://github.com/rahix/FusedFilamentDesign/compare/v0.25.200...v0.25.220
[0.25.200]: https://github.com/rahix/FusedFilamentDesign/releases/tag/v0.25.200
