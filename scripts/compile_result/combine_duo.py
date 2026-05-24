"""Combine duo usage files, matching partners by name."""

import json
from sys import path as sys_path

from send2trash import send2trash

sys_path.append("../")
from comp_rates_config import BASE_RESULT_PATH


def combine_duo_files(base_file: str, e1_file: str, output_file: str) -> None:
    """Combine duo usage files, matching partners by name."""
    with open(base_file, encoding="utf-8") as f:
        base_data = json.load(f)
    with open(e1_file, encoding="utf-8") as f:
        e1_data = json.load(f)

    # Map main character to its object for quick lookup
    base_map = {item["char"]: item for item in base_data}
    e1_map = {item["char"]: item for item in e1_data}

    combined: list[dict[str, str]] = []

    # Process each character from the base file (assume it covers all needed)
    for char, base_obj in base_map.items():
        e1_obj = e1_map.get(char, {})

        # Helper to extract partner data from an object.
        def extract_partners(
            obj: dict[str, str],
        ) -> dict[str, dict[str, str | float | int]]:
            partners: dict[str, dict[str, str | float | int]] = {}
            # Find all keys like "char_X"
            for key, partner_name in obj.items():
                if key.startswith("char_"):
                    idx = int(key[5:])
                    # Corresponding metrics
                    partners[partner_name] = {
                        "app_rate": obj[f"app_rate_{idx}"],
                        "avg_round": obj[f"avg_round_{idx}"],
                        "app_flat": obj[f"app_flat_{idx}"],
                        "idx": idx,  # store original index for ordering
                    }
            return partners

        base_partners = extract_partners(base_obj)
        e1_partners = extract_partners(e1_obj)

        # Build ordered list of partner names:
        # First all partners from base in the order they appear (by increasing index)
        ordered_names: list[str] = []
        seen: set[str] = set()
        # Sort by original index to preserve base order
        base_items = sorted(base_partners.items(), key=lambda x: x[1]["idx"])
        for name, _ in base_items:
            ordered_names.append(name)
            seen.add(name)
        # Then add any partners from e1 that are not already seen
        for name in e1_partners:
            if name not in seen:
                ordered_names.append(name)
                seen.add(name)

        if len(ordered_names) < 30:
            ordered_names.extend(["-"] * (30 - len(ordered_names)))

        new_obj = {"char": char, "app": base_obj.get("app", 0)}

        for i, partner_name in enumerate(ordered_names, start=1):
            # Base metrics (may be missing if partner only in e1)
            base_metrics = base_partners.get(partner_name, {})
            app_rate = base_metrics.get("app_rate", "0.00%")
            avg_round = base_metrics.get("avg_round", 99.99)
            app_flat = base_metrics.get("app_flat", 0)

            # e1 metrics (may be missing)
            e1_metrics = e1_partners.get(partner_name, {})
            e1_app_rate = e1_metrics.get("app_rate", "0.00%")
            e1_avg_round = e1_metrics.get("avg_round", 99.99)
            e1_app_flat = e1_metrics.get("app_flat", 0)

            new_obj[f"char_{i}"] = partner_name
            new_obj[f"app_rate_{i}"] = app_rate
            new_obj[f"avg_round_{i}"] = avg_round
            new_obj[f"app_flat_{i}"] = app_flat
            new_obj[f"app_rate_e1_{i}"] = e1_app_rate
            new_obj[f"avg_round_e1_{i}"] = e1_avg_round
            new_obj[f"app_flat_e1_{i}"] = e1_app_flat

        combined.append(new_obj)

    # Delete input files
    send2trash(base_file)
    send2trash(e1_file)

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    combine_duo_files(
        f"../../{BASE_RESULT_PATH}/duos/duo_usages.json",
        f"../../{BASE_RESULT_PATH}/duos/duo_usages_C1.json",
        f"../../{BASE_RESULT_PATH}/duos/duo_combine.json",
    )
