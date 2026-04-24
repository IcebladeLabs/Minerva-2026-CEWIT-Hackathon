# Minerva — Transfer & Deploy Guide

## Step 1: Get the project onto the other machine

### Option A: Email (simplest — tarball is ~30 KB)

On this Mac, the tarball is ready at:
```
~/Downloads/sentinelline.tar.gz
```
Email it to yourself. On the Ubuntu machine, download it via Firefox then:

```bash
cd ~/Downloads
tar xzf sentinelline.tar.gz
cd "CEWIT Hack"
```

### Option B: USB drive

```bash
# On this Mac
cp ~/Downloads/sentinelline.tar.gz /Volumes/YOUR_USB/

# On the Ubuntu machine
cp /media/*/sentinelline.tar.gz ~/
cd ~ && tar xzf sentinelline.tar.gz && cd "CEWIT Hack"
```

### Option C: LAN transfer (if on same network)

```bash
# On the Ubuntu machine, find the IP:
hostname -I    # e.g. 192.168.1.42

# On this Mac:
scp ~/Downloads/sentinelline.tar.gz cewit_admin@192.168.1.42:~/
# Password: Cewit@2026!

# Then on the Ubuntu machine:
cd ~ && tar xzf sentinelline.tar.gz && cd "CEWIT Hack"
```

---

## Step 2: Add your demo videos

```bash
mkdir -p videos
# Copy .mp4 files into the videos/ folder
cp /path/to/*.mp4 videos/
```

---

## Step 3: Deploy with Docker

```bash
docker compose up --build -d
```

- **Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8080

To see logs: `docker compose logs -f`
To stop: `docker compose down`

### If no webcam is connected

The `docker-compose.yml` has `devices: /dev/video0` enabled. If no webcam exists, either:
- Comment out the `devices` section, OR
- Just ignore the error — it won't prevent the backend from starting

### Video feed paths

In the dashboard, when adding an MP4 feed, use the **Docker-mounted** path:
```
/app/videos/your_video.mp4
```
(This maps to `./videos/` on the host.)

For a webcam: use `0` as the source.

---

## Step 4: Set up email alerts (easiest)

Use a Gmail account with an [App Password](https://myaccount.google.com/apppasswords):

1. Go to Google Account → Security → 2-Step Verification → App Passwords
2. Create one for "Mail"
3. Set these env vars before running `docker compose up`:

```bash
export SMTP_USER=yourname@gmail.com
export SMTP_PASSWORD=abcd-efgh-ijkl-mnop   # the 16-char app password
export ALERT_EMAILS=operator1@email.com,operator2@email.com
```

Or add directly to `docker-compose.yml` under `environment`:
```yaml
- SMTP_USER=yourname@gmail.com
- SMTP_PASSWORD=abcd-efgh-ijkl-mnop
- ALERT_EMAILS=operator1@email.com,operator2@email.com
```

Then `docker compose down && docker compose up -d`.

### SMS alerts (optional, needs Twilio account)

```bash
export TWILIO_SID=ACxxxxxxxx
export TWILIO_AUTH_TOKEN=xxxxxxxx
export TWILIO_FROM_NUMBER=+1234567890
export ALERT_PHONES=+1987654321
```

---

## Step 5 (optional): VLM integration

If the VLM Docker container is running (from the hackathon `vlms.ipynb`):
- It listens on `localhost:8000`
- Minerva auto-queries it when anomalies are detected
- Descriptions appear in the status bar under each feed

---

## Using the Logo in Slides

Two SVG files are included in the project root:

| File | Use |
|------|-----|
| `minerva-logo.svg` | White text — for dark backgrounds |
| `minerva-logo-dark.svg` | Dark text — for light backgrounds |

Open in a browser and screenshot, or drag directly into Google Slides / PowerPoint. SVGs scale to any size without losing quality.

---

## Deploy WITHOUT Docker (alternative)

```bash
cd ~/CEWIT\ Hack

source ~/venv/bin/activate   # Jetson's pre-installed venv
pip install flask flask-cors pyjwt

# Install Node for the frontend
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
cd frontend && npm install && npm run build && cd ..

python3 run.py
# Dashboard at http://localhost:8080
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Port in use | `export PORT=9090` or edit docker-compose.yml |
| Feed says "File not found" | Use Docker path: `/app/videos/filename.mp4` |
| Feed says "Feed offline" | Check `docker compose logs backend` for the actual error |
| No webcam | Comment out `devices` in docker-compose.yml |
| YOLO model download fails | Pre-download `yolov8n.pt` and put it in the project root |
| Email not sending | Verify app password works: try logging into smtp.gmail.com manually |
| npm install fails | Run `sudo apt install nodejs npm` first |
