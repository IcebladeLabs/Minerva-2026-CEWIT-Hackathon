# Minerva — Industrial AI Watchguard

Edge AI system that monitors factory CCTV feeds for anomalies when cloud connectivity is lost.  
Built for NVIDIA Jetson Nano. Theme: **Digital Resilience in Manufacturing.**

## Quick Start

```bash
# Put .mp4 demo videos in videos/
mkdir -p videos && cp /path/to/*.mp4 videos/

# Launch
docker compose up --build -d
```

Dashboard: **http://localhost:3000**

## Features

- **4-panel live CCTV dashboard** — MP4 files loop, webcams stream live
- **YOLOv8 object detection** — runs on-device, no cloud
- **Anomaly classification** by zone:
  - Fire/smoke → CRITICAL
  - Person in restricted zone → CRITICAL
  - Unexpected object on production line → WARNING
  - Person near machinery → WARNING
- **Email alerts** via SMTP (Gmail app password, stdlib — zero extra deps)
- **SMS alerts** via Twilio (optional)
- **VLM integration** — InternVL3 generates natural-language scene descriptions
- **Offline-first** — SQLite DB, local snapshots, cellular SMS, works without internet

## Architecture

```
Browser (any device on LAN)
    │ :3000
    ▼
  nginx → React dashboard (Vite + Tailwind)
    │ proxy /api →
    ▼
  Flask backend (:8080)
    ├── YOLOv8 detection loop (threaded)
    ├── Video feed manager (OpenCV, MJPEG streams)
    ├── Anomaly classifier (zone-aware rules)
    ├── Alert system (Email + SMS, rate-limited)
    ├── VLM client (async queries to InternVL3)
    └── SQLite (incidents, alerts, feed configs)
```
