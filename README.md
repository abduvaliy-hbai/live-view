# Hikvision Live Viewer

Python app for viewing a Hikvision camera live over RTSP when your computer is on the same network as the camera.

It also includes basic real-time motion tracking, shown as boxes around moving areas in the video.

## Setup

Open a terminal in this folder:

```bash
cd /home/compotuzb/Documents/hikvision_live_viewer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and enter your camera IP, username, and password.

## Run

```bash
python view_camera.py
```

Press `q` in the video window to quit.

## Notes

- Main stream is usually channel `101`.
- Sub stream is usually channel `102`; use this if the video is slow.
- Your computer must be on the same network as the camera.
- RTSP must be enabled on the Hikvision camera.
- The default RTSP URL is:

```text
rtsp://USERNAME:PASSWORD@CAMERA_IP:554/Streaming/Channels/101
```

If your camera uses a different stream path, set `HIKVISION_RTSP_URL` in `.env`.

To disable motion boxes, set this in `.env`:

```text
ENABLE_MOTION_TRACKING=false
```
