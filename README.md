# OTW PTX

Drop in a Pro Tools session (`.ptx`) and get one zip with everything a mix engineer needs. It's the same as **File → Save Copy In… → "Audio Files"**, then zipping the folder:

- the session file
- every audio file the session uses, including files outside the session folder (unused takes are left out)
- the `Bounced Files` folder

If audio files are missing, the app lists them and lets the user point to a folder or drive to search.

## For users

- **Mac** (Intel or Apple Silicon): open `OTW-PTX-x.y.z-mac.dmg` and drag **OTW PTX** to Applications.
- **Windows**: run `OTW-PTX-x.y.z-windows-setup.exe`. The Windows build isn't code-signed, so SmartScreen may say "Windows protected your PC". Click **More info → Run anyway**.

## Building the installers

Every push to `main` builds both installers and publishes them as a GitHub Release (version `0.1.<build number>`). Pushes to other branches never build, so do your work on a branch and merge it into `main` when it is ready to release.

To build without merging, go to GitHub → **Actions** → **Build installers** → **Run workflow** and pick a branch (optionally tick **Publish a GitHub Release**).

Cost: a run takes about 5 min on macOS and 4 min on Windows. On a private repo, GitHub bills macOS minutes at 10× and Windows at 2× against your free monthly minutes.

### Mac signing (one-time setup)

Without these secrets the Mac build still works, but it's unsigned and users get the "can't be opened" warning. Add them under **Settings → Secrets and variables → Actions**:

| Secret | What it is |
|---|---|
| `APPLE_CERT_P12_BASE64` | Your **Developer ID Application** certificate exported from Keychain Access as `.p12`, then `base64 -i cert.p12 \| pbcopy` |
| `APPLE_CERT_PASSWORD` | Password you set when exporting the `.p12` |
| `APPLE_ID` | Your Apple ID email |
| `APPLE_APP_PASSWORD` | An app-specific password from appleid.apple.com |
| `APPLE_TEAM_ID` | 10-character Team ID (developer.apple.com → Membership) |

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

Files: `ptx.py` reads the session and builds the zip, `app.py` is the window, `.github/workflows/build.yml` is the build, `installer.iss` is the Windows installer.

`.ptx` decryption is ported from [ptformat](https://github.com/zamaudio/ptformat) (LGPL-2.1+).
