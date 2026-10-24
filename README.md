# OTW PTX

**Send your Pro Tools session to a mix engineer in one zip.**

Drop in a Pro Tools session (`.ptx`) and OTW PTX packs everything the engineer needs into a single zip:

- the session file
- every audio file the session actually uses, even ones stored outside the session folder (unused takes are left out, so the zip stays small)
- the `Bounced Files` folder

It's the same as Pro Tools' **File → Save Copy In… → "Audio Files"** and then zipping the folder, minus the clicking around. Works on Mac and Windows, and you don't need Pro Tools open.

## Download

Get the latest version from the **[Releases page](https://github.com/outthewayyyyyyy/OTWPTX/releases/latest)**:

- **Mac** (Intel or Apple Silicon): `OTW-PTX-x.y.z-mac.pkg`
- **Windows**: `OTW-PTX-x.y.z-windows-setup.exe`

### Installing on Mac

The app isn't signed by Apple, so macOS asks you to approve it once:

1. Double-click the `.pkg`. macOS says it can't verify the developer. Click **Done**.
2. Open **System Settings → Privacy & Security**, scroll down, and click **Open Anyway** next to the OTW PTX message. Enter your Mac password.
3. Follow the installer. **OTW PTX** goes into your Applications folder and opens like any other app from then on.

### Installing on Windows

Run the setup `.exe`. If Windows says "Windows protected your PC", click **More info → Run anyway**.

## How to use it

1. Open **OTW PTX**.
2. Drag your `.ptx` session onto the window (or click to choose it).
3. If any audio files are missing, the app lists them and lets you point to a folder or drive to search, or leave them out.
4. Choose where to save the zip (defaults to your Desktop as `<Session> - Mix.zip`).
5. Send the zip to your engineer.

Your session is only read, never changed.

## Building from source

Needs Python 3.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python app.py
```

Check the parser against a session from the command line:

```bash
.venv/bin/python ptx.py "/path/to/Session.ptx"
```

`build-local.sh` builds and installs the Mac app on your own machine.

Every push to `main` builds both installers in GitHub Actions and publishes them as a release (version `0.1.<build number>`). To build without releasing, go to **Actions → Build installers → Run workflow**.

| File | What it does |
| --- | --- |
| `ptx.py` | Reads the session and builds the zip |
| `app.py` | The app window |
| `.github/workflows/build.yml` | Builds the Mac and Windows installers |
| `installer.iss` | Windows installer |
| `pkg-scripts/postinstall` | Ad-hoc signs the app on the user's Mac after install |

## Credits

`.ptx` decryption is ported from [ptformat](https://github.com/zamaudio/ptformat) (LGPL-2.1+). Pro Tools is a trademark of Avid Technology; this project isn't affiliated with Avid.
