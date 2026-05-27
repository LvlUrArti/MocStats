"""Main pipeline script."""

from os import getcwd, mkdir, path
from subprocess import CalledProcessError, Popen, run
from sys import executable as exe
from sys import exit as sys_exit

from scripts.utils.notif import send_notification
from send2trash import send2trash

# Define absolute directory tracks relative to where this script is launched
BASE_DIR = getcwd()
SCRIPTS_DIR = path.join(BASE_DIR, "scripts")
HF_DATA_DIR = path.join(SCRIPTS_DIR, "hf_data")
MIHOMO_DIR = path.join(BASE_DIR, "mihomo")
COMPILE_RESULT_DIR = path.join(SCRIPTS_DIR, "compile_result")
WEB_RESULTS_DIR = path.join(BASE_DIR, "results", "web_results")
NEW_DATA = False


def run_sequential(cmd: list[str], cwd: str) -> None:
    """Run a single command and blocks until finished."""
    run(cmd, cwd=cwd, check=True)


def run_parallel(cmds: list[list[str]], cwd: str) -> None:
    """Launch a group of commands simultaneously, waits for all to finish.

    Stops the pipeline immediately if any command fails.
    """
    processes: list[tuple[list[str], Popen[bytes]]] = []
    # Launch all commands concurrently
    for cmd in cmds:
        p = Popen(cmd, cwd=cwd)
        processes.append((cmd, p))

    # Wait for all processes to complete and check for errors
    failed_commands: list[str] = []
    for cmd, p in processes:
        exit_code = p.wait()
        if exit_code != 0:
            failed_commands.append(
                f"'{' '.join(cmd)}' failed with exit code {exit_code}",
            )

    if failed_commands:
        print("\n🛑 Pipeline halted due to parallel execution errors:")
        for error in failed_commands:
            print(error)
        sys_exit(1)


def main(add_args: list[str] | None = None) -> None:
    """Entrypoint of pipeline.

    add_args: Additional arguments to pass.
    """
    if add_args is None:
        add_args = []

    if NEW_DATA:
        run_sequential([exe, "combine_raw_chars.py", *add_args], cwd=SCRIPTS_DIR)
        run_sequential([exe, "hash.py", *add_args], cwd=SCRIPTS_DIR)
        run_sequential([exe, "up_data.py", "-y", *add_args], cwd=HF_DATA_DIR)
        run_sequential([exe, "up_data.py", "-n", *add_args], cwd=HF_DATA_DIR)
        run_sequential([exe, "generate_config.py", *add_args], cwd=HF_DATA_DIR)

    run_parallel(
        [
            [exe, "csv_to_pickle.py", "-m", "moc", *add_args],
            [exe, "csv_to_pickle.py", "-m", "pf", *add_args],
            [exe, "csv_to_pickle.py", "-m", "aa", *add_args],
            [exe, "csv_to_pickle.py", "-m", "as", *add_args],
        ],
        cwd=SCRIPTS_DIR,
    )

    # --- Compile Section ---
    print("\nCompile")
    run_parallel(
        [
            [exe, "comp_rates.py", "-w", "-m", "moc", *add_args],
            [exe, "comp_rates.py", "-f", "-m", "moc", *add_args],
            [exe, "comp_rates.py", "-a", "-m", "moc", *add_args],
        ],
        cwd=SCRIPTS_DIR,
    )

    run_parallel(
        [
            [exe, "comp_rates.py", "-w", "-m", "pf", *add_args],
            [exe, "comp_rates.py", "-f", "-m", "pf", *add_args],
            [exe, "comp_rates.py", "-a", "-m", "pf", *add_args],
        ],
        cwd=SCRIPTS_DIR,
    )

    run_parallel(
        [
            [exe, "comp_rates.py", "-w", "-m", "as", *add_args],
            [exe, "comp_rates.py", "-f", "-m", "as", *add_args],
            [exe, "comp_rates.py", "-a", "-m", "as", *add_args],
        ],
        cwd=SCRIPTS_DIR,
    )

    run_parallel(
        [
            [exe, "comp_rates.py", "-w", "-m", "aa", *add_args],
            [exe, "comp_rates.py", "-f", "-m", "aa", *add_args],
            [exe, "comp_rates.py", "-a", "-m", "aa", *add_args],
        ],
        cwd=SCRIPTS_DIR,
    )

    # --- Stats Section ---
    print("\nStats")
    run_parallel(
        [
            [exe, "stats.py", "-m", "moc", *add_args],
            [exe, "stats.py", "-m", "pf", *add_args],
            [exe, "stats.py", "-m", "as", *add_args],
            [exe, "stats.py", "-m", "aa", *add_args],
        ],
        cwd=MIHOMO_DIR,
    )

    # --- Compile Results Section ---
    print("\nProcessing Compile Results")
    run_parallel(
        [
            [exe, "combine_char.py", *add_args],
            [exe, "histograph.py", *add_args],
            [exe, "combine_comp.py", "-m", "moc", *add_args],
            [exe, "combine_comp.py", "-m", "pf", *add_args],
            [exe, "combine_comp.py", "-m", "as", *add_args],
            [exe, "combine_comp.py", "-m", "aa", *add_args],
            [exe, "combine_duo.py", "-m", "moc", *add_args],
            [exe, "combine_duo.py", "-m", "pf", *add_args],
            [exe, "combine_duo.py", "-m", "as", *add_args],
            [exe, "combine_duo.py", "-m", "aa", *add_args],
        ],
        cwd=COMPILE_RESULT_DIR,
    )

    # --- Optional Web Results Deployment ---
    if path.isdir(WEB_RESULTS_DIR):
        send2trash(WEB_RESULTS_DIR)
        mkdir(WEB_RESULTS_DIR)

        run_parallel(
            [
                [exe, "copyfiles.py", "-m", "moc", *add_args],
                [exe, "copyfiles.py", "-m", "pf", *add_args],
                [exe, "copyfiles.py", "-m", "as", *add_args],
                [exe, "copyfiles.py", "-m", "aa", *add_args],
            ],
            cwd=COMPILE_RESULT_DIR,
        )
        run_sequential([exe, "copy_common.py", *add_args], cwd=COMPILE_RESULT_DIR)

        if NEW_DATA:
            run_sequential([exe, "up_results.py", *add_args], cwd=HF_DATA_DIR)
    else:
        print("\nWeb results directory not found. Skipping copy and upload.")


if __name__ == "__main__":
    versions_to_process = ["3.0.1", "3.0.2"]

    try:
        for ver in versions_to_process:
            print(f"\nProcessing {ver}")
            main(["-v", ver])

        print("\n🎉 Full pipeline executed successfully!")
        send_notification(
            "🎉 Pipeline Complete",
            "All compilation and stats tasks have finished successfully.",
        )
    except CalledProcessError as e:
        print(f"\n🛑 Pipeline halted. Sequential command failed: {e.cmd}")
        send_notification(
            "❌ Pipeline Stopped",
            f"Sequential process failed: {e.cmd[1]}",
        )
        sys_exit(1)
