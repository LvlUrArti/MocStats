"""Generate a list of configs from a folder of csv files."""

# pyright: reportUnknownVariableType=false, reportMissingTypeStubs=false, reportOptionalCall=false
from os.path import exists
from time import sleep

from huggingface_hub import HfApi
from huggingface_hub.repocard import RepoCard
from plyer import notification

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
        api.upload_folder(
            folder_path=LOCAL_DATA_DIR,
            repo_id=REPO_ID,
            repo_type="dataset",
            commit_message="🤖 Upload new data",
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

    notification.notify(
        title="Finished",
        message="Finished uploading data",
        timeout=2,
    )
    sleep(0.1)
