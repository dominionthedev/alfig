"""
cli.py — Alfig CLI built with Typer + Rich.

Commands:
    alfig convert <input> --to <format>
    alfig validate <input>
    alfig get <input> <key>
    alfig info
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from alfig.core import Alfig
from alfig.formats import detect_format, _REGISTRY

app = typer.Typer(
    name="alfig",
    help="[bold violet]Alfig[/] — Unified Config System",
    rich_markup_mode="rich",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)

console = Console()
err_console = Console(stderr=True)

SYNTAX_LANG = {
    "json": "json",
    "yaml": "yaml",
    "toml": "toml",
    "conf": "ini",
    "ini":  "ini",
}


def _abort(message: str) -> None:
    err_console.print(f"[bold red]✗[/] {message}")
    raise typer.Exit(code=1)


def _resolve_format(path: Path, force: Optional[str]) -> str | None:
    if force:
        return force
    try:
        return detect_format(str(path))
    except ValueError as e:
        _abort(str(e))


@app.command()
def convert(
    input: Path = typer.Argument(..., help="Input config file", exists=True),
    to: str = typer.Option(..., "--to", help="Target format: json, yaml, toml, conf"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Output path (auto-named if omitted)"),
    from_fmt: Optional[str] = typer.Option(None, "--from", "-f", help="Force source format"),
    show: bool = typer.Option(False, "--show", "-s", help="Print the converted output"),
):
    """
    Convert a config file from one format to another.

    [dim]Examples:[/]
      [cyan]alfig convert settings.toml --to json[/]
      [cyan]alfig convert settings.yaml --to conf --out app.conf[/]
      [cyan]alfig convert settings.json --to toml --show[/]
    """
    src_fmt = _resolve_format(input, from_fmt)
    dst_fmt = to.lower()

    if dst_fmt not in _REGISTRY:
        _abort(f"Unknown target format [bold]{dst_fmt}[/]. Choose: {', '.join(sorted(set(_REGISTRY)))}")

    out_path = out or input.with_suffix(f".{dst_fmt}")

    with console.status(f"[dim]Converting [bold]{input.name}[/] → [bold]{out_path.name}[/]…"):
        try:
            Alfig.convert(str(input), str(out_path), input_format=src_fmt, output_format=dst_fmt)
        except Exception as e:
            _abort(f"Conversion failed: {e}")

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="dim")
    grid.add_column()
    grid.add_row("From", f"[bold]{input}[/]  [dim]{src_fmt.upper()}[/]")
    grid.add_row("To",   f"[bold]{out_path}[/]  [dim]{dst_fmt.upper()}[/]")
    grid.add_row("Size", f"{out_path.stat().st_size:,} bytes")

    console.print(Panel(grid, title="[bold green]✓ Converted[/]", border_style="green", padding=(1, 2)))

    if show:
        content = out_path.read_text()
        lang = SYNTAX_LANG.get(dst_fmt, "text")
        console.print(Syntax(content, lang, theme="nord", line_numbers=True))


@app.command()
def validate(
    input: Path = typer.Argument(..., help="Config file to validate", exists=True),
    fmt: Optional[str] = typer.Option(None, "--fmt", "-f", help="Force format"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print parsed config"),
):
    """
    Parse a config file and confirm it is well-formed.

    [dim]Examples:[/]
      [cyan]alfig validate settings.yaml[/]
      [cyan]alfig validate settings.conf --verbose[/]
    """
    detected = _resolve_format(input, fmt)

    with console.status(f"[dim]Parsing [bold]{input.name}[/]…"):
        try:
            cfg = Alfig()
            cfg.load(str(input), format=detected)
        except Exception as e:
            _abort(f"Parse error: {e}")

    data = cfg.as_dict()
    key_count = sum(1 for _ in _walk_keys(data))

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="dim")
    grid.add_column()
    grid.add_row("File",   f"[bold]{input}[/]")
    grid.add_row("Format", detected.upper())
    grid.add_row("Keys",   str(key_count))

    console.print(Panel(grid, title="[bold green]✓ Valid[/]", border_style="green", padding=(1, 2)))

    if verbose:
        pretty = json.dumps(data, indent=2, default=str)
        console.print(Syntax(pretty, "json", theme="nord", line_numbers=True))


def _walk_keys(data: dict, prefix: str = ""):
    for k, v in data.items():
        full = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            yield from _walk_keys(v, full)
        else:
            yield full, v


@app.command()
def get(
    input: Path = typer.Argument(..., help="Config file", exists=True),
    key: str = typer.Argument(..., help="Dot-notation key, e.g. database.host"),
    fmt: Optional[str] = typer.Option(None, "--fmt", "-f", help="Force format"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Print raw value only (for scripting)"),
):
    """
    Read a single value from a config file.

    [dim]Examples:[/]
      [cyan]alfig get settings.yaml database.host[/]
      [cyan]alfig get settings.toml features.max_threads --raw[/]
    """
    detected = _resolve_format(input, fmt)

    try:
        cfg = Alfig()
        cfg.load(str(input), format=detected)
    except Exception as e:
        _abort(f"Could not read [bold]{input}[/]: {e}")

    value = cfg.get(key)

    if value is None:
        _abort(f"Key [bold]{key}[/] not found in [bold]{input.name}[/]")

    if raw:
        typer.echo(value)
        return

    val_str = json.dumps(value) if isinstance(value, (list, dict)) else str(value)
    val_type = type(value).__name__

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="dim")
    grid.add_column()
    grid.add_row("Key",   f"[bold cyan]{key}[/]")
    grid.add_row("Value", f"[bold white]{val_str}[/]")
    grid.add_row("Type",  f"[dim]{val_type}[/]")

    console.print(Panel(grid, border_style="cyan", padding=(1, 2)))


@app.command()
def info():
    """Show Alfig version and supported formats."""
    from alfig import __version__

    console.print()
    console.print(
        Panel(
            f"[bold violet]alfig[/] [dim]v{__version__}[/]\n[dim]Unified Config System[/]",
            border_style="violet",
            padding=(1, 4),
        )
    )

    table = Table(
        title="Supported Formats",
        box=box.ROUNDED,
        border_style="dim",
        header_style="bold",
        show_lines=False,
        padding=(0, 2),
    )
    table.add_column("Format", style="bold")
    table.add_column("Extensions")
    table.add_column("Read")
    table.add_column("Write")
    table.add_column("Requires")

    format_info = [
        ("JSON",  ".json",       "✓", "✓", "[dim]none (stdlib)[/]"),
        ("YAML",  ".yaml, .yml", "✓", "✓", "[yellow]PyYAML[/]"),
        ("TOML",  ".toml",       "✓", "✓", "[cyan]tomllib[/] (3.11+) / [cyan]tomli-w[/]"),
        ("CONF",  ".conf, .ini", "✓", "✓", "[dim]none (custom parser)[/]"),
    ]

    colors = ["green", "yellow", "cyan", "magenta"]
    for (name, exts, r, w, req), color in zip(format_info, colors):
        table.add_row(
            f"[{color}]{name}[/]", exts,
            f"[green]{r}[/]", f"[green]{w}[/]",
            req,
        )

    console.print(table)
    console.print()


def main():
    app()


if __name__ == "__main__":
    main()
