# Changelog

## 2026-04-01

### Fixed
- Cover idle state now reports position 50 (midway) instead of 100, so HA shows both open and close buttons when the shutter is idle
- Cover open/close commands now clear the opposite channel in the state cache, preventing stale state from showing incorrect position

## 2026-03-28

### Added
- Initial release
- `vitrea.py` — TCP protocol implementation for Vitrea Smart Home controllers
- Switch on/off with optional dimmer level (0–100)
- Cover open/close/stop
- State polling and caching via `vitrea_states.json`
- `VITREA_PROTOCOL.md` — reverse-engineered binary protocol documentation
- Home Assistant `command_line` integration examples

### Changed
- On/off/open/close/stop commands now immediately update the state cache, so HA reflects changes instantly without waiting for the next poll cycle
- Credentials moved from hardcoded values to `vitrea_config.json` (gitignored) with environment variable override support
