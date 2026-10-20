# Sleia Easy

Sleia Easy is a standalone Python application for thermoplastic slicing. It implements the Basic process settings used in the Sleia web client: layer height, infill, support, and motion.

## Scope

The slicer is limited to Basic thermoplastic parameters. Supported input formats are STL, OBJ, and 3MF. Output is Marlin-compatible G-code written to a user-specified path or to the local data directory.

## Repository structure

| Path | Description |
| --- | --- |
| `start.py` | Command-line and service entry point |
| `requirements.txt` | Python dependencies |
| `engine/` | Core slicing, mesh processing, infill, support, and G-code generation |
| `app/` | Print settings, slice pipeline, command-line interface, and HTTP service |
| `api/` | Flask application factory |
| `config/` | Application paths and upload limits |
| `data/` | Uploaded models, job records, and generated G-code |

## Clone and pull from GitHub

Repository: [https://github.com/Sleia-engine/sleia-easy.git](https://github.com/Sleia-engine/sleia-easy.git)

First-time clone:

```bash
git clone https://github.com/Sleia-engine/sleia-easy.git
cd sleia-easy
```

To update an existing local copy:

```bash
cd sleia-easy
git fetch origin
git pull origin main
```

If the default branch is `master`, use `git pull origin master` instead.

## Installation

From the project root:

```bash
python -m pip install -r requirements.txt
```

Python 3.10 or later is recommended.

For command-by-command instructions, see [HOW_TO_RUN.md](HOW_TO_RUN.md).

## Command-line usage

Slice a model and write G-code:

```bash
python start.py slice model.stl -o print.gcode --infill 20 --pattern rectilinear
```

Optional arguments include `--layer-height`, `--walls`, `--support`, `--print-speed`, and `--settings-json` for a JSON file of Basic settings.

## HTTP service

Start the local service:

```bash
python start.py serve
```

The default bind address is `127.0.0.1:5000`.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health check |
| `POST` | `/api/slice` | Upload a model and Basic settings; starts an asynchronous slice job |
| `GET` | `/api/jobs/<id>` | Job status and metadata |
| `GET` | `/api/jobs/<id>/gcode` | Download generated G-code |
| `POST` | `/api/gcode/save` | Copy G-code to a destination path (`job_id`, `destination`) |

## Version control

This directory is part of the Sleia repository. Generated artifacts under `data/` and `*.gcode` files are excluded by `.gitignore`. Changes in this project must not be applied to `web-version`.
