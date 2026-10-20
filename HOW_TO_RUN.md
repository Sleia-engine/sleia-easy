# How to run Sleia Easy

Working directory for all commands:

```bash
cd /sleia-easy
```

Install dependencies once:

```bash
python -m pip install -r requirements.txt
```

## Slice a model (command line)

```bash
python start.py slice examples/models/cube.stl -o data/gcode/cube.gcode
```

Useful options:

| Option | Description |
| --- | --- |
| `-o`, `--output` | Output G-code path |
| `--walls` | Wall loops (perimeters) |
| `--infill` | Sparse infill density, percent |
| `--pattern` | Infill pattern (`rectilinear`, `grid`, `gyroid`, …) |
| `--layer-height` | Layer height in mm |
| `--material` | `PLA`, `PETG`, `ABS`, or `TPU` |
| `--baseplate` | `generic`, `ender3`, `prusa-mk4`, or `bambu-p1s` |
| `--bed-x`, `--bed-y` | Override build-plate size in mm |
| `--no-auto-orient` | Keep the file orientation; still place the model on z=0 |
| `--support` | Enable support |
| `--settings-json` | Load Basic settings from a JSON file |

Example with material and baseplate:

```bash
python start.py slice examples/models/cube.stl -o data/gcode/cube.gcode --material PLA --baseplate ender3 --walls 2 --infill 20
```

Example with a settings file:

```bash
python start.py slice examples/models/cube.stl -o data/gcode/cube.gcode --settings-json examples/settings_pla.json
```

## Example scripts

From `sleia-easy`:

```bash
python examples/slice_cube.py
```

Windows Command Prompt:

```bat
examples\slice_cube.bat
```

PowerShell:

```powershell
.\examples\slice_cube.ps1
```

The sample cube is written to `data/gcode/cube_example.gcode`.

## HTTP service

```bash
python start.py serve
```

Or:

```bat
examples\serve.bat
```

```powershell
.\examples\serve.ps1
```


| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Confirm the service is running |
| `POST` | `/api/slice` | Upload a model (`file`) and optional `settings` JSON form field |
| `GET` | `/api/jobs/<id>` | Read job status |
| `GET` | `/api/jobs/<id>/gcode` | Download G-code |
| `POST` | `/api/gcode/save` | Copy G-code to a local path |

## Auto-orient and baseplate

By default the slicer:

1. Tests six axis-aligned orientations and keeps the one with the largest downward contact area.
2. Translates the mesh so the lowest point is on z=0.
3. Centers the part on the selected build plate.

Material presets set nozzle temperature, bed temperature, fan speed, retraction, filament diameter, and density. Baseplate presets set bed size (`generic` 220×220 mm, `ender3` 220×220 mm, `prusa-mk4` 250×210 mm, `bambu-p1s` 256×256 mm).
