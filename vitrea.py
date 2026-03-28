#!/usr/bin/env python3
"""
Vitrea Smart Home controller for Home Assistant.

Usage:
  vitrea.py on      <group> <channel> [level]  Turn on  (level 0-100, default 0)
  vitrea.py off     <group> <channel> [level]  Turn off (level 0-100, default 0)
  vitrea.py open    <group>                    Open cover
  vitrea.py close   <group>                    Close cover
  vitrea.py stop    <group>                    Stop cover
  vitrea.py state   <group> <channel>          Query switch -> prints "on" or "off"
  vitrea.py state   cover <group>              Query cover  -> prints "open" or "closed"

Environment variables (or edit defaults below):
  VITREA_HOST       Controller IP (default: 192.168.1.100)
  VITREA_PORT       Controller port (default: 11503)
  VITREA_USER       Login username (required)
  VITREA_PASS       Login password (required)
"""
import socket, sys, json, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "vitrea_config.json")
STATE_FILE = os.path.join(SCRIPT_DIR, "vitrea_states.json")

# Load config: vitrea_config.json > environment variables > defaults
_config = {}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as _f:
        _config = json.load(_f)

HOST = os.environ.get("VITREA_HOST", _config.get("host", "192.168.1.100"))
PORT = int(os.environ.get("VITREA_PORT", _config.get("port", 11503)))
TIMEOUT = 3
USERNAME = os.environ.get("VITREA_USER", _config.get("user", ""))
PASSWORD = os.environ.get("VITREA_PASS", _config.get("pass", ""))


def _build_login(username, password):
    user_bytes = username.encode("utf-16-le")
    pass_bytes = password.encode("utf-16-le")
    payload = (
        bytes([0x56, 0x54, 0x50, 0x3E, 0x01, 0x1E, 0x01, len(user_bytes)])
        + user_bytes
        + bytes([len(pass_bytes)])
        + pass_bytes
    )
    return payload + bytes([sum(payload) & 0xFF])


LOGIN = _build_login(USERNAME, PASSWORD)
QUERY_SWITCHES = bytes.fromhex("5654503e3604360105ae")


def _checksum(data):
    return sum(data) & 0xFF


def _build_cmd(group, channel, on, level=0):
    payload = bytes([0x56, 0x54, 0x50, 0x3E, 0x32, 0x08, 0x32,
                     group, channel, 0x4F if on else 0x46, level, 0x00, 0x00])
    return payload + bytes([_checksum(payload)])


def _recv(sock, idle=0.5):
    sock.settimeout(idle)
    buf = b""
    try:
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            buf += chunk
    except socket.timeout:
        pass
    return buf


def send_command(cmd):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(TIMEOUT)
        s.connect((HOST, PORT))
        s.sendall(LOGIN + cmd)
        _recv(s)


def query_states():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(TIMEOUT)
        s.connect((HOST, PORT))
        s.sendall(LOGIN)
        _recv(s)
        s.sendall(QUERY_SWITCHES)
        data = _recv(s)

    result = {}
    i = data.find(b"\x56\x54\x50\x3C\x36")
    if i >= 0:
        count = data[i + 5]
        for n in range(count):
            o = i + 7 + n * 4
            if o + 3 < len(data):
                g, c, st, lv = data[o], data[o+1], data[o+2], data[o+3]
                result[(g, c)] = {"on": st == 0x4F, "level": lv}
    return result


def _update_state_cache(group, channel, on, level=0):
    """Update the cached state file immediately after a command."""
    try:
        with open(STATE_FILE, "r") as f:
            states = json.load(f)
    except Exception:
        states = {}
    states[f"{group}_{channel}"] = {"on": on, "level": level}
    with open(STATE_FILE, "w") as f:
        json.dump(states, f)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1].lower()

    if action == "states":
        try:
            states = query_states()
            out = {}
            for (g, c), v in states.items():
                out[f"{g}_{c}"] = {"on": v["on"], "level": v["level"]}
            with open(STATE_FILE, "w") as f:
                json.dump(out, f)
            print(json.dumps(out))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
        return

    if action == "on":
        g, c = int(sys.argv[2]), int(sys.argv[3])
        lv = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        send_command(_build_cmd(g, c, on=True, level=lv))
        _update_state_cache(g, c, True, lv)

    elif action == "off":
        g, c = int(sys.argv[2]), int(sys.argv[3])
        lv = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        send_command(_build_cmd(g, c, on=False, level=lv))
        _update_state_cache(g, c, False, lv)

    elif action == "open":
        g = int(sys.argv[2])
        send_command(_build_cmd(g, 1, on=True, level=100))
        _update_state_cache(g, 1, True, 100)

    elif action == "close":
        g = int(sys.argv[2])
        send_command(_build_cmd(g, 2, on=True, level=0))
        _update_state_cache(g, 2, True, 0)

    elif action == "stop":
        g = int(sys.argv[2])
        send_command(_build_cmd(g, 2, on=False, level=255))
        _update_state_cache(g, 1, False, 0)
        _update_state_cache(g, 2, False, 0)

    elif action == "state":
        try:
            with open(STATE_FILE, "r") as f:
                states_json = json.load(f)
        except Exception:
            states_json = {}
        if sys.argv[2].lower() == "cover":
            g = int(sys.argv[3])
            ch1 = states_json.get(f"{g}_1", {})
            ch2 = states_json.get(f"{g}_2", {})
            if ch1.get("on"):
                print("100")
            elif ch2.get("on"):
                print("0")
            else:
                print("100")
        else:
            g, c = int(sys.argv[2]), int(sys.argv[3])
            s = states_json.get(f"{g}_{c}", {})
            print("True" if s.get("on") else "False")

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
