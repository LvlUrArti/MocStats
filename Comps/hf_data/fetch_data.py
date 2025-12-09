"""Fetch data from Huggingface Hub."""

from typing import cast

from huggingface_hub import (
    snapshot_download,  # pyright: ignore[reportUnknownVariableType]
)
from up_data import LOCAL_DATA_DIR, REPO_ID, generate_yaml_config

config = generate_yaml_config()
config_name = cast("str", config[0]["config_name"])

confirm = input(f"Download files from {REPO_ID} with config {config_name}? (y/n): ")

if confirm == "n":
    config_name = input("Config name: ")
    confirm = input("Download files with this config? (y/n): ")

if confirm == "y":
    snapshot_download(
        repo_id=REPO_ID,
        allow_patterns=f"{config_name}*",
        local_dir=LOCAL_DATA_DIR,
        repo_type="dataset",
    )
