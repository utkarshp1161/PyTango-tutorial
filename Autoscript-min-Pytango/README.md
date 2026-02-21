# TEM PyTango Control

A [PyTango](https://pytango.readthedocs.io/) wrapper around the AutoScript TEM microscope client API. Exposes microscope hardware — detectors, stage, beam — as Tango devices so they can be controlled and monitored from any Tango-compatible client.

---

## What this project does

AutoScript provides a Python API for controlling TEM microscopes (Thermo Fisher / FEI). This project wraps that API as a set of Tango device servers so that:

- Detector settings (dwell time, resolution) live in dedicated Tango devices and can be read/written by any client independently of acquisition
- The `Microscope` device reads those settings at acquisition time and calls AutoScript — AutoScript calls never leak outside `Microscope.py`
- Images are returned as `DevEncoded = (json_metadata, raw_bytes)` — metadata and pixel data travel together atomically
- The whole stack runs in simulation mode on any machine without AutoScript installed, making development and testing possible offline

---

## Project layout

```
.
├── src/
│   ├── Microscope.py              # Main device — owns AutoScript connection and all acquisition commands
│   ├── detectors/
│   │   ├── HAADF.py               # HAADF detector settings device
│   │   ├── EELS.py                # EELS detector settings device (stub)
│   │   ├── EDS.py                 # EDS detector settings device (stub)
│   │   └── CEOS.py                # CEOS detector settings device (stub)
│   ├── hardware/
│   │   ├── STAGE.py               # Stage position and movement device
│   │   └── BEAM.py                # Beam blanking and current device
│   └── acquisition/
│       └── advanced_acquisition.py  # Multi-detector acquisition helpers (stub)
├── tests/
│   ├── conftest.py                # Shared pytest fixtures (DeviceTestContext proxies)
│   ├── test_microscope.py         # Microscope device tests
│   ├── test_acquisition.py        # Acquisition tests
│   └── detectors/
│       └── test_HAADF.py          # HAADF device tests
├── notebooks/
│   └── Client.ipynb               # Tutorial: connect → configure → acquire → display
├── llm-context/                   # AutoScript and PyTango API corpus for LLM-assisted development
├── AS_commands.txt                # AutoScript API reference snippets
└── pyproject.toml
```

### Design principle

Each detector device (e.g. `HAADF`) is a **settings holder only** — it has no AutoScript dependency. `Microscope` reads detector settings via `DeviceProxy` at acquisition time, calls AutoScript, and returns the result. Adding a new detector means adding a new device file and one line in `Microscope._connect_detector_proxies()` — nothing else changes.

---

## Requirements

- Python `>=3.11, <3.13`
- PyTango `10.1.2`
- AutoScript TEM client `1.5.x` (only required on the microscope PC — see [Simulation mode](#simulation-mode))
- [uv](https://github.com/astral-sh/uv) for dependency management

---

## Installation

```bash
git clone <repo-url>
cd <repo>
uv sync
```

---

## Running the device servers

Use the `tango.test_context` CLI — it handles port assignment automatically and **prints the exact connection URL** to use in your client. Run each device in a separate terminal.

```bash
python -m tango.test_context src.detectors.HAADF.HAADF --host 127.0.0.1 --port 8888
python -m tango.test_context src.hardware.STAGE.Stage   --host 127.0.0.1 --port 8891
python -m tango.test_context src.hardware.BEAM.Beam     --host 127.0.0.1 --port 8890
uv run python -m tango.test_context src.Microscope.Microscope --host 127.0.0.1 --port 8889 \
  --prop "{'haadf_device_address': 'tango://127.0.0.1:8888/test/nodb/haadf#dbase=no'}"

```

Each prints its own URL on startup:

```
Ready to accept request
Device access: tango://127.0.0.1:8888/test/nodb/haadf#dbase=no
Server access: tango://127.0.0.1:8888/dserver/HAADF/haadf#dbase=no
```

Copy the `Device access` line — that is the exact string to pass to `tango.DeviceProxy(...)`.

> **Why `127.0.0.1` and not `localhost`?**
> On macOS, `localhost` may resolve to IPv6 (`::1`) before IPv4. The Tango C++ layer binds to IPv4, so the connection fails with `TRANSIENT_ConnectFailed` even though the server says "Ready to accept request". Always use `127.0.0.1` explicitly.

> **Why not `python src/detectors/HAADF.py test haadf_server --nodb --port 45678`?**
> The `--port` flag sets the Tango port but CORBA may open a second random port for its IOR endpoint, causing `API_ServerNotRunning` on the client side. The `tango.test_context` CLI avoids this entirely and reports the actual URL.

> **Why call `wait_for_proxy` before any attribute/command?**
> `DeviceProxy(...)` returns immediately but the CORBA connection establishes in the background. Calling `.state()` or any attribute too quickly raises `API_CantConnectToDevice`. `wait_for_proxy` polls until the device is ready or the timeout expires.

### With a Tango database (full stack / production)

Start a Tango DB via Docker:

```bash
docker run -d --name tango-db \
  -e MYSQL_ROOT_PASSWORD=tango \
  -p 10000:10000 \
  tangocs/tango-cs:latest
```

Set the environment variable (add to `.zshrc` / `.bashrc` to persist):

```bash
export TANGO_HOST=localhost:10000
```

Run servers in order — detectors and hardware first, Microscope last:

```bash
uv run python src/detectors/HAADF.py test haadf_server
uv run python src/hardware/STAGE.py  test stage_server
uv run python src/hardware/BEAM.py   test beam_server
uv run python src/Microscope.py      test mic_server
```

In this mode device addresses are short: `test/detector/haadf`, `test/microscope/1`, etc. — no port or `#dbase=no` needed.

> **Note:** Tests use `DeviceTestContext` internally — `uv run pytest tests/ -v` works with no Tango DB or env variable set.

---

## Simulation mode

On any machine without AutoScript installed, `Microscope.py` detects the missing package and runs in simulation mode automatically — `get_image` returns a randomly generated array of the correct shape and dtype. No code changes needed.

---

## Acquiring an image

```python
import json
import numpy as np
import tango
from tango.test_utils import wait_for_proxy

# Paste the Device access URLs printed by tango.test_context at startup
haadf      = tango.DeviceProxy("tango://127.0.0.1:8888/test/nodb/haadf#dbase=no")
microscope = tango.DeviceProxy("tango://127.0.0.1:8889/test/nodb/microscope#dbase=no")

# Always wait before making any calls — CORBA connection is async
wait_for_proxy(haadf,      timeout=5)
wait_for_proxy(microscope, timeout=5)

# Configure detector settings
haadf.dwell_time   = 1e-6
haadf.image_width  = 1024
haadf.image_height = 1024

# Acquire — returns DevEncoded = (json_metadata_str, raw_bytes)
json_meta, raw_bytes = microscope.get_image("haadf")

# Decode
meta  = json.loads(json_meta)
image = np.frombuffer(raw_bytes, dtype=meta["dtype"]).reshape(meta["shape"])

print(image.shape)  # (1024, 1024)
print(meta)         # {"detector": "haadf", "shape": [...], "dtype": "uint16", ...}
```

---

## Running tests

```bash
uv run pytest tests/ -v
```

---

## Adding a new detector

1. Copy `src/detectors/HAADF.py` to `src/detectors/NEWDET.py` and adjust the attributes for that detector's settings.
2. Add a `device_property` in `Microscope.py`:
   ```python
   newdet_device_address = device_property(dtype=str, default_value="test/detector/newdet")
   ```
3. Register it in `_connect_detector_proxies()`:
   ```python
   "newdet": self.newdet_device_address,
   ```
4. Add acquisition logic in `_acquire_stem_image()` if it differs from HAADF.
5. Add `tests/detectors/test_NEWDET.py` following `test_HAADF.py` as a template.

---

## Notebook tutorial

```bash
uv run jupyter notebook notebooks/Client.ipynb
```

---

## Not yet implemented

- **Multi-detector acquisition** (`get_image_advanced`) — see `src/acquisition/advanced_acquisition.py` for design notes.
- **EELS, EDS, CEOS** detector device files are present as stubs.
- **Async acquisition** — deferred; architecture is designed to adopt gevent-based async later without structural changes.