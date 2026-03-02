#!/usr/bin/env python3
"""install_scripts.py

Copy project-initializer check scripts from the skill's assets/scripts/ directory
into the target project's scripts/ directory.

All three runtime variants (.sh, .ps1, .js) of each required script are installed
so the project can run checks on Linux, macOS, and Windows CI runners without
modification.

Usage:
    python assets/install_scripts.py <project_root> --framework <openspec|speckit|gsd>

Arguments:
    project_root        Absolute or relative path to the target project root.

Options:
    --framework         SDD framework: openspec, speckit, or gsd  [required]
    --scripts-dir       Subdirectory inside project_root for scripts
                        (default: scripts)
    --dry-run           Print what would be copied without creating any files.

Installed scripts (3 variants each):
    check_project_tag.{sh,ps1,js}       — AGENTS.md identity tag validation
    check_sdd_<framework>.{sh,ps1,js}   — SDD process documentation checks

Example:
    python .agents/skills/project-initializer/assets/install_scripts.py . --framework gsd
    python .agents/skills/project-initializer/assets/install_scripts.py /path/to/project --framework openspec --dry-run
"""

import argparse
import shutil
import stat
import sys
from pathlib import Path

FRAMEWORKS = ("openspec", "speckit", "gsd")
VARIANTS = (".sh", ".ps1", ".js")

# Required scripts: always-installed base names
ALWAYS_INSTALL = ["check_project_tag"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy project-initializer check scripts into a target project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "project_root",
        help="Path to the target project root directory.",
    )
    parser.add_argument(
        "--framework",
        required=True,
        choices=FRAMEWORKS,
        metavar="FRAMEWORK",
        help=f"SDD framework to install check scripts for: {', '.join(FRAMEWORKS)}  [required]",
    )
    parser.add_argument(
        "--scripts-dir",
        default="scripts",
        metavar="DIR",
        help="Subdirectory inside project_root where scripts will be placed (default: scripts).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be copied without creating any files.",
    )
    return parser.parse_args()


def collect_files(src_dir: Path, framework: str) -> list[Path]:
    """Return the list of source script files to install, warning on missing ones."""
    bases = ALWAYS_INSTALL + [f"check_sdd_{framework}"]
    files: list[Path] = []

    for base in bases:
        found_any = False
        for ext in VARIANTS:
            candidate = src_dir / (base + ext)
            if candidate.exists():
                files.append(candidate)
                found_any = True
            else:
                print(
                    f"WARNING: Expected script not found: {candidate}",
                    file=sys.stderr,
                )
        if not found_any:
            print(
                f"ERROR: No variants found for '{base}' — aborting.",
                file=sys.stderr,
            )
            sys.exit(1)

    return files


def make_executable(path: Path) -> None:
    """Add user/group/other execute permission to a file (no-op on non-Unix)."""
    try:
        current_mode = path.stat().st_mode
        path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except NotImplementedError:
        pass  # Windows: chmod is a no-op, skip silently


def install(files: list[Path], dest_dir: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] Would create: {dest_dir}/")
        for src in files:
            print(f"[dry-run]   {src.name}  →  {dest_dir / src.name}")
        print(f"\n[dry-run] {len(files)} file(s) would be installed.")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    installed: list[Path] = []

    for src in files:
        dest = dest_dir / src.name
        shutil.copy2(src, dest)
        if src.suffix == ".sh":
            make_executable(dest)
        installed.append(dest)
        print(f"  + {dest}")

    print(f"\nDone. {len(installed)} script file(s) installed to {dest_dir}/")
    print(
        "\nNext step: commit the scripts/ directory to your repository so CI runners can access it."
    )


def main() -> None:
    args = parse_args()

    # Resolve paths
    skill_assets = Path(__file__).parent          # assets/ dir next to this script
    src_dir = skill_assets / "scripts"
    project_root = Path(args.project_root).resolve()
    dest_dir = project_root / args.scripts_dir

    # Validate source
    if not src_dir.is_dir():
        print(
            f"ERROR: Source scripts directory not found: {src_dir}\n"
            "Make sure you are running this script from within the project-initializer skill directory.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate project root exists
    if not project_root.is_dir():
        print(
            f"ERROR: Project root does not exist: {project_root}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Project root : {project_root}")
    print(f"Framework    : {args.framework}")
    print(f"Scripts dir  : {dest_dir}")
    if args.dry_run:
        print("Mode         : dry-run\n")
    else:
        print()

    files = collect_files(src_dir, args.framework)
    install(files, dest_dir, args.dry_run)


if __name__ == "__main__":
    main()
