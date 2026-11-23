"""
COMPILER/comp.py
Script di compilazione con Nuitka per gli eseguibili netplan.

Produce eseguibili standalone one-file in dist/:

- Netplan-GUI.exe           (gui.py, PySide6, senza console)
- Netplan.exe               (main.py, CLI)
- Netplan-Congestione.exe   (congestion_check.py, CLI)

Uso:
    python COMPILER/comp.py              # compila tutto
    python COMPILER/comp.py --only gui   # solo la GUI
    python COMPILER/comp.py --dry-run    # mostra i comandi senza eseguirli

Richiede Nuitka:  pip install nuitka
"""

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from version import __version__

COPYRIGHT = "© Copyright 2024-2026 Nsfr750 - All rights reserved."
COMPANY = "Tuxxle"
PRODUCT = "Netplan"
DESCRIPTION = "Strumento di pianificazione copertura radio (KPI aggregati)"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "dist")
ICON_ICO = os.path.join(ROOT, "assets", "icon.ico")
ASSETS_DIR = os.path.join(ROOT, "assets")

# Opzioni comuni a tutti i target: metadati Windows + pacchetto one-file.
# --mingw64 forza l'uso del gcc scaricato da Nuitka (winlibs ufficiale):
# senza di esso può prendere un gcc dal PATH privo degli header MinGW
# (errore "windows.h: No such file or directory" in fase scons).
COMMON_OPTIONS = [
    "--mingw64",
    "--standalone",
    "--onefile",
    f"--windows-icon-from-ico={ICON_ICO}",
    f"--include-data-dir={ASSETS_DIR}=assets",
    f"--company-name={COMPANY}",
    f"--product-name={PRODUCT}",
    f"--file-version={__version__}",
    f"--product-version={__version__}",
    f"--file-description={DESCRIPTION}",
    f"--copyright={COPYRIGHT}",
    f"--output-dir={OUTDIR}",
    "--assume-yes-for-downloads",
    "--remove-output",
    "--show-progress",
]

# nome target -> (script, opzioni specifiche)
TARGETS = {
    "gui": (
        "gui.py",
        ["--enable-plugin=pyside6", "--windows-console-mode=disable"],
    ),
    "main": ("main.py", []),
    "check": ("congestion_check.py", []),
}


def build_command(script: str, extra: list[str]) -> list[str]:
    """Costruisce la riga di comando Nuitka per un singolo target."""
    return [
        sys.executable,
        "-m",
        "nuitka",
        *COMMON_OPTIONS,
        *extra,
        os.path.join(ROOT, script),
    ]


def compile_target(name: str, dry_run: bool = False) -> bool:
    """Compila un target; restituisce True se la compilazione riesce."""
    script, extra = TARGETS[name]
    cmd = build_command(script, extra)
    print(f"\n{'=' * 70}\nTarget: {name} ({script})\n{'=' * 70}")
    print(" ".join(cmd))
    if dry_run:
        return True
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"ERRORE: compilazione di '{name}' fallita (exit {result.returncode})")
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compilazione Nuitka degli eseguibili netplan"
    )
    parser.add_argument(
        "--only",
        choices=[*TARGETS, "all"],
        default="all",
        help="Compila un solo target (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra i comandi senza eseguire la compilazione",
    )
    args = parser.parse_args()

    try:
        import nuitka  # noqa: F401
    except ImportError:
        print("Nuitka non installato. Installa con: pip install nuitka", file=sys.stderr)
        if not args.dry_run:
            return 1

    selected = list(TARGETS) if args.only == "all" else [args.only]
    failed = [name for name in selected if not compile_target(name, args.dry_run)]

    print(f"\n{'=' * 70}")
    if failed:
        print(f"Compilazione terminata con errori su: {', '.join(failed)}")
        return 1
    if not args.dry_run:
        print(f"Compilazione completata. Eseguibili in: {OUTDIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
