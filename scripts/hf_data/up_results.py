"""Generate a list of configs from a folder of csv files."""

from os.path import exists
from sys import path as sys_path

sys_path.append("../")
from comp_rates_config import RECENT_PHASE
from huggingface_hub import HfApi
from huggingface_hub.repocard import RepoCard
from utils.notif import send_notification

# ================= CONFIGURATION =================
# Where to look for NEW files to upload
LOCAL_DATA_DIR = "../../results/final_results"

REPO_ID = "LvlUrArti/MocDataProcessed"
DEFAULT_README = (
    "# MocDataProcessed\n\n"
    "Contains the processed data as shown on the Prydwen website.\n\n"
    "Used alongside my [data processing repository]"
    "(https://github.com/LvlUrArti/MocStats). Feel free to analyze the data and post "
    "the findings. If you do, please credit me (LvlUrArti).\n\n"
    "[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Q5Q4IJ3P6)"
)
# =================================================


def scan_upload_and_clean() -> None:
    """Scan, uploads to HF, adds to the tracking CSV.

    Keeps only last version locally.
    """
    api = HfApi()

    # 2. Identify files
    if not exists(LOCAL_DATA_DIR):
        print(f"⚠️  Scan folder not found: {LOCAL_DATA_DIR}")
        return

    # 3. Upload to Hugging Face in chunks"""
    """Uploads all contents of a local folder to a Hugging Face Dataset repo.
    """

    print(f"🚀 Starting upload from {LOCAL_DATA_DIR} to {REPO_ID}...")

    try:
        api.upload_file(
            path_or_fileobj=f"{LOCAL_DATA_DIR}/config.json",
            path_in_repo="config.json",
            repo_id=REPO_ID,
            repo_type="dataset",
            commit_message=f"🤖 Upload {RECENT_PHASE} config",
        )
        api.upload_folder(
            folder_path=f"{LOCAL_DATA_DIR}/{RECENT_PHASE}",
            path_in_repo=RECENT_PHASE,
            repo_id=REPO_ID,
            repo_type="dataset",
            commit_message=f"🤖 Upload {RECENT_PHASE} data",
        )
        print("✅ Upload successful!")
    except Exception as e:
        print(f"❌ An error occurred: {e}")


def update_readme() -> None:
    """Update the README with the new configs."""
    print(f"🔄 Fetching README.md from {REPO_ID}...")

    card = RepoCard(DEFAULT_README)

    # 2. Update the metadata
    card.data["license"] = "mit"

    # 3. Push the update to Hugging Face
    print("🚀 Uploading updated README to the Hub...")
    card.push_to_hub(
        repo_id=REPO_ID,
        repo_type="dataset",
        commit_message="🤖 Update README",
    )

    print("✅ Done! Check your dataset page.")


if __name__ == "__main__":
    scan_upload_and_clean()
    update_readme()
    send_notification("Finished", "Finished uploading data")
