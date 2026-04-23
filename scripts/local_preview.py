#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = ROOT / "local_preview_registry.json"
DEFAULT_COMMAND_TEMPLATE = [
    "python3",
    "-m",
    "http.server",
    "{port}",
    "--bind",
    "{host}",
    "--directory",
    "{path}",
]
UNSAFE_BIND_HOSTS = {"0.0.0.0", "::"}


def load_registry(path: Path | None = None) -> dict:
    registry_path = path or DEFAULT_REGISTRY_PATH
    return json.loads(Path(registry_path).read_text())


def registry_defaults(registry: dict) -> dict:
    defaults = registry.get("defaults", {})
    localhost_host = defaults.get("localhost_host", "127.0.0.1")
    port_min = int(defaults.get("port_min", 41000))
    port_max = int(defaults.get("port_max", 41999))
    command_template = defaults.get("command_template", DEFAULT_COMMAND_TEMPLATE)
    if port_min > port_max:
        raise ValueError("port_min must be less than or equal to port_max")
    if localhost_host in UNSAFE_BIND_HOSTS:
        raise ValueError("localhost_host must not be a wildcard bind address")
    return {
        "localhost_host": localhost_host,
        "port_min": port_min,
        "port_max": port_max,
        "command_template": command_template,
    }


def resolve_bind_host(host: str | None, localhost_host: str = "127.0.0.1") -> str:
    chosen_host = localhost_host if host in (None, "") else host
    if chosen_host in UNSAFE_BIND_HOSTS:
        raise ValueError("Wildcard bind addresses are not allowed")
    return chosen_host


def suggest_port(
    project: str,
    occupied_ports: set[int],
    *,
    port_min: int,
    port_max: int,
) -> int:
    span = (port_max - port_min) + 1
    if len(occupied_ports) >= span:
        raise ValueError("No preview ports remain in the configured range")

    digest = hashlib.sha256(project.encode("utf-8")).hexdigest()
    candidate = port_min + (int(digest[:12], 16) % span)
    start = candidate
    while candidate in occupied_ports:
        candidate += 1
        if candidate > port_max:
            candidate = port_min
        if candidate == start:
            raise ValueError("Unable to allocate a non-conflicting preview port")
    return candidate


def materialize_project_ports(registry: dict) -> dict[str, int]:
    defaults = registry_defaults(registry)
    projects = registry.get("projects", {})
    assigned: dict[str, int] = {}
    occupied_ports: set[int] = set()

    for project, config in sorted(projects.items()):
        if "port" not in config:
            continue
        port = int(config["port"])
        if port in occupied_ports:
            raise ValueError(f"Duplicate port {port} configured for {project}")
        if not defaults["port_min"] <= port <= defaults["port_max"]:
            raise ValueError(
                f"Configured port {port} for {project} is outside the allowed preview range"
            )
        assigned[project] = port
        occupied_ports.add(port)

    for project, config in sorted(projects.items()):
        if project in assigned:
            continue
        port = suggest_port(
            project,
            occupied_ports,
            port_min=defaults["port_min"],
            port_max=defaults["port_max"],
        )
        assigned[project] = port
        occupied_ports.add(port)
        config["port"] = port

    return assigned


def build_preview_plan(
    project: str,
    registry: dict,
    *,
    tailscale_ip: str | None = None,
) -> dict:
    defaults = registry_defaults(registry)
    resolved_ports = materialize_project_ports(registry)
    project_config = registry.get("projects", {}).get(project, {})
    port = resolved_ports.get(project)
    if port is None:
        port = suggest_port(
            project,
            set(resolved_ports.values()),
            port_min=defaults["port_min"],
            port_max=defaults["port_max"],
        )

    repo_relative_path = project_config.get("path", ".")
    resolved_path = str((ROOT / repo_relative_path).resolve())
    localhost_host = resolve_bind_host(None, defaults["localhost_host"])

    urls = [
        {
            "label": f"{project} (localhost)",
            "url": f"http://{localhost_host}:{port}/",
        }
    ]
    if tailscale_ip:
        tailscale_host = resolve_bind_host(tailscale_ip, defaults["localhost_host"])
        urls.append(
            {
                "label": f"{project} (tailscale)",
                "url": f"http://{tailscale_host}:{port}/",
            }
        )

    command_template = project_config.get(
        "command_template",
        defaults["command_template"],
    )

    return {
        "project": project,
        "path": resolved_path,
        "port": port,
        "localhost_host": localhost_host,
        "tailscale_ip": tailscale_ip,
        "command_template": command_template,
        "urls": urls,
    }


def render_command(plan: dict, *, exposure: str = "localhost") -> str:
    if exposure == "tailscale":
        bind_host = resolve_bind_host(plan.get("tailscale_ip"), plan["localhost_host"])
    else:
        bind_host = resolve_bind_host(None, plan["localhost_host"])

    tokens = [
        token.format(
            project=plan["project"],
            port=plan["port"],
            host=bind_host,
            path=plan["path"],
        )
        for token in plan["command_template"]
    ]
    return shlex.join(tokens)


def render_preview_report(plan: dict) -> str:
    lines = [
        f"Project: {plan['project']}",
        f"Port: {plan['port']}",
        f"Local bind host: {plan['localhost_host']}",
        "URLs:",
    ]
    for entry in plan["urls"]:
        lines.append(f"- {entry['label']}: {entry['url']}")
    lines.append("Commands:")
    lines.append(f"- localhost: {render_command(plan, exposure='localhost')}")
    if plan.get("tailscale_ip"):
        lines.append(f"- tailscale: {render_command(plan, exposure='tailscale')}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deterministic local preview helper for repo-hosted apps and demos."
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY_PATH,
        help="Path to the preview registry JSON file.",
    )
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    show_parser = subparsers.add_parser("show", help="Show preview details for a project.")
    show_parser.add_argument("project")
    show_parser.add_argument(
        "--tailscale-ip",
        help="Optional Tailscale IP to include in the preview report.",
    )

    port_parser = subparsers.add_parser("port", help="Print the assigned preview port.")
    port_parser.add_argument("project")

    command_parser = subparsers.add_parser(
        "command",
        help="Render a safe preview command for the project.",
    )
    command_parser.add_argument("project")
    command_parser.add_argument(
        "--tailscale-ip",
        help="Explicit Tailscale IP to bind when --exposure tailscale is selected.",
    )
    command_parser.add_argument(
        "--exposure",
        choices=("localhost", "tailscale"),
        default="localhost",
        help="Choose the bind host to render into the command.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    registry = load_registry(args.registry)
    plan = build_preview_plan(
        getattr(args, "project"),
        registry,
        tailscale_ip=getattr(args, "tailscale_ip", None),
    )

    if args.command_name == "show":
        print(render_preview_report(plan))
        return 0
    if args.command_name == "port":
        print(plan["port"])
        return 0
    if args.command_name == "command":
        if args.exposure == "tailscale" and not args.tailscale_ip:
            parser.error("--tailscale-ip is required when --exposure tailscale is used")
        print(render_command(plan, exposure=args.exposure))
        return 0

    parser.error(f"Unsupported command {args.command_name}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
