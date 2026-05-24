"""Main pipeline script."""

from os import getcwd, path
from subprocess import CalledProcessError, Popen, run
from sys import argv, executable
from sys import exit as sys_exit

from scripts.utils.notif import send_notification

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


def main() -> None:
    """Entrypoint of pipeline."""
    # Check for arguments
    has_argument = len(argv) > 1

    if not has_argument:
        if NEW_DATA:
            run_sequential([executable, "combine_raw_chars.py"], cwd=SCRIPTS_DIR)
            run_sequential([executable, "hash.py"], cwd=SCRIPTS_DIR)
            run_sequential([executable, "up_data.py", "-y"], cwd=HF_DATA_DIR)
            run_sequential([executable, "up_data.py", "-n"], cwd=HF_DATA_DIR)
            run_sequential([executable, "generate_config.py"], cwd=HF_DATA_DIR)

        run_parallel(
            [
                [executable, "csv_to_pickle.py", "-moc"],
                [executable, "csv_to_pickle.py", "-pf"],
                [executable, "csv_to_pickle.py", "-aa"],
                [executable, "csv_to_pickle.py", "-as"],
            ],
            cwd=SCRIPTS_DIR,
        )

    # --- Compile Section ---
    print("\nCompile")
    run_parallel(
        [
            [executable, "comp_rates.py", "-w", "-moc"],
            [executable, "comp_rates.py", "-f", "-moc"],
            [executable, "comp_rates.py", "-a", "-moc"],
            [executable, "comp_rates.py", "-w", "-pf"],
            [executable, "comp_rates.py", "-f", "-pf"],
            [executable, "comp_rates.py", "-a", "-pf"],
            [executable, "comp_rates.py", "-w", "-as"],
            [executable, "comp_rates.py", "-f", "-as"],
            [executable, "comp_rates.py", "-a", "-as"],
            [executable, "comp_rates.py", "-w", "-aa"],
            [executable, "comp_rates.py", "-f", "-aa"],
            [executable, "comp_rates.py", "-a", "-aa"],
        ],
        cwd=SCRIPTS_DIR,
    )

    # --- Stats Section ---
    print("\nStats")
    run_parallel(
        [
            [executable, "stats.py", "-moc"],
            [executable, "stats.py", "-pf"],
            [executable, "stats.py", "-as"],
            [executable, "stats.py", "-aa"],
        ],
        cwd=MIHOMO_DIR,
    )

    # --- Compile Results Section ---
    print("\nProcessing Compile Results")
    run_parallel(
        [
            [executable, "combine_char.py"],
            [executable, "histograph.py"],
            [executable, "combine_comp.py", "-moc"],
            [executable, "combine_comp.py", "-pf"],
            [executable, "combine_comp.py", "-as"],
            [executable, "combine_comp.py", "-aa"],
            [executable, "combine_duo.py", "-moc"],
            [executable, "combine_duo.py", "-pf"],
            [executable, "combine_duo.py", "-as"],
            [executable, "combine_duo.py", "-aa"],
        ],
        cwd=COMPILE_RESULT_DIR,
    )

    # --- Optional Web Results Deployment ---
    if path.isdir(WEB_RESULTS_DIR):
        print("\nWeb results directory found. Copying files...")
        run_sequential([executable, "copyfiles.py", "-moc"], cwd=COMPILE_RESULT_DIR)
        run_sequential([executable, "copyfiles.py", "-pf"], cwd=COMPILE_RESULT_DIR)
        run_sequential([executable, "copyfiles.py", "-as"], cwd=COMPILE_RESULT_DIR)
        run_sequential([executable, "copyfiles.py", "-aa"], cwd=COMPILE_RESULT_DIR)

        if NEW_DATA:
            run_sequential([executable, "up_results.py"], cwd=HF_DATA_DIR)
    else:
        print("\nWeb results directory not found. Skipping copy and upload.")


if __name__ == "__main__":
    try:
        main()
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
