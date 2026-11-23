"""Update endgame version data from nanoka."""

# pyright: reportUnknownVariableType=false
# ruff: noqa: ANN401

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests

ENDGAME_VERSIONS_PATH = "../data/versions/endgame_versions.json"
ENDGAME_VERSION_LABELS_PATH = "../data/versions/endgame_version_labels.json"


@dataclass(frozen=True)
class EndgameSpec:
    """Describe one endgame data source."""

    name: str
    version_path: str | None
    metadata_path: str


@dataclass
class EndgameContext:
    """Hold shared state for the endgame update."""

    existing: dict[str, dict[str, dict[str, str]]]
    labels: dict[str, dict[str, str]]


SPECS = (
    EndgameSpec(
        name="Memory of Chaos",
        version_path="en/maze/version.json",
        metadata_path="maze.json",
    ),
    EndgameSpec(
        name="Pure Fiction",
        version_path=None,
        metadata_path="maze_extra.json",
    ),
    EndgameSpec(
        name="Apocalyptic Shadow",
        version_path=None,
        metadata_path="maze_boss.json",
    ),
    # maze_peak.json has names only; times come from the existing output.
    EndgameSpec(
        name="Anomaly Arbitration",
        version_path="en/peak/version.json",
        metadata_path="maze_peak.json",
    ),
)


def _load_from_url(url: str, *, allow_missing: bool = False) -> Any:
    """Load JSON data from a URL."""
    response = requests.get(url, timeout=20)
    if allow_missing and response.status_code == 404:
        print(f"Missing version groups at {url}; falling back to prompts")
        return None
    response.raise_for_status()
    return json.loads(response.content.decode("utf-8"))


def format_date(value: str) -> str:
    """Format an ISO date string as DD/MM/YYYY."""
    return datetime.strptime(
        value.split(" ", maxsplit=1)[0],
        "%Y-%m-%d",
    ).strftime("%d/%m/%Y")


def get_name(info: dict[str, Any]) -> str:
    """Return the English display name for an endgame entry."""
    return (
        str(info.get("en") or "")
        .replace("<unbreak>", "")
        .replace("</unbreak>", "")
        .strip()
    )


def get_times(info: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return live start and end dates from an endgame entry."""
    begin = info.get("live_begin") or info.get("begin")
    end = info.get("live_end") or info.get("end")
    time_start = format_date(str(begin)) if begin else None
    time_end = format_date(str(end)) if end else None
    return time_start, time_end


def load_existing_versions() -> dict[str, dict[str, dict[str, str]]]:
    """Load the previously generated endgame versions."""
    try:
        with open(ENDGAME_VERSIONS_PATH) as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def load_version_labels() -> dict[str, dict[str, str]]:
    """Load the persistent version ID to label mapping."""
    try:
        with open(ENDGAME_VERSION_LABELS_PATH) as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_version_labels(labels: dict[str, dict[str, str]]) -> None:
    """Save the persistent version ID to label mapping."""
    with open(ENDGAME_VERSION_LABELS_PATH, "w") as out_file:
        out_file.write(json.dumps(labels, indent=2))


def label_sort_key(label: str) -> tuple[int, ...]:
    """Return a sortable key for a numeric version label."""
    return tuple(int(part) for part in label.split("."))


def build_labels_from_groups(
    kind: str,
    groups: dict[str, list[Any]],
    metadata: dict[str, dict[str, Any]],
) -> tuple[dict[str, str], set[str]]:
    """Build labels and ignored IDs from a version.json group file."""
    labels: dict[str, str] = {}
    ignored_ids: set[str] = set()
    used_ids: set[str] = set()
    for patch, raw_ids in groups.items():
        if patch in {"static", "unknown"}:
            ignored_ids.update(str(raw_id) for raw_id in raw_ids)
            continue
        for index, raw_id in enumerate(raw_ids, start=1):
            version_id = str(raw_id)
            if version_id not in metadata:
                print(f"{kind}: version ID {version_id} not found; skipping")
                continue
            if version_id in used_ids:
                print(f"{kind}: duplicate version ID {version_id}; skipping")
                continue
            label = f"{patch}.{index}"
            labels[label] = version_id
            used_ids.add(version_id)
    return labels, ignored_ids


def seed_labels(
    kind: str,
    missing_ids: list[str],
    metadata: dict[str, dict[str, Any]],
    context: EndgameContext,
    used_labels: set[str],
) -> list[str]:
    """Seed labels from the existing output by dates or unique name."""
    remaining: list[str] = []
    seeded = False
    existing_versions = context.existing.get(kind, {})
    for version_id in missing_ids:
        info = metadata[version_id]
        time_start, time_end = get_times(info)
        matches: list[str] = []
        if time_start and time_end:
            matches = [
                label
                for label, entry in existing_versions.items()
                if entry.get("time_start") == time_start
                and entry.get("time_end") == time_end
                and label not in used_labels
            ]
        if len(matches) == 1:
            label = matches[0]
            context.labels.setdefault(kind, {})[version_id] = label
            used_labels.add(label)
            seeded = True
            print(f"Seeded {kind} {version_id} -> {label} from existing dates")
            continue

        name = get_name(info)
        if name:
            name_matches = [
                label
                for label, entry in existing_versions.items()
                if entry.get("name") == name and label not in used_labels
            ]
            if len(name_matches) == 1:
                label = name_matches[0]
                context.labels.setdefault(kind, {})[version_id] = label
                used_labels.add(label)
                seeded = True
                print(f"Seeded {kind} {version_id} -> {label} from existing name")
                continue
        remaining.append(version_id)
    if seeded:
        save_version_labels(context.labels)
    return remaining


def get_next_phase(patch: str, used_labels: set[str]) -> int:
    """Return the next phase number for a patch."""
    prefix = f"{patch}."
    phases = [
        int(label.removeprefix(prefix))
        for label in used_labels
        if label.startswith(prefix) and label.removeprefix(prefix).isdigit()
    ]
    return max(phases, default=0) + 1


def parse_patch_count(value: str) -> tuple[str, int] | None:
    """Parse a '<major>.<minor> <count>' prompt answer."""
    parts = value.replace(":", " ").replace("=", " ").split()
    if len(parts) != 2:
        return None
    patch, count_text = parts
    if not re.fullmatch(r"\d+\.\d+", patch):
        return None
    if not count_text.isdigit():
        return None
    count = int(count_text)
    if count < 1:
        return None
    return patch, count


def prompt_for_labels(
    kind: str,
    missing_ids: list[str],
    metadata: dict[str, dict[str, Any]],
    context: EndgameContext,
    used_labels: set[str],
) -> None:
    """Prompt for labels of version IDs missing from version.json."""
    remaining = sorted(
        missing_ids,
        key=lambda version_id: (
            metadata[version_id].get("live_begin")
            or metadata[version_id].get("begin")
            or str(version_id)
        ),
    )
    mapping = context.labels.setdefault(kind, {})
    while remaining:
        print(f"\n{kind}: unlabeled version IDs:")
        for version_id in remaining:
            info = metadata[version_id]
            begin = info.get("live_begin") or info.get("begin") or "?"
            end = info.get("live_end") or info.get("end") or "?"
            print(f"  {version_id}: {get_name(info)} | {begin} - {end}")
        answer = input(
            "Patch and count for the earliest IDs (e.g. '3.4 2'), or 'skip': ",
        ).strip()
        if answer.lower() == "skip":
            print(f"Skipping {len(remaining)} unlabeled {kind} ID(s).")
            print("They will be asked again next run.")
            break
        parsed = parse_patch_count(answer)
        if parsed is None:
            print("Invalid input. Use '<major>.<minor> <count>' or 'skip'.")
            continue
        patch, count = parsed
        if count > len(remaining):
            print(f"Count {count} exceeds the {len(remaining)} remaining ID(s).")
            continue
        next_phase = get_next_phase(patch, used_labels)
        assignments: list[tuple[str, str]] = []
        for offset in range(count):
            version_id = remaining[offset]
            label = f"{patch}.{next_phase + offset}"
            mapping[version_id] = label
            used_labels.add(label)
            assignments.append((version_id, label))
        save_version_labels(context.labels)
        saved = ", ".join(
            f"{version_id} -> {label}" for version_id, label in assignments
        )
        print("Saved: " + saved)
        remaining = remaining[count:]


def is_date(value: str) -> bool:
    """Return whether a value is a DD/MM/YYYY date."""
    try:
        datetime.strptime(value, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def parse_time_range(value: str) -> tuple[str, str] | None:
    """Parse a 'DD/MM/YYYY - DD/MM/YYYY' date range."""
    parts = [part.strip() for part in value.split(" - ")]
    if len(parts) != 2:
        return None
    if not all(is_date(part) for part in parts):
        return None
    return parts[0], parts[1]


def resolve_times(
    kind: str,
    label: str,
    metadata: dict[str, dict[str, Any]],
    context: EndgameContext,
    version_id: str,
) -> tuple[str, str] | None:
    """Resolve start and end times from source data, existing output, or input."""
    info = metadata[version_id]
    time_start, time_end = get_times(info)
    if time_start and time_end:
        return time_start, time_end

    existing_versions = context.existing.get(kind, {})
    existing_entry = existing_versions.get(label)
    if existing_entry:
        old_start = existing_entry.get("time_start")
        old_end = existing_entry.get("time_end")
        if old_start and old_end:
            return old_start, old_end

    name = get_name(info)
    if name:
        matches = [
            entry
            for entry in existing_versions.values()
            if entry.get("name") == name
            and entry.get("time_start")
            and entry.get("time_end")
        ]
        if len(matches) == 1:
            entry = matches[0]
            print(f"{kind} {version_id}: using existing times for {name!r}")
            return str(entry["time_start"]), str(entry["time_end"])

    print(f"\n{kind} {version_id} ({name or 'unknown'}) has no begin/end times.")
    while True:
        answer = input(
            "Enter 'DD/MM/YYYY - DD/MM/YYYY', or leave blank to skip: ",
        ).strip()
        if not answer:
            print(f"{kind} {version_id}: skipping missing times")
            return None
        parsed = parse_time_range(answer)
        if parsed is not None:
            return parsed
        print("Invalid date range. Use 'DD/MM/YYYY - DD/MM/YYYY'.")


def build_entry(
    version_id: str,
    label: str,
    metadata: dict[str, dict[str, Any]],
    context: EndgameContext,
    kind: str,
) -> dict[str, str] | None:
    """Build one version entry with a name and date range."""
    info = metadata[version_id]
    name = get_name(info)
    if not name:
        print(f"{kind} {version_id}: missing name; skipping")
        return None
    times = resolve_times(kind, label, metadata, context, version_id)
    if times is None:
        return None
    return {
        "name": name,
        "time_start": times[0],
        "time_end": times[1],
    }


def sort_entries(entries: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """Sort entries by version label."""
    return {
        label: entries[label]
        for label in sorted(entries, key=label_sort_key)
    }


def warn_changes(
    existing: dict[str, dict[str, dict[str, str]]],
    new_entries: dict[str, dict[str, dict[str, str]]],
) -> None:
    """Print label, name, and date changes compared with the previous output."""
    for kind, versions in new_entries.items():
        old_versions = existing.get(kind, {})
        old_labels = set(old_versions)
        new_labels = set(versions)
        for label in sorted(old_labels - new_labels, key=label_sort_key):
            print(
                f"{kind}: removed label {label} "
                f"({old_versions[label].get('name')})",
            )
        for label in sorted(new_labels - old_labels, key=label_sort_key):
            print(f"{kind}: added label {label} ({versions[label].get('name')})")
        for label in sorted(old_labels & new_labels, key=label_sort_key):
            old_entry = old_versions[label]
            new_entry = versions[label]
            for key in ("name", "time_start", "time_end"):
                old_value = old_entry.get(key)
                new_value = new_entry.get(key)
                if old_value != new_value:
                    print(f"{kind} {label} {key}: {old_value} -> {new_value}")


def build_endgame(
    spec: EndgameSpec,
    groups: dict[str, list[Any]] | None,
    metadata: dict[str, dict[str, Any]],
    context: EndgameContext,
) -> dict[str, dict[str, str]]:
    """Build all entries for one endgame type."""
    if groups is None:
        version_labels: dict[str, str] = {}
        ignored_ids: set[str] = set()
    else:
        version_labels, ignored_ids = build_labels_from_groups(
            spec.name,
            groups,
            metadata,
        )

    used_labels = set(version_labels)
    mapping = context.labels.setdefault(spec.name, {})
    grouped_ids = set(version_labels.values())
    relevant_ids = [
        version_id
        for version_id in metadata
        if version_id not in grouped_ids and version_id not in ignored_ids
    ]

    unlabeled_ids: list[str] = []
    for version_id in relevant_ids:
        label = mapping.get(version_id)
        if label is None:
            unlabeled_ids.append(version_id)
            continue
        if not re.fullmatch(r"\d+\.\d+\.\d+", label):
            print(f"{spec.name}: invalid label for {version_id}: {label!r}")
            del mapping[version_id]
            unlabeled_ids.append(version_id)
            continue
        if label in used_labels:
            print(f"{spec.name}: conflicting label for {version_id}: {label}")
            del mapping[version_id]
            unlabeled_ids.append(version_id)
            continue
        used_labels.add(label)

    unlabeled_ids = seed_labels(
        spec.name,
        unlabeled_ids,
        metadata,
        context,
        used_labels,
    )
    if unlabeled_ids:
        prompt_for_labels(
            spec.name,
            unlabeled_ids,
            metadata,
            context,
            used_labels,
        )

    entries: dict[str, dict[str, str]] = {}
    for label, version_id in version_labels.items():
        entry = build_entry(version_id, label, metadata, context, spec.name)
        if entry is not None:
            entries[label] = entry
    for version_id in relevant_ids:
        label = mapping.get(version_id)
        if label is None:
            continue
        entry = build_entry(version_id, label, metadata, context, spec.name)
        if entry is not None:
            entries[label] = entry
    return sort_entries(entries)


def update_endgame_versions(
    live_version: str,
) -> dict[str, dict[str, dict[str, str]]]:
    """Update endgame version data from nanoka."""
    base_url = f"https://static.nanoka.cc/hsr/{live_version}"
    context = EndgameContext(
        existing=load_existing_versions(),
        labels=load_version_labels(),
    )
    save_entries: dict[str, dict[str, dict[str, str]]] = {}
    for spec in SPECS:
        groups: dict[str, list[Any]] | None = None
        if spec.version_path is not None:
            groups = _load_from_url(
                f"{base_url}/{spec.version_path}",
                allow_missing=True,
            )
        metadata: dict[str, dict[str, Any]] = _load_from_url(
            f"{base_url}/{spec.metadata_path}",
        )
        save_entries[spec.name] = build_endgame(spec, groups, metadata, context)
    context.labels = {
        kind: mapping for kind, mapping in context.labels.items() if mapping
    }
    save_version_labels(context.labels)
    warn_changes(context.existing, save_entries)
    return save_entries
