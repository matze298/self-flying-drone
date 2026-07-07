# Agent Instructions

This repository is a fixed-wing autonomy buyers and developers guide. Use these notes when working as Codex, Claude, or another coding agent in this repo.

## Operating Style

- Prefer small, explicit changes over broad rewrites.
- Read the nearby docs before editing; this project values consistent guidance more than clever phrasing.
- Ask before making broad policy changes. The user explicitly prefers being asked for general changes rather than having them assumed.
- Do not commit or push unless the user asks.
- When opening PRs, use a draft PR unless the user asks for ready-for-review.
- Keep PR descriptions brief and structured with `What`, `How`, `Why`, and `Experiments / Tests`.

## Branch Naming

- Use lowercase work branch names in the form `<type>/<short-kebab-slug>`.
- Preferred branch types are `feature/`, `fix/`, `cleanup/`, `docs/`, `test/`, `ci/`, `deps/`, `release/`, and `spike/`.
- Use `feature/` for new user-visible capability, `fix/` for defects, `cleanup/` for refactors or repository hygiene, and `docs/` for documentation-only changes.
- Use `test/` for test-only work, `ci/` for GitHub Actions or hook changes, `deps/` for dependency updates, `release/` for release preparation, and `spike/` for short-lived experiments.
- Never use `codex/` for branch names.

## Tooling Decisions

- Use `uv` for Python environments, Python dependency groups, docs tooling, and local repo checks.
- `setup.py` is a self-executable uv script. Keep `./setup.py` working.
- The default setup path should create/update `.venv` and return to the caller.
- Supported setup workstreams are `docs`, `python`, `sim`, `rust`, `ros`, and `jetson`.
- `docs`, `python`, and `sim` are implemented through uv dependency groups.
- The `sim` workstream installs Python-side MAVLink/software-in-the-loop (SITL) client tools. ArduPilot SITL remains an external checkout with system dependencies.
- `rust`, `ros`, `jetson`, and `--all-workstreams` should fail clearly until real workspaces/installers exist.
- Do not pretend `uv` manages Rust, ROS, C++, CUDA, TensorRT, or system packages.

## Quality Gates

- Prefer `pytest` for Python tests. Avoid adding new `unittest`-style tests unless there is a specific reason.
- Mirror source/tool paths under `tests/`; for example, test `tools/sitl/run.py` in `tests/tools/sitl/test_run.py`.
- Ruff is configured with `select = ["ALL"]`; fix issues where practical.
- Ruff line length is 120.
- Ruff docstrings use Google style.
- Keep per-file ignores narrow and commented.
- Do not add new `setup.py` ignores without checking whether the issue can be fixed first.
- `ty` is enabled with the project-selected recommended mode. Preserve the existing intent rather than tightening it casually.
- `prek.toml` is the pre-commit framework configuration. Do not recreate `.pre-commit-config.yaml`.
- Use hooks from the `prek` builtin repo where possible.
- `no-commit-to-branch` is expected to block commits on `main`; branch before committing.

Useful checks:

```bash
uv run --group dev --group sim pytest
uv run --group dev ruff format --check .
uv run --group dev ruff check .
uv run --group dev ty check
uv run --group docs mkdocs build --strict --site-dir /tmp/drone_build_site
uv run --group dev prek run --all-files
```

## Documentation Decisions

- This is a MkDocs Material site with plain Markdown as the source of truth.
- Hardware recommendations should be interface-first, not vendor-locked.
- Cost and buying advice can mention Germany-specific availability, but treat price links as live market guidance rather than permanent quotes.
- Use representative component families, and warn readers to verify current board revisions, firmware targets, pinouts, and voltage domains.
- Keep automatic and autonomous operation distinct in safety/legal writing.
- Experimental vision code must never command control surfaces directly.
- Spell out domain abbreviations on first use in docs. Keep standard terms like software-in-the-loop (SITL) in paths and tool names when they match upstream robotics terminology.

## Software Architecture Decisions

- Keep a polyglot monorepo for now.
- Split development environments by workstream instead of splitting the repository prematurely.
- Use Ubuntu 24.04 and ROS 2 Jazzy as the baseline for ROS guidance.
- Use JetPack 7 as the Jetson deployment direction.
- Prefer Python for tooling, CLIs, replay, evaluation, ground-side inference, and MAVSDK experiments.
- Prefer Rust for new standalone daemons and robust services with clean file, socket, or message boundaries.
- Keep C++ as the fallback where ROS 2, NVIDIA, TensorRT, GStreamer, or vendor examples are first-class in C++.
- Do not force ROS 2 onto every helper script. Add ROS where multi-process robotics integration, simulation, launch, visualization, or hardware abstraction justify it.

## Repository Shape

The intended long-term layout is:

```text
docs/                  # MkDocs handbook
src/                   # Future real Python packages once stable APIs exist
tools/python/          # Future Python CLIs and replay utilities
tools/sitl/            # ArduPilot SITL checkout/run helpers
services/rust/         # Future Cargo workspace for standalone services
ros_ws/src/            # Future ROS 2 packages built with colcon
aircraft/              # Future parameters, missions, wiring records
deploy/                # Future systemd, container, and Jetson deployment config
models/                # Manifests only; keep large weights outside normal Git history
data/                  # Manifests only; keep raw videos/datasets outside normal Git history
```

Do not add large videos, datasets, or model weights to normal Git history.

## GitHub And Dependency Updates

- Dependabot updates uv dependencies weekly as one uv dependency group.
- Dependabot updates GitHub Actions weekly as a separate group.
- Keep the one-week cooldown for dependency ecosystems unless the user asks otherwise.
