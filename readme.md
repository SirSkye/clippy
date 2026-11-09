# ClipSync

Send your iPad clipboard (text **and** images) to your Windows laptop with one tap.

ClipSync is a small FastAPI server that runs on Windows and receives clipboard contents from an iPad Shortcut over your local network. Copy something on the iPad, tap a button, and it is ready to paste on your laptop.

---

## Features

- 📋 **Text sync**: plain text and Unicode
- 🖼️ **Image sync**: PNG, JPEG and **HEIC** (iPad photos and screenshots)
- 🔄 **Automatic EXIF rotation**, so portrait photos don't paste sideways
- 🪟 **Transparency-aware**: sets both `CF_DIB` (works everywhere) and `PNG` (keeps transparency in apps that support it)
- 🔐 **Token authentication** on every request
- 📡 **`.local` hostname discovery** via mDNS, so you don't have to hardcode an IP
- 🔳 **QR code pairing** to set up the iPad without typing

---

## How it works

```
┌──────────────────────┐        HTTP POST /clip         ┌─────────────────────────┐
│        iPad          │  ───────────────────────────►  │     Windows laptop      │
│                      │   X-Token: <secret>            │                         │
│  Get Clipboard       │   Content-Type: image/heic     │  FastAPI server         │
│  → Get Contents of   │   <raw bytes>                  │  → decode (Pillow)      │
│    URL (Shortcuts)   │                                │  → set Windows clipboard│
└──────────────────────┘                                └─────────────────────────┘
```

iPadOS doesn't let apps watch the clipboard in the background, so syncing is triggered by a tap (Home Screen icon, Control Center or an AssistiveTouch button).

---

## Requirements

**Laptop**
- Windows 10 or 11
- Python 3.10+

**iPad**
- iPadOS with the **Shortcuts** app (built in)
- iPadOS 18+ if you want the Control Center button

Both devices must be on the **same network**. Some campus and public Wi-Fi networks block devices from reaching each other; see [Troubleshooting](#troubleshooting).

---

## Installation

```bash
git clone https://github.com/<your-username>/clipsync.git
cd clipsync
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt`:

```
fastapi
uvicorn
pillow
pillow-heif
pywin32
zeroconf
qrcode
```

---

## Configuration

Set your secret token as an environment variable (or in a `.env` file, which you should **not** commit):

```powershell
setx CLIPSYNC_TOKEN "your-long-random-secret"
```

Generate a good token with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Running the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8765
```

> `--host 0.0.0.0` is required. The default `127.0.0.1` only accepts connections from the laptop itself.

Check it's working by opening `http://localhost:8000/docs` on the laptop, then `http://<laptop-ip>:8000/docs` in Safari on the iPad.

---

## iPad Shortcut setup

1. Open **Shortcuts** → tap **+** → rename it **Send to Laptop**.
2. Add **Get Clipboard**.
3. Add **Get Contents of URL**.
   - If it reads *"Get contents of Clipboard"*, tap **Clipboard** → **Clear**, then tap **URL** and enter:
     `http://clipsync.local:8765/clip` (or your laptop's IP).
4. Expand the action (›):
   - **Method:** `POST`
   - **Headers:** `X-Token` → your token
   - **Request Body:** `File` → *Select Variable* → **Clipboard**
5. *(Optional)* Add **Show Notification**: "Sent ✓".
6. On the first run, **allow** local network access.

**Skip the "Allow Paste" prompt:** Settings → Apps → Shortcuts → **Paste from Other Apps** → **Allow**.

### One-tap trigger

| Method | Setup |
|---|---|
| **AssistiveTouch** (recommended) | Settings → Accessibility → Touch → AssistiveTouch → Custom Actions → Double-Tap → *Send to Laptop* |
| **Control Center** | Swipe down from top-right → **+** → Add a Control → Shortcuts → Run Shortcut |
| **Home Screen** | Shortcut menu → Add to Home Screen |

---

## QR code pairing

Instead of typing the address and token into the Shortcut:

1. On the laptop, open `http://localhost:8765/pair` to show a QR code containing:
   ```json
   {"host": "clipsync.local", "port": 8765, "token": "..."}
   ```
2. On the iPad, run the **Pair** shortcut: *Scan QR or Barcode* → *Get Dictionary from Input* → *Save File* (overwrite).
3. **Send to Laptop** reads the saved file for its host and token.

Re-scan whenever the address or token changes. Treat the QR code like a password.

---

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/clip` | Set the Windows clipboard from the request body |
| `GET` | `/clip` | *(planned)* Return the current Windows clipboard |
| `GET` | `/pair` | Show the pairing QR code (localhost only) |

### `POST /clip`

**Headers**

| Header | Value |
|---|---|
| `X-Token` | Your secret token |
| `Content-Type` | `text/plain`, `image/png`, `image/jpeg`, `image/heic`, … |

**Responses**

| Code | Meaning |
|---|---|
| `200` | Clipboard updated |
| `401` | Missing or wrong token |
| `413` | Body too large |
| `415` | Unsupported or corrupt image |

**Examples**

```bash
# Text
curl -X POST http://localhost:8765/clip \
  -H "X-Token: $CLIPSYNC_TOKEN" \
  -H "Content-Type: text/plain" \
  --data "hello from curl"

# Image (use --data-binary, not --data)
curl -X POST http://localhost:8765/clip \
  -H "X-Token: $CLIPSYNC_TOKEN" \
  -H "Content-Type: image/heic" \
  --data-binary @photo.heic
```

---

## Running at startup

1. Create `start_clipsync.bat`:
   ```bat
   @echo off
   cd /d C:\path\to\clipsync
   .venv\Scripts\pythonw.exe -m uvicorn main:app --host 0.0.0.0 --port 8765
   ```
2. Press `Win + R` → `shell:startup` → put a shortcut to the `.bat` file there.

Using `pythonw` means no console window appears.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| iPad can't reach the server | Same Wi-Fi? Server started with `--host 0.0.0.0`? Firewall allows Python on private networks? |
| Works at home, not on campus | Many campus networks (e.g. eduroam) block device-to-device traffic and mDNS. Use [Tailscale](https://tailscale.com) on both devices. |
| `clipsync.local` doesn't resolve | Use the laptop's IP (`ipconfig` → IPv4), or allow UDP 5353 in the firewall. |
| Image pastes sideways | Make sure EXIF rotation (`ImageOps.exif_transpose`) runs before encoding. |
| Transparent areas are black | Expected in apps that only read `CF_DIB`. Apps that read the `PNG` format keep transparency. |
| HEIC fails to open | Install `pillow-heif` and call `register_heif_opener()` at startup. |
| Works with curl, not Shortcuts | Log `request.headers` and `len(body)` to see what Shortcuts actually sends. |

---

## Security notes

- The server accepts connections from **anyone on the same network**, so always use a strong token.
- Traffic is plain HTTP, so don't run this on untrusted networks. Use Tailscale for an encrypted tunnel when away from home.

---

## Roadmap

- [ ] Implement Security Token
- [ ] Laptop → iPad (`GET /clip` + "Get from Laptop" shortcut)
- [ ] Clipboard history (`GET /history`)
- [ ] System tray icon
- [ ] One-time pairing codes that expire
- [ ] Fallback from `.local` to the Tailscal

---
