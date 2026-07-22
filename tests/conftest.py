"""Repository-wide classification for the reproducible legacy baseline."""

import json
from pathlib import Path

import pytest


MANIFEST_PATH = Path(__file__).with_name("legacy_baseline_manifest.json")


def _load_manifest():
    with MANIFEST_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _selector_matches(nodeid, selector):
    return (
        nodeid == selector
        or nodeid.startswith(f"{selector}::")
        or nodeid.startswith(f"{selector}[")
    )


def pytest_collection_modifyitems(config, items):
    manifest = _load_manifest()
    slow_selectors = manifest["slow_selectors"]
    quarantines = {entry["nodeid"]: entry for entry in manifest["quarantines"]}

    for item in items:
        if any(_selector_matches(item.nodeid, value) for value in slow_selectors):
            item.add_marker(pytest.mark.slow)

        quarantine = quarantines.get(item.nodeid)
        if quarantine is not None:
            item.add_marker(pytest.mark.legacy_quarantine)
            outcome = quarantine.get("outcome", "xfail")
            if outcome == "xfail":
                item.add_marker(
                    pytest.mark.xfail(reason=quarantine["reason"], strict=True)
                )
            elif outcome == "skip":
                item.add_marker(pytest.mark.skip(reason=quarantine["reason"]))
            else:
                raise pytest.UsageError(
                    f"Unknown legacy quarantine outcome {outcome!r} "
                    f"for {item.nodeid}"
                )

    # Focused test invocations intentionally collect only part of the manifest.
    if config.args != ["tests"]:
        return

    collected = {item.nodeid for item in items}
    unmatched_slow = [
        selector
        for selector in slow_selectors
        if not any(_selector_matches(nodeid, selector) for nodeid in collected)
    ]
    unmatched_quarantines = [
        nodeid for nodeid in quarantines if nodeid not in collected
    ]
    if unmatched_slow or unmatched_quarantines:
        details = [
            *(f"unmatched slow selector: {value}" for value in unmatched_slow),
            *(f"unmatched quarantine: {value}" for value in unmatched_quarantines),
        ]
        raise pytest.UsageError("Legacy baseline manifest drift:\n" + "\n".join(details))
