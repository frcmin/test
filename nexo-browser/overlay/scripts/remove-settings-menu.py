#!/usr/bin/env python3
"""Remove chrome entry points that open Settings/Preferences.

Edits the extracted Firefox tree so the menu bar, hamburger/app menu, and
related command/key bindings no longer open about:preferences.

Designed to be run after `scripts/patch.py` (see Makefile `dir`).
Prints every file it changes so the set can be documented.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Element ids Firefox uses for Settings/Preferences chrome.
TARGET_IDS = (
    "menu_preferences",
    "menu_settings",
    "menu_openPreferences",
    "openPreferences",
    "appMenu-settings-button",
    "appMenu-preferences-button",
    "key_openPreferences",
    "key_preferencesCmdMac",
    "cmd_Preferences",
    "cmd_preferences",
    "PanelUI-menu-button",
    "PanelUI-button",
)

ID_ATTR = re.compile(
    r'\bid\s*=\s*["\'](' + "|".join(re.escape(i) for i in TARGET_IDS) + r')["\']',
    re.IGNORECASE,
)

# Make an existing element hidden if it is not already.
HIDDEN_INJECT = re.compile(
    r'(<(?:menuitem|toolbarbutton|key|command|menu)\b[^>]*?\bid\s*=\s*["\'](?:'
    + "|".join(re.escape(i) for i in TARGET_IDS)
    + r')["\'][^>]*?)(/?>)',
    re.IGNORECASE | re.DOTALL,
)

OPEN_PREFS_ONCOMMAND = re.compile(
    r'''(<(?:menuitem|toolbarbutton|command)\b[^>]*?\boncommand\s*=\s*["'][^"']*openPreferences[^"']*["'][^>]*?)(/?>)''',
    re.IGNORECASE | re.DOTALL,
)

PANELUI_CASE = re.compile(
    r'(case\s+["\']appMenu-settings-button["\']\s*:\s*)(.*?)(break\s*;)',
    re.DOTALL,
)

L10N_ITEMS = re.compile(
    r'(<(?:menuitem|toolbarbutton)\b[^>]*?data-l10n-id\s*=\s*["\']'
    r'(?:menu-settings|menu-tools-settings|menu-application-preferences|'
    r'menu-application-settings|appmenuitem-settings|appmenuitem-preferences)'
    r'["\'][^>]*?)(/?>)',
    re.IGNORECASE | re.DOTALL,
)


def inject_hidden(match: re.Match) -> str:
    head, tail = match.group(1), match.group(2)
    if re.search(r'\bhidden\s*=', head, re.IGNORECASE):
        head = re.sub(r'\bhidden\s*=\s*["\'][^"\']*["\']', 'hidden="true"', head, flags=re.IGNORECASE)
    else:
        head = head + ' hidden="true"'
    return head + tail


def neutralize_panelui(text: str) -> str:
    def repl(match: re.Match) -> str:
        return match.group(1) + "\n        // NexoBrowser: Settings chrome entry removed\n        " + match.group(3)

    return PANELUI_CASE.sub(repl, text, count=1)


def patch_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    updated = original

    if path.suffix == ".js" or path.name.endswith(".sys.mjs"):
        if "appMenu-settings-button" in updated and "openPreferences" in updated:
            updated = neutralize_panelui(updated)
        # Neutralize command handlers that only open preferences.
        updated = re.sub(
            r'(["\']appMenu-settings-button["\']\s*[:=][^\n]*openPreferences[^\n]*)',
            r'/* NexoBrowser removed settings handler */',
            updated,
        )
    else:
        updated = HIDDEN_INJECT.sub(inject_hidden, updated)
        updated = OPEN_PREFS_ONCOMMAND.sub(inject_hidden, updated)
        updated = L10N_ITEMS.sub(inject_hidden, updated)

    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def candidate_files(src_dir: Path) -> list[Path]:
    roots = [
        src_dir / "browser" / "base" / "content",
        src_dir / "browser" / "components" / "customizableui",
        src_dir / "browser" / "locales",
    ]
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".inc", ".xhtml", ".js", ".mjs", ".xml", ".html"}:
                if not path.name.endswith(".inc.xhtml"):
                    continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if ID_ATTR.search(text) or "openPreferences" in text or "appMenu-settings-button" in text:
                files.append(path)
    return files


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: remove-settings-menu.py <firefox-source-dir>", file=sys.stderr)
        return 2
    src_dir = Path(sys.argv[1]).resolve()
    if not src_dir.is_dir():
        print(f"error: source dir not found: {src_dir}", file=sys.stderr)
        return 1

    changed: list[str] = []
    for path in candidate_files(src_dir):
        if patch_file(path):
            rel = path.relative_to(src_dir)
            changed.append(str(rel))
            print(f"updated: {rel}")

    marker = src_dir / "_NEXOBROWSER_SETTINGS_REMOVED"
    marker.write_text("\n".join(changed) + "\n", encoding="utf-8")
    print(f"\nNexoBrowser settings-menu removal: {len(changed)} file(s) changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
