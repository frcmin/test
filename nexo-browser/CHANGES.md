# NexoBrowser (Camoufox-based)

Windows x86_64 portable build branded **NexoBrowser**, with the hamburger /
app-menu button removed from chrome. Product work is applied on top of
upstream [Camoufox](https://github.com/daijro/camoufox) cloned at
`upstream-camoufox/`.

**Pinned Camoufox tag:** `v152.0.4-beta.30`
(`5d06ec1629ac7843508f1e683f83e404fde8db76`).

The Firefox source tree and the Windows zip are **not** committed. The zip is
published as a Cursor agent artifact.

Do not substitute a GitHub Release binary.

## Overlay files (branding + packaging)

Copied onto the Camoufox clone by `nexo-browser/apply.sh`:

| File | Change |
|---|---|
| `additions/browser/branding/camoufox/configure.sh` | `MOZ_APP_*` renamed to NexoBrowser / nexobrowser |
| `additions/browser/branding/camoufox/locales/en-US/brand.ftl` | Window title / About Fluent strings |
| `additions/browser/branding/camoufox/locales/en-US/brand.dtd` | DTD brand entities |
| `additions/browser/branding/camoufox/locales/en-US/brand.properties` | Properties brand strings |
| `additions/browser/branding/camoufox/branding.nsi` | Windows NSIS display names (no camoufox URLs) |
| `additions/browser/base/content/aboutDialog.xhtml` | About wordmark/text show NexoBrowser |
| `additions/browser/locales/en-US/chrome/overrides/appstrings.properties` | Error strings say NexoBrowser |
| `additions/browser/app/firefox.exe.manifest` | Windows assembly name/description NexoBrowser |
| `patches/librewolf/disable-data-reporting-at-compile-time.patch` | `MOZ_APP_VENDOR` / `MOZ_APP_PROFILE` |
| `assets/base.mozconfig` | `--with-app-name=nexobrowser`, `--disable-accessibility`, ccache off; `-j12` compile / 1 link job on 16c/32G-class, else `-j$(nproc)` |
| `scripts/package.py` | Zip named `NexoBrowser-*-win.x86_64.zip`, exe `NexoBrowser.exe` |
| `scripts/patch.py` | Find `rustup` on PATH; skip tree reset on `--mozconfig-only` |
| `multibuild.py` | Asset glob matches the NexoBrowser zip name |

## Settings / hamburger chrome removal

| File | Change |
|---|---|
| `settings/chrome.css` | Hide the entire hamburger (`#PanelUI-button`, `#PanelUI-menu-button`, `#appMenu-popup`) and Settings items |
| `scripts/remove-settings-menu.py` | Post-patch edit of Firefox chrome (XUL/JS ids and `openPreferences` handlers) |
| `Makefile` `dir` target | Runs the settings-removal script after Camoufox patches |

`remove-settings-menu.py` writes `_NEXOBROWSER_SETTINGS_REMOVED` in the Firefox
tree listing every file it actually modified.

## Address-bar / GenAI lockdown

| File | Change |
|---|---|
| `scripts/apply-nexo-lockdown.py` | Block `javascript:` in UrlbarInput/SmartbarInput; drop javascript: urlbar results; hide Ask-an-AI-ChatBot (`context-ask-chat`); stub GenAI chat entry points |
| `settings/chrome.css` | Hide chatbot context menu, GenAI shortcut panels, URL-bar quick-action / command chips |
| `settings/nexo-lockdown.cfg` | `lockPref` for `browser.urlbar.filter.javascript`, quickactions/scotchBonnet/secondaryActions, and `browser.ml.chat.*` |
| `settings/distribution/policies.json` | WebsiteFilter also blocks `javascript:*` |

`apply.sh` appends `nexo-lockdown.cfg` onto `settings/camoufox.cfg` once.

## Sci-fi app icon

Source mark: `nexo-browser/icons/nexobrowser_icon_1024.png` (cyan/magenta HUD
hexagon with an N). Rasterized by `scripts/generate-nexo-icons.py` into
Camoufox branding slots (`firefox.ico`, `default*.png`, VisualElements, about
logos, MSIX/macOS assets).

## clang-cl Unix-path wrapper

Linux-hosted `clang-cl` treats arguments that start with `/` as options, so
`/workspace/.../foo.c` is dropped (`clang-cl: error: no input files`).
`scripts/clang-cl-unix-wrapper.sh` rewrites those sources to cwd-relative
paths. `scripts/install-clang-cl-wrapper.sh` installs it over
`~/.mozbuild/clang/bin/clang-cl` and is invoked from `make build`.

## Build (Windows x86_64, compiled from source)

```bash
bash nexo-browser/apply.sh
bash nexo-browser/build-windows-x86_64.sh
```

Uses Camoufox's Linux cross-compile path (`make dir` → `make bootstrap` →
`python3 multibuild.py --target windows --arch x86_64`).
