# Releasing Your App

When the app is ready for its users, `tesserae build` makes it one
executable file. The people you give it to run it like any other program:
they don't install Python, Tesserae or anything else.

```bash
pip install "tesserae-ui[build]"
cd notes
tesserae build --check
```

That makes `dist/notes` (`dist/notes.exe` on Windows). `--check` then runs
it briefly from an empty folder and says whether it drew frames and exited
cleanly:

```text
built /home/you/notes/dist/notes
checked: it drew 30 frames and exited cleanly
```

The `build` extra adds [PyInstaller](https://pyinstaller.org), which does
the building. It's kept out of the everyday `pip install tesserae-ui`, so
an app that's never released doesn't carry it; without it, `tesserae
build` tells you what to install.

## One platform at a time

An executable runs on the kind of computer it was built on: build on
Windows for Windows users, on a Mac for Mac users, on Linux for Linux
users. There's no cross-building. Tesserae's supported platforms are
Linux x86-64, macOS on Apple silicon and Windows x64.

If you don't have all three, a CI service can build on each. Tesserae's
own CI does this for a generated app on every push; the same steps in
GitHub Actions, for your app's repository:

```yaml
jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      # Linux runners have no display: a virtual one, software Vulkan, and
      # the keyboard library winit loads for a window (desktops have these).
      - if: runner.os == 'Linux'
        run: sudo apt-get update && sudo apt-get install -y xvfb mesa-vulkan-drivers libxkbcommon-x11-0
      - run: pip install "tesserae-ui[build]"
      - shell: bash
        run: |
          if [ "$RUNNER_OS" = "Linux" ]; then RUN="xvfb-run -a"; else RUN=""; fi
          $RUN tesserae build --check
      - uses: actions/upload-artifact@v4
        with:
          name: app-${{ matrix.os }}
          path: dist/
```

## What goes in

Everything under the app's folder (the folder `app.py` is in), at the
same place relative to it: view and style files, images, fonts, the
ViewModels. The app's folder is scanned, rather than only what the app
opens at start-up, because an app opens files later too: a screen the
user navigates to, an app shell's panels, an image picked at run time.

Left out, wherever they are:

- `.git` and other hidden files and folders (a name starting with `.`),
- virtual environments (any folder with a `pyvenv.cfg`), and folders
  named `venv` or `env`,
- `build`, `dist`, `__pycache__` and `node_modules`,
- `*.pyc` and `*.spec` files.

Two options adjust that, each taking a glob on the path relative to the
app's folder, `/`-separated, and repeatable:

```bash
tesserae build --include .settings.yaml --exclude "notes/*.md" --exclude drafts
```

A folder that matches is taken, or left out, whole.

The app's own `.py` files also go through PyInstaller's import analysis,
so the libraries they import come along. A library that's only imported
in some unusual way (by a string name, say) may need PyInstaller's own
`--hidden-import`; `tesserae build` covers the usual case.

## Finding files in a built app

A `tesserae new` app finds its files next to `app.py`:

```python
HERE = Path(__file__).parent
app.load(HERE / "Home_View.yaml", HomeViewModel)
```

Keep doing that. In a built app, `__file__` is inside the folder the
executable unpacks itself into, where every bundled file is, so these
paths work wherever it's run from. A path relative to the *current*
folder (`Path("Home_View.yaml")`) works when you run `python app.py`
from the app's folder, and fails in a built app run from anywhere else;
`--check` runs from an empty folder to catch exactly that.

That unpacked folder is temporary: it's made fresh on each start and
removed when the app exits. So **don't write files next to `app.py`** —
settings, documents, a database. Save them in the user's own folders
instead (`Path.home()`, or a per-platform app-data folder, which the
[`platformdirs`](https://pypi.org/project/platformdirs/) library finds).

## Options

| Option | What it does |
|---|---|
| `app.py` (positional) | The app's entry point; defaults to `app.py` here. |
| `--name NAME` | The executable's name; defaults to the app's folder name. |
| `--icon FILE` | The app's icon. A PNG (square, 1024 px or more is best) works everywhere: it's made into an `.ico` on Windows and an `.icns` on macOS. An `.ico` or `.icns` is used as it is. |
| `--console` | Keeps a console window on Windows, to see the app's log while debugging. Without it there's none. |
| `--include GLOB` | Bundles files the scan leaves out. |
| `--exclude GLOB` | Leaves more files out. |
| `--check` | Runs the result for 30 frames from an empty folder. |
| `--installer` | Makes this platform's installer instead of a single file (see below). |
| `--app-version 1.2.0` | The installer's version: numbers and dots. Without it the build uses a placeholder starting at zero. |
| `--identifier ID` | Reverse-DNS, like `com.yourcompany.notes`. macOS keeps the app's settings under it. Defaults to a `com.example` placeholder, which the build points out. |
| `--publisher NAME` | Who makes the app; shown as its copyright on macOS. |
| `--description TEXT` | A line about the app. |

PyInstaller's working files go in a temporary folder, so the app's
folder gains only `dist/`.

## Installers

`--installer` makes what users of each platform expect to install,
instead of a single file:

```bash
tesserae build --installer --check --app-version 1.2.0 --identifier com.yourcompany.notes --icon icon.png
```

It builds the app as one folder rather than one file, so the installed
app doesn't unpack itself each time it starts (0.27 s against 0.55 s, on
Linux, for a `tesserae new` app).

- **macOS:** `dist/notes.app` and `dist/notes-1.2.0.dmg`. The `.dmg` opens
  to the app beside a link to Applications, to drag it onto. The version,
  identifier and publisher are in the app's `Info.plist`, and it's signed
  ad hoc (Apple silicon runs nothing unsigned) -- not with a Developer ID,
  so Gatekeeper still asks the first time; see [Signing](#signing).
- **Windows:** `dist/notes-1.2.0-setup.exe`, made with
  [Inno Setup](https://jrsoftware.org/isinfo.php), and the app's folder
  in `dist/notes`. The installer needs no admin rights: it installs for
  the user into `AppData\Local\Programs` (an admin can choose everyone
  instead), adds a Start-menu entry and optionally a desktop one, and
  registers an uninstaller. A new version with the same `--identifier`
  replaces the old one. Run silently, it takes Inno Setup's usual
  `/VERYSILENT /CURRENTUSER`.

  Tesserae uses the Inno Setup it finds (the PATH, or where Inno Setup 6
  or 7 installs; `TESSERAE_ISCC` names one exactly). If there's none, it
  fetches Inno Setup 7.1.0 (14 MB, from its GitHub releases, checked
  against the release's SHA-256), once, into a cache
  (`AppData\Local\tesserae\tools`), and unpacks it there in Inno
  Setup's portable mode, which installs nothing. Inno Setup is free for
  any use; its authors ask companies using it commercially to consider
  [buying a licence](https://jrsoftware.org/isorder.php).
- **Linux:** up to five at once, and the app's folder in `dist/notes-1.2.0`:
    - `notes-1.2.0-x86_64.AppImage` runs on most distributions with no
      install step: download, make executable, run.
    - `notes_1.2.0_amd64.deb` installs on Debian, Ubuntu and their kin
      (`sudo apt install ./notes_1.2.0_amd64.deb`).
    - `notes-1.2.0-1-x86_64.pkg.tar.xz` installs on Arch Linux and its kin
      (`sudo pacman -U ...`).
    - `notes-1.2.0-1.x86_64.rpm` installs on Fedora, openSUSE and their kin
      (`sudo dnf install ./notes-1.2.0-1.x86_64.rpm`), when `rpmbuild` is
      installed where you build (`rpm-build` on Fedora, `rpm` on Ubuntu).
    - `notes-1.2.0-x86_64.flatpak` installs on any distribution with
      Flatpak (`flatpak install --user notes-1.2.0-x86_64.flatpak`), which
      fetches the Freedesktop 26.08 runtime it runs on. It needs
      `flatpak-builder` where you build (or Flathub's
      `org.flatpak.Builder`), and Flathub set up as a remote. The app's
      Flatpak ID is `--identifier` with any dash in its last part made an
      underscore; its sandbox lets it reach the display (Wayland, or X11)
      and the GPU.

    The packages put the app in `/opt/notes`, a `notes` command in
    `/usr/bin`, and a menu entry (named after `--identifier`) with its
    icon; they depend on the Vulkan loader and those X11 libraries, which
    a desktop has, so a package manager installs any that are missing.
    The package name is the app's name in lower case with
    dashes (`Demo App` is `demo-app`). Tesserae writes the `.deb` and the
    pacman package itself; for the AppImage it fetches `appimagetool`
    1.9.1 and the AppImage runtime (16 MB together, from their GitHub
    releases, checked against the releases' SHA-256), once, into
    `~/.cache/tesserae/tools`. With no `--icon`, the menu gets a plain one.

    The `.rpm` and the Flatpak need tools Tesserae can't fetch; where one
    is missing, the build makes the rest and says what to install:
    `skipped the Flatpak needs flatpak-builder: ...`. Like the
    executable, the `.rpm`, `.deb`, pacman package and AppImage run on
    Linux as new as the one they were built on or newer, so build on the
    oldest you support; the Flatpak brings its own runtime, but that
    runtime's system library must be as new as the build machine's.

`--check` runs the app about to be packed (on macOS the one in
`dist/notes.app`, on Windows `dist/notes/`, on Linux `dist/notes-1.2.0/`) from an empty
folder, as with a single file.

## Installing and uninstalling

What your users do with each installer, for `notes` at 1.2.0 (the
package name is the app's name in lower case with dashes, and the
Flatpak ID is your `--identifier`):

| Installer | Install | Uninstall |
|---|---|---|
| macOS `.dmg` | Open it and drag `notes.app` onto Applications | Drag `notes.app` from Applications to the Trash |
| Windows `-setup.exe` | Run it; silently, `notes-1.2.0-setup.exe /VERYSILENT /CURRENTUSER` | Settings › Apps, or `unins000.exe /VERYSILENT` in the app's folder |
| AppImage | `chmod +x notes-1.2.0-x86_64.AppImage`, then run it | Delete the file |
| `.deb` | `sudo apt install ./notes_1.2.0_amd64.deb` | `sudo apt remove notes` |
| pacman | `sudo pacman -U notes-1.2.0-1-x86_64.pkg.tar.xz` | `sudo pacman -R notes` |
| `.rpm` | `sudo dnf install ./notes-1.2.0-1.x86_64.rpm` | `sudo dnf remove notes` |
| Flatpak | `flatpak install --user notes-1.2.0-x86_64.flatpak` | `flatpak uninstall --user com.yourcompany.notes` |

A new version installs over the old one in each: the same `--identifier`
(macOS, Windows, Flatpak) or package name (Linux) is what ties them
together. Tesserae's own CI installs and runs each of these on every
change to Tesserae, on the platform it's for (Fedora and Arch in
containers), and removes the Windows and Linux ones again.

## How it behaves

- **Start-up** takes a little longer than `python app.py`: the executable
  unpacks itself first (on Linux, about 0.55 s against 0.23 s for a
  `tesserae new` app).
- **Size:** a `tesserae new --shell` app is about 41 MB on Linux, 25 MB on
  macOS and 30 MB on Windows, most of it Python itself and `tre`'s engine.
- **Hot reload is off.** There are no source files to edit, so
  `app.run(hot_reload=True)` logs that and runs without it.
- **Its log** goes to the console when there is one (`--console`, or
  started from a terminal on Linux).

### Running it for a set number of frames

Two environment variables, which `--check` uses, work for any Tesserae
app, built or not, when an automated test or CI runs it:

- `TESSERAE_MAX_FRAMES=n` stops `app.run()` after `n` frames, unless the
  app passes `max_frames` itself.
- `TESSERAE_FRAMES_REPORT=<file>` writes how many frames the run drew to
  that file. With no display a run draws none and returns at once, so a
  clean exit alone doesn't show the app worked.

## On each platform

- **Linux:** the executable needs what any desktop has: a display, a
  Vulkan driver, and the X11 libraries winit loads for a window
  (`libX11`, `libXcursor`, `libXi`, `libxkbcommon-x11`). Without one of
  them the app finds "no display" and exits, as on a bare container. It's also tied to the system
  library (glibc) of the machine it was built on, and runs on that
  version or newer: build on the oldest Linux you want to support.
- **macOS:** the single executable runs from a terminal; for an app to
  double-click, use `--installer`. Without a Developer ID signature
  either is stopped by Gatekeeper the first time; since macOS 15
  (Sequoia) the user allows it in System Settings › Privacy & Security ›
  Open Anyway.
- **Windows:** unsigned, SmartScreen warns the first time it's run.

## Signing

Without a signature, macOS and Windows warn the first time an app is
opened. Signing is done with your own certificate, which Tesserae can't
supply, so `tesserae build` leaves it to you; these are the steps, run
after `tesserae build --installer`.

### macOS: Developer ID and notarization

This needs Apple's [Developer Program](https://developer.apple.com/programs/)
(99 USD a year), a *Developer ID Application* certificate in your
keychain, and, once, an app-specific password stored for `notarytool`:

```bash
xcrun notarytool store-credentials notary --apple-id you@example.com --team-id TEAMID
```

Then sign the app with the hardened runtime (which notarization
requires), make the `.dmg` again from the signed app (the one Tesserae
made holds the ad-hoc-signed app), sign it, notarize it and staple the
ticket to it:

```bash
IDENTITY="Developer ID Application: Your Name (TEAMID)"
codesign --force --deep --options runtime --timestamp --sign "$IDENTITY" dist/notes.app
codesign --verify --deep --strict dist/notes.app

mkdir dmg && cp -R dist/notes.app dmg/ && ln -s /Applications dmg/Applications
hdiutil create -volname notes -srcfolder dmg -ov -format UDZO dist/notes-1.2.0.dmg
codesign --sign "$IDENTITY" --timestamp dist/notes-1.2.0.dmg

xcrun notarytool submit dist/notes-1.2.0.dmg --keychain-profile notary --wait
xcrun stapler staple dist/notes-1.2.0.dmg
```

Once stapled, the `.dmg` opens with no warning, even offline. If the
signed app won't start, PyInstaller's [notes on macOS code
signing](https://pyinstaller.org/en/stable/feature-notes.html) cover
the hardened-runtime entitlements some Python libraries need.

### Windows: a code-signing certificate

This needs a code-signing certificate, from a certificate authority (on
a hardware token, as they're now issued) or through
[Azure Artifact Signing](https://learn.microsoft.com/en-us/azure/artifact-signing/),
and `signtool` from the Windows SDK. Sign the installer, with a
timestamp so the signature outlives the certificate:

```powershell
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a dist\notes-1.2.0-setup.exe
signtool verify /pa dist\notes-1.2.0-setup.exe
```

`/a` picks the best certificate it finds; `/f cert.pfx` or `/sha1
<thumbprint>` names one. SmartScreen still warns about a new signed
installer until it has been downloaded often enough to earn a
reputation, which then carries over to later versions signed with the
same certificate. This signs the installer, not the app it installs:
that would mean signing `dist\notes\notes.exe` before Inno Setup packs
it, which `tesserae build` doesn't do.

### Linux

Linux packages are usually trusted through the repository that serves
them rather than signed one by one: publishing to an apt, dnf or
Flatpak repository means signing that repository with its GPG key.
Given as files, an `.rpm` can still carry a signature
(`rpm --addsign`, with a GPG key set in `%_gpg_name`), and a Flatpak
bundle one (`flatpak build-bundle --gpg-sign`).
