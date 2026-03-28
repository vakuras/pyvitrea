# Vitrea Smart Home Protocol (VTP) — Documentation

## Overview

This documents the **Vitrea Smart Home** proprietary TCP protocol, reverse-engineered from packet captures between the Vitrea mobile app and a Vitrea controller. The `vitrea.py` script implements this protocol for Home Assistant integration.

## Network Details

| Parameter | Value |
|---|---|
| TCP Port | `11503` |
| Protocol | Raw TCP, binary |

## Device Layout (example)

| Group | Channel(s) | Type | Name |
|---|---|---|---|
| 1 | 1 | Switch (on/off) | Entry Light |
| 3 | 1 | Switch | Living Room Light |
| 3 | 2 | Switch | Dining Room Light |
| 3 | 3 | Switch | Kitchen Bar Light |
| 3 | 4 | Switch | Kitchen Light |
| 4 | 1-2 | Cover | Dining Room Window Shutter |
| 5 | 1-2 | Cover | Master Bedroom Shutter |

### Cover Wiring

Covers use **two channels** per physical shutter:
- **Channel 1** = OPEN direction (relay)
- **Channel 2** = CLOSE direction (relay)

Both channels will be OFF once movement finishes (relays are momentary).

## Protocol Structure

### General Packet Format

```
[VTP] [direction] [type] [length] [data...] [checksum]
```

- **Magic**: `56 54 50` = ASCII `VTP`
- **Direction**: `3E` (`>`) = client -> device, `3C` (`<`) = device -> client
- **Checksum**: Low byte of the sum of all preceding bytes: `sum(payload) & 0xFF`

### Checksum Calculation (Python)

```python
def checksum(data: bytes) -> int:
    return sum(data) & 0xFF
```

---

## Message Types

### Type 0x01 — Login

**Request (client -> device):**
```
VTP> 01 1E 01 [user_len] [username_utf16le] [pass_len] [password_utf16le] [checksum]
```

- Username: UTF-16LE encoded
- Password: UTF-16LE encoded

**Response (device -> client):**
```
VTP< 01 06 01 [device_id bytes] [checksum]
```

### Type 0x04 — Firmware Version

**Request:** `VTP> 04 02 04 [checksum]`

**Response:** `VTP< 04 05 04 [major] [minor] [patch] [checksum]`

### Type 0x32 — Switch/Dimmer Command

**Request (14 bytes):**
```
VTP> 32 08 32 [group] [channel] [command] [level] 00 00 [checksum]
```

| Field | Values |
|---|---|
| `command` | `4F` ('O') = **ON**, `46` ('F') = **OFF** |
| `level` | `00` = switch, `01`-`64` = dimmer (1-100%), `FF` = cover stop |

**ACK Response:**
```
VTP< 00 03 32 00 [checksum]
```

**Status Confirmation (~100ms after ACK):**
```
VTP< 33 09 [seq] [group] [channel] [command] 00 00 00 01 [checksum]
```

### Type 0x36 — Query All Switch/Dimmer States

**Request:**
```
VTP> 36 04 36 [first_group] [last_group] [checksum]
```

**Response:**
```
VTP< 36 [count] 36 [group ch state level] x N [checksum]
```

Each entry is 4 bytes: group, channel, state (`4F`=ON, `46`=OFF), level.

### Type 0x37 — Query All Blind/Cover States

**Request:** `VTP> 37 02 37 [checksum]`

**Response:** Each entry is 6 bytes: group, channel, state, position, 00, 00.

---

## Communication Flow

```
1. TCP connect (port 11503)
2. Login (Type 0x01)
3. Query states (Type 0x36, 0x37)
4. Send commands (Type 0x32)
```

You can send **login + command** back-to-back in one TCP stream. The device processes both sequentially.

---

## Architecture Notes

- **State caching**: The poller queries the device every 15s and writes `vitrea_states.json`. Individual state reads use this cached file.
- **Covers**: Relays are momentary (both OFF after movement). Default position reported as "open" when idle.
- **Dimmer levels**: Protocol supports 0-100. Can be exposed as `light` entities with brightness.
- **Concurrent connections**: Controller handles one TCP connection at a time.
