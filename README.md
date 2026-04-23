# allora2026.github.io

Personal GitHub Pages site for Allora.

## Local previews

Use `scripts/local_preview.py` with `local_preview_registry.json` to reserve stable preview ports for local apps and demos in this repo.

Show the assigned preview details for the site:

```bash
python3 scripts/local_preview.py show allora2026-site
```

Include an opt-in Tailscale URL and matching bind command:

```bash
python3 scripts/local_preview.py show allora2026-site --tailscale-ip 100.x.y.z
python3 scripts/local_preview.py command allora2026-site --exposure tailscale --tailscale-ip 100.x.y.z
```

Start the default localhost preview without guessing the port:

```bash
$(python3 scripts/local_preview.py command allora2026-site)
```

Add future apps or demos by creating a new entry under `projects` in `local_preview_registry.json`. If you need a deterministic port before checking the project in, run:

```bash
python3 scripts/local_preview.py port my-next-demo
```

The workflow always binds to `127.0.0.1` by default. If you need Tailscale access, pass an explicit Tailscale IP. The helper rejects wildcard bind addresses such as `0.0.0.0`.
