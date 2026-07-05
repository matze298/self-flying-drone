# Fixed-Wing Autonomy Lab — Buyers & Developers Guide

A modular, safety-first documentation site for a fixed-wing RC aircraft with ArduPilot, a companion computer, live video, and staged computer-vision experiments.

## Local preview

Install `uv` first. The official install guide is at
<https://docs.astral.sh/uv/getting-started/installation/>.

Create/update the local environment and enter a shell inside `.venv`:

```bash
./setup.py
```

Run `exit` to return to your previous shell.

For non-interactive setup, such as CI:

```bash
./setup.py --no-shell
```

Serve the documentation site:

```bash
uv run mkdocs serve
```

Open `http://127.0.0.1:8000`.

Run formatting, linting, and type checks:

```bash
uv run --group dev prek run --all-files
```

Install the Git hooks locally:

```bash
uv run --group dev prek install
```

## Publish with GitHub Pages

1. Create a GitHub repository and push this directory.
2. In **Settings → Pages**, set **Source** to **GitHub Actions**.
3. Push to `main`. The included workflow builds and deploys the site.
4. Optionally set `site_url` and a custom domain in `mkdocs.yml`.

## Editorial policy

- Hardware recommendations are interface-first, not vendor-locked.
- Never let experimental vision code command control surfaces directly.
- Treat all cost bands as planning estimates, not live price quotes.
- Keep the Open-category EU operation model in mind: automatic missions are distinct from autonomous operation and a pilot intervention path remains essential.

## License

Documentation: CC BY 4.0. Source code snippets: MIT unless a file says otherwise.
