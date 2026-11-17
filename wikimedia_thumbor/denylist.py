# Copyright (c) 2026 Wikimedia Foundation
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

import os
from fnmatch import fnmatchcase

import yaml
from thumbor.utils import logger

PATH = os.environ.get("DENY_RULES_PATH", "/etc/thumbor/deny-rules.yaml")


def parse_rule(rule):
    """Normalise one rule, raising on anything unexpected."""
    # A misspelled min_bytes would otherwise deny every match
    if rule.keys() - {"glob", "min_bytes", "reason"}:
        raise ValueError(f"unknown keys in {rule!r}")
    return {"glob": rule["glob"].lower(), "min_bytes": int(rule.get("min_bytes", 0)), "reason": rule.get("reason")}


def load_denylist(path):
    """Read the rules from path; a missing or invalid file denies nothing."""
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            return [parse_rule(rule) for rule in yaml.safe_load(f)["rules"]]
    except Exception as e:
        logger.error(f"[Denylist] Ignoring invalid denylist {path}: {e!r}")
        return []


def deny_reason(rules, path, size=None):
    """Return why thumbnails of the original at path are denied, or None.

    Rules with min_bytes only match once size is known."""
    for rule in rules:
        if rule["min_bytes"] and (size is None or size < rule["min_bytes"]):
            continue
        if fnmatchcase(path.lower(), rule["glob"]):
            return rule["reason"] or f"Thumbnailing {path} is disabled"
    return None
