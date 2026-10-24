# OTW PTX

Drop in a Pro Tools session (`.ptx`) and get one zip with everything a mix engineer needs. It's the same as **File → Save Copy In… → "Audio Files"**, then zipping the folder:

- the session file
- every audio file the session uses, including files outside the session folder (unused takes are left out)
- the `Bounced Files` folder

If audio files are missing, the app lists them and lets the user point to a folder or drive to search.

## For users

- **Mac** (Intel or Apple Silicon): double-click `OTW-PTX-x.y.z-mac.pkg`. The first time, macOS says it can't verify the developer. Click **Done**, open **System Settings → Privacy & Security**, scroll down, click **Open Anyway** next to the OTW PTX message, and enter your Mac password. Then follow the installer. It puts **OTW PTX** in Applications and signs it for that Mac, so after that it opens like any other app.
- **Windows**: run `OTW-PTX-x.y.z-windows-setup.exe`. The Windows build isn't code-signed, so SmartScreen may say "Windows protected your PC". Click **More info → Run anyway**.

## Building the installers

Every push to `main` builds both installers and publishes them as a GitHub Release (version `0.1.<build number>`). Pushes to other branches never build, so do your work on a branch and merge it into `main` when it is ready to release.

To build without merging, go to GitHub → **Actions** → **Build installers** → **Run workflow** and pick a branch (optionally tick **Publish a GitHub Release**).

Cost: a run takes about 5 min on macOS and 4 min on Windows. On a private repo, GitHub bills macOS minutes at 10× and Windows at 2× against your free monthly minutes.

The Mac installer isn't signed by Apple; it ad-hoc signs the app on each user's Mac when it installs (`pkg-scripts/postinstall`). The `APPLE_*` repo secrets aren't used.

## Developing

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python app.py
```

Self-check the parser against real sessions:

```bash
.venv/bin/python ptx.py "/path/to/Session.ptx"
```

Files: `ptx.py` reads the session and builds the zip, `app.py` is the window, `.github/workflows/build.yml` is the build, `installer.iss` is the Windows installer, `pkg-scripts/postinstall` runs after the Mac install, and `build-local.sh` builds and installs the app on your own Mac.

`.ptx` decryption is ported from [ptformat](https://github.com/zamaudio/ptformat) (LGPL-2.1+).
