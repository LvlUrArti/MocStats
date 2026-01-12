"""Generate a list of configs from a folder of csv files."""

from os import listdir
from os.path import dirname, exists, join
from time import sleep

from huggingface_hub import (
    HfApi,
    hf_hub_download,  # pyright: ignore[reportUnknownVariableType]
)
from huggingface_hub.repocard import RepoCard
from plyer import notification  # type: ignore[reportMissingTypeStubs]
from send2trash import send2trash

# Prompt for real data
is_real_suffix = input("Real data? (y/n): ")
is_real_suffix = is_real_suffix == "y"
real_suffix = "_real" if is_real_suffix else ""

# ================= CONFIGURATION =================
# Define known suffixes (DO NOT include the underscore).
# If a file ends in "_char.csv", it will be treated as the 'char' split.
# Any part of the filename BEFORE the suffix becomes the Version ID.
KNOWN_SUFFIXES: list[str] = ["char", "pf", "as", "aa", "build"]

# Where to look for NEW files to upload
LOCAL_DATA_DIR = f"../../data/raw_csvs{real_suffix}"

# The local tracking file
CSV_LIST_FILE = f"repo_files{real_suffix}.csv"
CSV_LIST = join("../../data", CSV_LIST_FILE)

REPO_ID = f"LvlUrArti/MocData{'Real' if is_real_suffix else ''}"
DEFAULT_README = (
    "# MocData\n\nUsed alongside my [data compilation repository]"
    "(https://github.com/LvlUrArti/MocStats). Feel free to analyze the data"
    " and post the findings. If you do, please credit me (LvlUrArti)."
    "\n\n[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Q5Q4IJ3P6)"
)
# =================================================


def scan_upload_and_clean() -> None:
    """Scan, uploads to HF, adds to the tracking CSV, deletes local copies."""
    api = HfApi()

    # 1. Download latest tracking
    print(f"📥 Downloading latest {CSV_LIST_FILE} from Hub...")
    try:
        # We download the file from the repo to our local path
        hf_hub_download(
            repo_id=REPO_ID,
            filename=CSV_LIST_FILE,
            repo_type="dataset",
            local_dir=dirname(CSV_LIST),  # Save to local folder
            force_download=True,  # Ensure we get the latest
        )
    except Exception:
        print("⚠️  Could not download tracking. Using local.")

    # 2. Identify files
    if not exists(LOCAL_DATA_DIR):
        print(f"⚠️  Scan folder not found: {LOCAL_DATA_DIR}")
        return

    files_to_upload = [
        f for f in listdir(LOCAL_DATA_DIR) if f.endswith((".csv", ".json"))
    ]

    if not files_to_upload:
        print("✨ No new files found to upload.")
        return

    print(f"📦 Found {len(files_to_upload)} files. Uploading to {REPO_ID}...")

    # 3. Upload to Hugging Face
    # Using upload_folder is more efficient than looping upload_file
    try:
        api.upload_folder(
            folder_path=LOCAL_DATA_DIR,
            repo_id=REPO_ID,
            repo_type="dataset",
            allow_patterns=["*.csv", "*.json"],
            commit_message=f"Upload {len(files_to_upload)} new data files",
        )
        print("✅ Upload successful.")
    except Exception:
        print("⚠️  Failed to upload data.")
        return

    # 4. Update local tracking CSV
    print(f"📝 Updating {CSV_LIST_FILE}...")

    # Read existing entries to prevent duplicates
    existing_files: set[str] = set()
    if exists(CSV_LIST):
        with open(CSV_LIST) as f:
            existing_files = {line.strip() for line in f}

    with open(CSV_LIST, "a") as f:
        for filename in files_to_upload:
            if filename not in existing_files:
                f.write(f"{filename}\n")
                print(f"   + Added {filename}")
            else:
                print(f"   . Skipping duplicate in list: {filename}")

    # 5. Delete local files
    print("🗑️  Cleaning up local files...")
    for filename in files_to_upload:
        file_path = join(LOCAL_DATA_DIR, filename)
        try:
            send2trash(file_path)
            print(f"   - Deleted {filename}")
        except OSError as e:
            print(f"   ❌ Error deleting {filename}: {e}")

    # 6. Sync the tracking CSV
    print(f"⬆️  Syncing {CSV_LIST_FILE} back to Hub...")
    api.upload_file(
        path_or_fileobj=CSV_LIST,
        path_in_repo=CSV_LIST_FILE,
        repo_id=REPO_ID,
        repo_type="dataset",
        commit_message="📝 Update tracking CSV",
    )
    print("✅ Tracking CSV synced.")


def generate_yaml_config() -> list[dict[str, str | list[dict[str, str]]]]:
    """Generate a YAML config from a folder of CSV files."""
    # Read files from repo_files.csv
    repo_files: list[str] = []

    with open(CSV_LIST) as f:
        repo_files.extend(line.strip() for line in f)

    # Get all CSV files
    all_files: set[str] = set(repo_files)

    # Track which files we successfully add to the config
    processed_files: set[str] = set()

    # Dictionary to hold data: { "1.0.1": [ {split: 'moc', path: '...'}, ... ] }
    version_map: dict[str, list[dict[str, str]]] = {}

    for filename in sorted(all_files):
        # Remove extension
        name_no_ext: str = filename.replace(".csv", "").replace(".json", "")

        version: str = ""
        split_name: str = ""

        # Logic: Check if filename ends with a known suffix
        matched_suffix: bool = False
        for suffix in KNOWN_SUFFIXES:
            # Check for "_suffix" at the end of the name
            if name_no_ext.endswith(f"_{suffix}"):
                # Example: 2.7.1_old_char -> version: 2.7.1_old, split: char
                split_name = suffix
                # Remove "_suffix" from the end to get version
                version = name_no_ext[: -(len(suffix) + 1)]
                matched_suffix = True
                break

        # If no suffix matched, assume it is the moc file for that version
        if not matched_suffix:
            # Example: 2.7.1_old.csv -> version: 2.7.1_old, split: moc
            version = name_no_ext
            split_name = "moc"

        # Add to our map
        if version not in version_map:
            version_map[version] = []

        version_map[version].append({"split": split_name, "path": filename})

        processed_files.add(filename)

    # Construct the final YAML structure
    # We sort versions to keep the file tidy
    final_configs: list[dict[str, str | list[dict[str, str]]]] = []

    sorted_versions: list[str] = sorted(version_map.keys(), reverse=True)

    final_configs.extend(
        {"config_name": ver, "data_files": version_map[ver]} for ver in sorted_versions
    )

    # ================= OUTPUT =================

    # 1. Print Unused Files (Audit)
    unused_files: set[str] = all_files - processed_files

    print("-" * 40)
    if unused_files:
        print(f"⚠️  WARNING: {len(unused_files)} files were NOT added to the config:")
        for f in sorted(unused_files):
            print(f"   - {f}")
        print(
            "\n(Check if these files have typos or missing suffixes in KNOWN_SUFFIXES)",
        )
    else:
        print("✨ All .csv files were successfully mapped to a version.")
    print("-" * 40)

    # 2. Return the YAML config
    return final_configs


def update_readme(
    new_config_data: list[dict[str, str | list[dict[str, str]]]],
) -> None:
    """Update the README with the new configs."""
    print(f"🔄 Fetching README.md from {REPO_ID}...")

    # 1. Load the existing README (RepoCard handles the split between YAML and Text)
    try:
        readme_path = hf_hub_download(
            repo_id=REPO_ID,
            filename="README.md",
            repo_type="dataset",
        )
        old_card = RepoCard.load(readme_path)
        card = (
            RepoCard(old_card.text.replace("\r\n", "\n"))
            if old_card.text
            else RepoCard(DEFAULT_README)
        )
    except Exception:
        print("⚠️  No README found. Creating a new one.")
        card = RepoCard(DEFAULT_README)

    # 2. Update the metadata
    card.data["license"] = "mit"
    card.data["configs"] = new_config_data

    # 3. Push the update to Hugging Face
    print("🚀 Uploading updated README to the Hub...")
    card.push_to_hub(
        repo_id=REPO_ID,
        repo_type="dataset",
        commit_message="🤖 Auto-update dataset configurations",
    )

    print("✅ Done! Check your dataset page.")


if __name__ == "__main__":
    scan_upload_and_clean()
    config = generate_yaml_config()
    update_readme(config)

    if __name__ == "__main__":
        notification.notify(
            title="Finished",
            message="Finished uploading data",
            # displaying time
            timeout=2,
        )  # pyright: ignore[reportOptionalCall]
        sleep(0.1)
