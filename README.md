<div align="center">

<div align="center">
  <img src="/assets/minerva-logo-dark.svg" alt="Minerva" width="700" />
</div>


**Entry for the 2026 CEWIT Hackathon**

*Digital Resilience in Manufacturing*

---

</div>

## The Problem

In smart factories where manufacturing is autonomous, safety remains a pressing concern. Supervision is normally driven by cameras, which are monitored remotely: either by a human or by an AI running in the cloud. However, in the case of a outage, the loss of supervision can be deadly: undetected fires, jammed machines, or other anomalies can lead to production delays, massive financial losses, and danger for human workers on site.

## Our Solution

**Minerva** is an AI monitoring system that runs locally on factory hardware. When cloud connectivity is lost, Minerva takes over, continuously analyzing CCTV feeds and alerting operators via SMS when anomalies are detected. This lends an operation digital resilience in the event of an outage or hosting issue.

## Features

- **Authentication** — Operator login with JWT-based session management
<div align="center">
  <img src="/assets/login.png" alt="Minerva" width="700" />
</div>

- **Multi-feed CCTV dashboard** — Add live camera streams or `.mp4` files; all are monitored simultaneously in a 4-panel grid
<div align="center">
  <img src="/assets/blankdash.png" alt="Minerva" width="700" />
</div>

- **Real-time YOLOv8 object detection** — Runs entirely on-device with no cloud dependency, can detect humans/ objects in frame.
- **Zone-aware anomaly classification** — Each feed is designated as one of three zone types, each with its own severity rules and detection targets:

  | Zone | Critical Triggers | Warning Triggers |
  |------|------------------|-----------------|
  | **Restricted** | Person detected in zone | — |
  | **Production** | Unexpected object on line | Person near machinery |
  | **General** | Fire / smoke | Unidentified activity |

- **Live dashboard alerts** — Incidents are logged in real time with snapshots, severity levels, and timestamps
- **Offline-first architecture** — SQLite database, local snapshot storage, and on-device inference ensure full functionality without internet

### Planned Features

- **Fire & smoke detection** — Custom model integration, as YOLOv8 does not include fire as a default class
- **PPE compliance detection** — Verify workers are wearing required protective equipment
- **Shutdown detection** — Identify when machinery has stopped unexpectedly
- **SMS alerts** — Notify operators and nearby personnel to aid evacuation via Twilio when critical anomalies occur
- **Hardened security** — Role-based access control and audit logging

## Architecture

```
Browser (any device on LAN)
    │  :3000
    ▼
  React dashboard (Vite + Tailwind CSS)
    │  proxy /api →
    ▼
  Flask backend (:8080)
    ├── YOLOv8 detection loop (threaded)
    ├── Video feed manager (OpenCV, MJPEG streams)
    ├── Zone-aware anomaly classifier
    ├── Alert system (email + SMS, rate-limited)
    └── SQLite (incidents, alerts, feed configs)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, Tailwind CSS 4, Lucide icons |
| Backend | Python, Flask, Flask-CORS |
| Detection | Ultralytics YOLOv8, OpenCV |
| Database | SQLite |
| Auth | PyJWT (HMAC-SHA256) |
| Deployment | Docker Compose, NVIDIA Jetson Nano (Ubuntu) |

## Quick Start

```bash
docker compose up --build -d
```

- **Dashboard** → [http://localhost:3000](http://localhost:3000)
- **Backend API** → [http://localhost:8080](http://localhost:8080)

At the hackathon, Minerva ran on an **NVIDIA Jetson Nano** running Ubuntu inside a Docker container.

## Team

[Amartya Das](https://github.com/IcebladeLabs)

[Joon Kim
](https://github.com/kokonut27)

[Bharath Kanagal Raj
](https://github.com/CRLgamer)

[Srihari Kumariduraivan
](https://github.com/Srithegread)

### Advisors

Michael Smit

Aaron Tam
