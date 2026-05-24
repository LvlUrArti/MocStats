"""Copy json files."""

from pathlib import Path
from shutil import copyfile


def copy_json_files(src_dir: Path, dst_dir: Path) -> None:
    """Copy all .json files from src_dir to dst_dir, creating dst_dir if needed."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    for json_file in src_dir.glob("*.json"):
        copyfile(json_file, dst_dir / json_file.name)
