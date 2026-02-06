"""Generate a list of configs from a folder of csv files."""

from argparse import ArgumentParser
from os import listdir
from os.path import dirname, exists, join
from time import sleep

from huggingface_hub import (
    CommitOperationAdd,
    HfApi,
    hf_hub_download,  # pyright: ignore[reportUnknownVariableType]
)
from huggingface_hub.repocard import RepoCard
from plyer import notification  # type: ignore[reportMissingTypeStubs]
from send2trash import send2trash

# Prompt for real data
parser = ArgumentParser()
parser.add_argument("-y", "--yes", action="store_true")
parser.add_argument("-n", "--no", action="store_true")
args = parser.parse_args()


yes_arg: bool | None = args.yes
no_arg: bool | None = args.no

if yes_arg:
    is_real_suffix = True
elif no_arg:
    is_real_suffix = False
else:
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

CHUNK_SIZE = 3
REPO_ID = f"LvlUrArti/MocData{'Real' if is_real_suffix else ''}"
DEFAULT_README = (
    "# MocData\n\nUsed alongside my [data compilation repository]"
    "(https://github.com/LvlUrArti/MocStats). Feel free to analyze the data"
    " and post the findings. If you do, please credit me (LvlUrArti)."
    "\n\n[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Q5Q4IJ3P6)"
)
# =================================================


def get_version_map(filenames: list[str]) -> dict[str, list[dict[str, str]]]:
    """Group filenames by version and identifies their splits.

    Returns: { "version_str": [{"split": "split_name", "path": "filename.csv"}, ...] }.
    """
    version_map: dict[str, list[dict[str, str]]] = {}

    for filename in sorted(filenames):
        # Remove supported extensions
        name_no_ext: str = filename.replace(".csv", "").replace(".json", "")

        version: str = ""
        split_name: str = ""

        # Logic: Check if filename ends with a known suffix
        matched_suffix: bool = False
        for suffix in KNOWN_SUFFIXES:
            if name_no_ext.endswith(f"_{suffix}"):
                split_name = suffix
                version = name_no_ext[: -(len(suffix) + 1)]
                matched_suffix = True
                break

        if not matched_suffix:
            version = name_no_ext
            split_name = "moc"

        if version not in version_map:
            version_map[version] = []

        version_map[version].append({"split": split_name, "path": filename})

    return version_map


def scan_upload_and_clean() -> None:
    """Scan, uploads to HF, adds to the tracking CSV.

    Keeps only last version locally.
    """
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
    else:
        print(f"📦 Found {len(files_to_upload)} files. Uploading to {REPO_ID}...")

        # 3. Upload to Hugging Face in chunks
        for i in range(0, len(files_to_upload), CHUNK_SIZE):
            batch = files_to_upload[i : i + CHUNK_SIZE]

            # Prepare the operations for this specific batch
            operations = [
                CommitOperationAdd(
                    path_in_repo=filename,
                    path_or_fileobj=join(LOCAL_DATA_DIR, filename),
                )
                for filename in batch
            ]

            try:
                api.create_commit(
                    repo_id=REPO_ID,
                    operations=operations,
                    commit_message=f"🤖 Batch upload {len(batch)} files",
                    repo_type="dataset",
                )
                print(
                    f"   ✅ Successfully uploaded batch {i // CHUNK_SIZE + 1}: {batch}",
                )
            except Exception as e:
                print(
                    f"   ❌ Failed to upload batch starting with {batch[0]}."
                    f" Error: {e}",
                )
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

    # 5. Delete local files
    print("🧹 Starting smart cleanup of local files...")

    # Use the new centralized logic
    local_version_map = get_version_map(files_to_upload)

    # Determine which versions to keep
    sorted_versions = sorted(local_version_map.keys(), reverse=True)
    versions_to_keep = sorted_versions[:1]

    print(f"📌 Versions to keep locally: {versions_to_keep}")

    # Delete versions not in the keep list
    for version, file_infos in local_version_map.items():
        if not is_real_suffix or version not in versions_to_keep:
            for info in file_infos:
                filename = info["path"]
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

    # Dictionary to hold data: { "1.0.1": [ {split: 'moc', path: '...'}, ... ] }
    version_map = get_version_map(repo_files)

    # Construct the final YAML structure
    # We sort versions to keep the file tidy
    final_configs: list[dict[str, str | list[dict[str, str]]]] = []

    sorted_versions: list[str] = sorted(version_map.keys(), reverse=True)

    final_configs.extend(
        {"config_name": ver, "data_files": version_map[ver]} for ver in sorted_versions
    )

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

    notification.notify(
        title="Finished",
        message="Finished uploading data",
        # displaying time
        timeout=2,
    )  # pyright: ignore[reportOptionalCall]
    sleep(0.1)
