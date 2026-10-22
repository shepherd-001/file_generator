#!/usr/bin/env python3
"""
File Generator - Create files of any name, extension and size.
Supports interactive mode and command-line mode.
If no name is given, a random filename is generated.
"""

import argparse
import os
import sys
import uuid
from pathlib import Path


def parse_size(size_str: str) -> int:
    """Convert strings like '10MB', '500KB', '2GB', '1.5GB' into bytes."""
    size_str = size_str.strip().upper().replace(" ", "")

    # Longer units first so "MB" is matched before "B"
    units = [
        ("TB", 1024 ** 4),
        ("GB", 1024 ** 3),
        ("MB", 1024 ** 2),
        ("KB", 1024),
        ("B", 1),
    ]

    for unit, multiplier in units:
        if size_str.endswith(unit):
            number = size_str[:-len(unit)]
            try:
                return int(float(number) * multiplier)
            except ValueError:
                raise ValueError(f"Invalid size number: '{number}'")

    # No unit → treat as bytes
    try:
        return int(float(size_str))
    except ValueError:
        raise ValueError(
            "Invalid size. Examples: 1048576, 10MB, 500KB, 1.5GB, 2GB"
        )


def get_downloads_folder() -> Path:
    return Path.home() / "Downloads"


def generate_random_name() -> str:
    """Generate a short random filename (e.g. file_a3f9c2b1)."""
    return f"file_{uuid.uuid4().hex[:8]}"


def create_file(filepath: Path, size_bytes: int, random_data: bool = False) -> None:
    """Create a single file of the exact size."""
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "wb") as f:
        if size_bytes <= 0:
            return

        if random_data:
            # Write in chunks to avoid using too much RAM
            chunk_size = 1024 * 1024  # 1 MB chunks
            remaining = size_bytes
            while remaining > 0:
                to_write = min(chunk_size, remaining)
                f.write(os.urandom(to_write))
                remaining -= to_write
        else:
            # Fast sparse-style zero file
            f.seek(size_bytes - 1)
            f.write(b"\0")


def interactive_mode():
    print("=" * 60)
    print("  File Generator (Interactive Mode)")
    print("=" * 60)

    # Folder
    print("\nWhere do you want to save the file(s)?")
    print("1. Downloads folder (default)")
    print("2. Custom folder")
    choice = input("Enter choice [1/2]: ").strip() or "1"

    if choice == "2":
        folder = Path(input("Enter full folder path: ").strip()).expanduser()
    else:
        folder = get_downloads_folder()
        print(f"→ Using: {folder}")

    # Number of files
    count_str = input("\nHow many files do you want to create? [1]: ").strip() or "1"
    try:
        count = max(1, int(count_str))
    except ValueError:
        count = 1

    # Random data?
    rand_choice = input("Fill with random data? (y/N): ").strip().lower()
    random_data = rand_choice in ("y", "yes")

    created = []

    for i in range(count):
        print(f"\n--- File {i + 1} of {count} ---")

        name = input("Filename (without extension) [leave empty for random]: ").strip()
        if not name:
            name = generate_random_name()
            print(f"→ Using random name: {name}")

        extension = input("Extension (e.g. jpg, mp4, pdf): ").strip()
        if extension.startswith("."):
            extension = extension[1:]

        filename = f"{name}.{extension}" if extension else name

        size_input = input("Size (e.g. 5MB, 200KB, 1.5GB): ").strip()
        try:
            size_bytes = parse_size(size_input)
        except ValueError as e:
            print(f"Error: {e}")
            continue

        filepath = folder / filename
        try:
            create_file(filepath, size_bytes, random_data=random_data)
            actual = filepath.stat().st_size
            print(f"✅ Created: {filepath} ({actual:,} bytes)")
            created.append(filepath)
        except Exception as e:
            print(f"❌ Failed: {e}")

    print("\n" + "=" * 60)
    print(f"Done! {len(created)} file(s) created.")
    print("=" * 60)


def cli_mode(args):
    folder = Path(args.folder).expanduser() if args.folder else get_downloads_folder()

    names = args.name or []
    sizes = args.size or []
    extensions = args.ext or []

    # Determine how many files to create
    count = max(len(names), len(sizes), len(extensions), 1)

    # Pad lists so they all have the same length
    if not names:
        names = [None] * count  # None → will generate random name
    else:
        names += [names[-1]] * (count - len(names))

    if not sizes:
        print("Error: --size is required in CLI mode.")
        sys.exit(1)
    else:
        sizes += [sizes[-1]] * (count - len(sizes))

    if not extensions:
        extensions = [""] * count
    else:
        extensions += [extensions[-1]] * (count - len(extensions))

    for name, size_str, ext in zip(names, sizes, extensions):
        if not name:
            name = generate_random_name()

        try:
            size_bytes = parse_size(size_str)
        except ValueError as e:
            print(f"Error with size '{size_str}': {e}")
            continue

        if ext.startswith("."):
            ext = ext[1:]
        filename = f"{name}.{ext}" if ext else name
        filepath = folder / filename

        try:
            create_file(filepath, size_bytes, random_data=args.random)
            actual = filepath.stat().st_size
            print(f"✅ {filepath}  ({actual:,} bytes)")
        except Exception as e:
            print(f"❌ Failed to create {filepath}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate files of any name, extension and size.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_file.py
      → Interactive mode

  python generate_file.py -e jpg -s 8MB
      → Creates a random-named .jpg file (8 MB) in Downloads

  python generate_file.py -n photo -e jpg -s 8MB
      → Creates photo.jpg (8 MB)

  python generate_file.py -n movie -e mp4 -s 1.5GB --random
      → Creates movie.mp4 filled with random data

  python generate_file.py -e pdf -s 3MB -f ~/Documents
      → Creates a random-named .pdf in Documents

  python generate_file.py -n img1 img2 -e png jpg -s 2MB 5MB
      → Creates two files at once
        """
    )

    parser.add_argument("-n", "--name", nargs="+", help="Filename(s) without extension (optional – random if omitted)")
    parser.add_argument("-e", "--ext", nargs="+", help="Extension(s) e.g. jpg mp4 pdf")
    parser.add_argument("-s", "--size", nargs="+", help="Size(s) e.g. 5MB 1.5GB 200KB")
    parser.add_argument("-f", "--folder", help="Target folder (default: Downloads)")
    parser.add_argument("--random", action="store_true", help="Fill with random data instead of zeros")

    args = parser.parse_args()

    # If any creation-related arguments are given → CLI mode
    if any([args.name, args.size, args.ext, args.folder, args.random]):
        cli_mode(args)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()