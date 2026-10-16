"""Default panel geometry and persistence for the desktop workspace."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Mapping, Optional, Tuple

PanelGeometry = Tuple[int, int, int, int]

PANEL_SPECS = {
    "system": {"title": "SYSTEM // BTOP", "min_width": 250, "min_height": 170},
    "matrix": {"title": "MATRIX // STREAM", "min_width": 240, "min_height": 180},
    "pipes": {"title": "PIPES // ACTIVITY", "min_width": 220, "min_height": 170},
    "events": {"title": "EVENT LOG // ANONYMOUS", "min_width": 280, "min_height": 180},
    "assistant": {"title": "COMMAND CENTER", "min_width": 320, "min_height": 200},
    "findings": {"title": "FINDINGS // RECENT", "min_width": 260, "min_height": 160},
}

DEFAULT_LAYOUT: Dict[str, PanelGeometry] = {
    "system": (14, 14, 350, 230),
    "matrix": (382, 14, 500, 280),
    "pipes": (900, 14, 300, 220),
    "events": (14, 265, 420, 290),
    "assistant": (452, 315, 500, 280),
    "findings": (975, 250, 340, 300),
}

MIN_PANEL_WIDTH = 180
MIN_PANEL_HEIGHT = 120


def move_panel(
    layout: Mapping[str, PanelGeometry], panel_id: str, x: int, y: int
) -> Dict[str, PanelGeometry]:
    """Return a copy of the layout with one panel moved to the requested position."""
    if panel_id not in PANEL_SPECS:
        raise KeyError(f"Unknown panel: {panel_id}")
    current = layout[panel_id]
    updated = dict(layout)
    updated[panel_id] = (max(0, int(x)), max(0, int(y)), current[2], current[3])
    return updated


def resize_panel(
    layout: Mapping[str, PanelGeometry], panel_id: str, width: int, height: int
) -> Dict[str, PanelGeometry]:
    """Return a copy of the layout with one panel resized."""
    if panel_id not in PANEL_SPECS:
        raise KeyError(f"Unknown panel: {panel_id}")
    minimum_width = max(MIN_PANEL_WIDTH, PANEL_SPECS[panel_id]["min_width"])
    minimum_height = max(MIN_PANEL_HEIGHT, PANEL_SPECS[panel_id]["min_height"])
    if width < minimum_width or height < minimum_height:
        raise ValueError(
            f"{panel_id} must be at least {minimum_width}x{minimum_height} pixels"
        )
    current = layout[panel_id]
    updated = dict(layout)
    updated[panel_id] = (current[0], current[1], int(width), int(height))
    return updated


def load_layout(path: Path) -> Dict[str, PanelGeometry]:
    """Load stored panel positions, retaining defaults for new or absent panels."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return dict(DEFAULT_LAYOUT)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read desktop layout from {path}: {exc}") from exc

    raw_panels = data.get("panels", data) if isinstance(data, dict) else {}
    restored = dict(DEFAULT_LAYOUT)
    if not isinstance(raw_panels, dict):
        raise ValueError(f"Invalid panel layout in {path}")
    for panel_id, values in raw_panels.items():
        if panel_id not in PANEL_SPECS:
            continue
        if not isinstance(values, (list, tuple)) or len(values) != 4:
            raise ValueError(f"Invalid geometry for panel {panel_id}")
        x, y, width, height = (int(value) for value in values)
        if width < MIN_PANEL_WIDTH or height < MIN_PANEL_HEIGHT:
            raise ValueError(f"Invalid dimensions for panel {panel_id}")
        restored[panel_id] = (max(0, x), max(0, y), width, height)
    return restored


def load_visible_panels(path: Path) -> set[str]:
    """Load visible panel IDs, defaulting to every dashboard panel."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return set(PANEL_SPECS)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read desktop visibility from {path}: {exc}") from exc
    if not isinstance(data, dict) or "visible" not in data:
        return set(PANEL_SPECS)
    visible = data["visible"]
    if not isinstance(visible, list) or not all(isinstance(name, str) for name in visible):
        raise ValueError(f"Invalid visible panel list in {path}")
    return set(visible).intersection(PANEL_SPECS)


def save_layout(path: Path, layout: Mapping[str, PanelGeometry], visible: Optional[set[str]] = None) -> None:
    """Persist panel geometry and optionally the user's visible-panel selection."""
    payload = {
        "panels": {name: list(layout[name]) for name in PANEL_SPECS if name in layout},
        "visible": sorted(visible if visible is not None else PANEL_SPECS),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
