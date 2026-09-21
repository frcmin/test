#!/usr/bin/env python3
"""Bake NexoBrowser chrome/urlbar lockdown into the extracted Firefox tree.

- Never execute javascript: from the address bar
- Hide URL-bar quick actions / command chips
- Remove Ask-an-AI-ChatBot and related GenAI command UI

Run after scripts/patch.py and remove-settings-menu.py (Makefile `dir`).
Idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

JS_GUARD = """    // NexoBrowser: never execute javascript: typed in the address bar.
    if (typeof url === "string" && /^\\s*javascript:/i.test(url)) {
      return;
    }
"""

GENAI_STUB = """    // NexoBrowser: AI/chat command UI is disabled.
    try {
      contextMenu?.showItem?.(menu, false);
    } catch (e) {}
    if (menu) {
      menu.hidden = true;
    }
    return;
"""

ASK_CHAT_CALL = """    lazy.GenAI.buildAskChatMenu(document.getElementById("context-ask-chat"), {
      browser: this.browser,
      selectionInfo: this.selectionInfo,
      showItem: this.showItem.bind(this),
      source: "page",
    });
"""

ASK_CHAT_REPL = """    // NexoBrowser: do not build the Ask-an-AI-ChatBot context menu.
    this.showItem("context-ask-chat", false);
"""


def replace_once(text: str, old: str, new: str) -> tuple[str, bool]:
    if new.strip() in text and old not in text:
        return text, False
    if old not in text:
        return text, False
    return text.replace(old, new, 1), True


def patch_urlbar_load(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    if "NexoBrowser: never execute javascript:" in original:
        return False
    needle = """  _loadURL(
    url,
    event,
    openUILinkWhere,
    params,
    resultDetails = null,
    browser = this.window.gBrowser.selectedBrowser
  ) {
"""
    if needle not in original:
        # SmartbarInput uses a slightly different default browser arg.
        needle = """  _loadURL(
    url,
    event,
    openUILinkWhere,
    params,
    resultDetails = null,
    browser = this.window.gBrowser.selectedBrowser
  ) {
"""
    if needle not in original:
        # Try a looser match: first `_loadURL(` function body.
        idx = original.find("  _loadURL(")
        if idx < 0:
            print(f"skip (no _loadURL): {path}")
            return False
        brace = original.find("{", idx)
        if brace < 0:
            return False
        updated = original[: brace + 1] + "\n" + JS_GUARD + original[brace + 1 :]
        path.write_text(updated, encoding="utf-8")
        return True
    updated = original.replace(needle, needle + JS_GUARD, 1)
    path.write_text(updated, encoding="utf-8")
    return True


def patch_urlbar_filter(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    old = """    if (
      result.type != lazy.UrlbarUtils.RESULT_TYPE.KEYWORD &&
      result.payload.url &&
      result.payload.url.startsWith("javascript:") &&
      !this.context.searchString.startsWith("javascript:") &&
      lazy.UrlbarPrefs.get("filter.javascript")
    ) {
      return;
    }"""
    new = """    if (
      result.payload.url &&
      /^\\s*javascript:/i.test(result.payload.url)
    ) {
      // NexoBrowser: drop all javascript: urlbar results, including typed.
      return;
    }"""
    updated, changed = replace_once(original, old, new)
    if changed:
        path.write_text(updated, encoding="utf-8")
    return changed


def patch_genai(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    changed = False
    if "NexoBrowser: AI/chat command UI is disabled" not in original:
        old = """  async buildAskChatMenu(menu, contextMenu) {
    const {"""
        new = """  async buildAskChatMenu(menu, contextMenu) {
""" + GENAI_STUB + """    const {"""
        original, ok = replace_once(original, old, new)
        changed = changed or ok
    old_ep = """  get canShowChatEntrypoint() {
    return (
      lazy.chatEnabled &&
      lazy.chatProvider != "" &&
      // Chatbot needs to be a tool if new sidebar
      (!lazy.sidebarRevamp || lazy.sidebarTools.includes("aichat"))
    );
  }"""
    new_ep = """  get canShowChatEntrypoint() {
    // NexoBrowser: AI chat entry points are disabled.
    return false;
  }"""
    original, ok = replace_once(original, old_ep, new_ep)
    changed = changed or ok
    if changed:
        path.write_text(original, encoding="utf-8")
    return changed


def patch_nscontext(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    updated, changed = replace_once(original, ASK_CHAT_CALL, ASK_CHAT_REPL)
    if changed:
        path.write_text(updated, encoding="utf-8")
    return changed


def patch_context_xhtml(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    old = '<menu id="context-ask-chat"/>'
    new = '<menu id="context-ask-chat" hidden="true"/>'
    updated, changed = replace_once(original, old, new)
    if changed:
        path.write_text(updated, encoding="utf-8")
    return changed


def patch_browser_sets(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    if 'id="viewGenaiChatSidebarKb"' not in original:
        return False
    if "NexoBrowser: AI chatbot shortcut removed" in original:
        return False
    # Disable the key by commenting it out via wrapping in a never-true ifdef-style
    # XML comment is enough — XUL ignores commented keys.
    start = original.find('<key id="viewGenaiChatSidebarKb"')
    if start < 0:
        return False
    end = original.find("/>", start)
    if end < 0:
        return False
    end += 2
    block = original[start:end]
    updated = (
        original[:start]
        + "<!-- NexoBrowser: AI chatbot shortcut removed\n    "
        + block
        + "\n    -->"
        + original[end:]
    )
    path.write_text(updated, encoding="utf-8")
    return True


def patch_popupset(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    changed = False
    for pid in ("selection-shortcut-action-panel", "chat-shortcuts-options-panel"):
        old = f'id="{pid}"'
        new = f'id="{pid}" hidden="true"'
        if f'id="{pid}" hidden="true"' in original:
            continue
        if old in original:
            original = original.replace(old, new, 1)
            changed = True
    if changed:
        path.write_text(original, encoding="utf-8")
    return changed


def rebrand_text(path: Path) -> bool:
    """Replace user-visible Camoufox strings with NexoBrowser."""
    original = path.read_text(encoding="utf-8", errors="replace")
    updated = original.replace("Camoufox", "NexoBrowser")
    updated = updated.replace("https://github.com/daijro/camoufox", "about:blank")
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: apply-nexo-lockdown.py <firefox-source-dir>", file=sys.stderr)
        return 2
    src = Path(sys.argv[1]).resolve()
    if not src.is_dir():
        print(f"error: source dir not found: {src}", file=sys.stderr)
        return 1

    targets = [
        (src / "browser/components/urlbar/content/UrlbarInput.mjs", patch_urlbar_load),
        (src / "browser/components/urlbar/content/SmartbarInput.mjs", patch_urlbar_load),
        (src / "browser/components/urlbar/UrlbarProvidersManager.sys.mjs", patch_urlbar_filter),
        (src / "browser/components/genai/GenAI.sys.mjs", patch_genai),
        (src / "browser/base/content/nsContextMenu.sys.mjs", patch_nscontext),
        (src / "browser/base/content/browser-context.inc.xhtml", patch_context_xhtml),
        (src / "browser/base/content/browser-sets.inc.xhtml", patch_browser_sets),
        (src / "browser/base/content/main-popupset.inc.xhtml", patch_popupset),
    ]

    changed: list[str] = []
    for path, fn in targets:
        if not path.is_file():
            print(f"missing: {path.relative_to(src)}")
            continue
        if fn(path):
            rel = str(path.relative_to(src))
            changed.append(rel)
            print(f"updated: {rel}")

    marker = src / "_NEXOBROWSER_LOCKDOWN"
    marker.write_text("\n".join(changed) + "\n", encoding="utf-8")
    print(f"\nNexoBrowser lockdown: {len(changed)} file(s) changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
