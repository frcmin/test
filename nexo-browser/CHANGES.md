# NexoBrowser (Camoufox-based)

Windows x86_64 portable build branded **NexoBrowser**, with Settings/Preferences
chrome entry points removed. Product work is applied on top of upstream
[Camoufox](https://github.com/daijro/camoufox) cloned at `upstream-camoufox/`.

The Firefox source tree and the Windows zip are **not** committed. The zip is
published as a Cursor agent artifact.

Upstream Camoufox commit used for this work: `52d6746a4a67830ec8a24e2196822204ba843134` (shallow clone of `main`).

## Overlay files (branding + packaging)

Copied onto the Camoufox clone by `nexo-browser/apply.sh`:

| File | Change |
|---|---|
| `additions/browser/branding/camoufox/configure.sh` | `MOZ_APP_*` renamed to NexoBrowser / nexobrowser |
| `additions/browser/branding/camoufox/locales/en-US/brand.ftl` | Window title / About Fluent strings |
| `additions/browser/branding/camoufox/locales/en-US/brand.dtd` | DTD brand entities |
| `additions/browser/branding/camoufox/locales/en-US/brand.properties` | Properties brand strings |
| `additions/browser/branding/camoufox/branding.nsi` | Windows NSIS display names |
| `patches/librewolf/disable-data-reporting-at-compile-time.patch` | `MOZ_APP_VENDOR` / `MOZ_APP_PROFILE` |
| `assets/base.mozconfig` | `--with-app-name=nexobrowser`, `-j2` make flags |
| `scripts/package.py` | Zip named `NexoBrowser-*-win.x86_64.zip`, exe `NexoBrowser.exe` |
| `scripts/patch.py` | Find `rustup` on PATH when `~/.cargo/bin/rustup` is missing |
| `multibuild.py` | Asset glob matches the NexoBrowser zip name |

## Settings / Preferences chrome removal

| File | Change |
|---|---|
| `settings/chrome.css` | Hide menu-bar, hamburger, and app-menu Settings items |
| `scripts/remove-settings-menu.py` | Post-patch edit of Firefox chrome (XUL/JS ids and `openPreferences` handlers) |
| `Makefile` `dir` target | Runs the settings-removal script after Camoufox patches |

`remove-settings-menu.py` writes `_NEXOBROWSER_SETTINGS_REMOVED` in the Firefox
tree listing every file it actually modified. Against Firefox 152.0.4 those
files were:

- `browser/base/content/browser-menubar.inc.xhtml` (menu bar Settings items)
- `browser/base/content/appmenu-viewcache.inc.xhtml` (`appMenu-settings-button`)
- `browser/base/content/browser-sets.inc.xhtml` (`key_preferencesCmdMac`)
- `browser/components/customizableui/content/panelUI.js` (hamburger click handler)

The resulting unified diff is `nexo-browser/patches/remove-settings-menu.patch`.

## Build (Windows x86_64, compiled from source)

```bash
bash nexo-browser/apply.sh
bash nexo-browser/build-windows-x86_64.sh
```

Uses Camoufox's Linux cross-compile path (`make dir` → `make bootstrap` →
`python3 multibuild.py --target windows --arch x86_64`). Docker is preferred
when available; otherwise the native Makefile path is used.

Do not substitute a GitHub Release binary.
