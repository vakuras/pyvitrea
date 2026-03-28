# pyvitrea

Python controller for **Vitrea Smart Home** switches and covers, designed for [Home Assistant](https://www.home-assistant.io/) integration via the `command_line` platform.

Communicates directly with the Vitrea controller over TCP using a reverse-engineered binary protocol (VTP).

## Features

- Turn switches on/off (with optional dimmer level 0-100)
- Open / close / stop covers (shutters/blinds)
- Query all device states in a single poll
- State caching via JSON file for instant HA reads
- Configurable via environment variables (no hardcoded credentials)

## Quick Start

```bash
# Set your controller details
export VITREA_HOST=192.168.1.100
export VITREA_USER=<YOUR_USERNAME>
export VITREA_PASS=<YOUR_PASSWORD>

# Control switches
python3 vitrea.py on  3 1        # Turn on group 3, channel 1
python3 vitrea.py off 3 1        # Turn off
python3 vitrea.py on  3 1 50     # Dim to 50%

# Control covers
python3 vitrea.py open  4        # Open cover (group 4)
python3 vitrea.py close 4        # Close cover
python3 vitrea.py stop  4        # Stop cover

# Query states
python3 vitrea.py states         # Poll all -> writes vitrea_states.json
python3 vitrea.py state 3 1      # Read switch state -> True/False
python3 vitrea.py state cover 4  # Read cover state -> 100/0
```

## Configuration

Set via environment variables or edit defaults in `vitrea.py`:

| Variable | Default | Description |
|---|---|---|
| `VITREA_HOST` | `192.168.1.100` | Vitrea controller IP |
| `VITREA_PORT` | `11503` | Vitrea TCP port |
| `VITREA_USER` | *(required)* | Login username |
| `VITREA_PASS` | *(required)* | Login password |

## Home Assistant Setup

Copy `vitrea.py` to `/config/scripts/` on your HA instance.

In HA, set environment variables via the add-on config or pass them inline:

### State Poller (polls all devices every 15s)

```yaml
command_line:
  - sensor:
      unique_id: vitrea_state_poller
      name: Vitrea State Poller
      command: "VITREA_HOST=<YOUR_IP> python3 /config/scripts/vitrea.py states"
      value_template: "{{ now().isoformat() }}"
      scan_interval: 15
```

### Switch Example

```yaml
  - switch:
      unique_id: vitrea_living_room_light
      name: Living Room Light
      command_on:    "VITREA_HOST=<YOUR_IP> python3 /config/scripts/vitrea.py on 3 1"
      command_off:   "VITREA_HOST=<YOUR_IP> python3 /config/scripts/vitrea.py off 3 1"
      command_state: "python3 /config/scripts/vitrea.py state 3 1"
      value_template: "{{ value.strip() }}"
      scan_interval: 15
```

### Cover Example

```yaml
  - cover:
      unique_id: vitrea_dining_room_shutter
      name: Dining Room Shutter
      command_open:  "VITREA_HOST=<YOUR_IP> python3 /config/scripts/vitrea.py open 4"
      command_close: "VITREA_HOST=<YOUR_IP> python3 /config/scripts/vitrea.py close 4"
      command_stop:  "VITREA_HOST=<YOUR_IP> python3 /config/scripts/vitrea.py stop 4"
      command_state: "python3 /config/scripts/vitrea.py state cover 4"
      value_template: "{{ value | int(0) }}"
      scan_interval: 15
```

## Protocol

See [VITREA_PROTOCOL.md](VITREA_PROTOCOL.md) for the reverse-engineered protocol documentation.

## License

[MIT](LICENSE)
