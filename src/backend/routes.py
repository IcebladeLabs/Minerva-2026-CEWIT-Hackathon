"""
API routes for the manufacturing monitoring dashboard.
"""
from __future__ import annotations
import json, time
from flask import Blueprint, request, jsonify, Response
from backend import auth, database as db, alerts
from backend.video import feed_manager, FeedConfig
from backend.detection import DetectionLoop, save_snapshot

api = Blueprint("api", __name__, url_prefix="/api")

detection_loop: DetectionLoop | None = None


def _on_anomaly_detected(anomalies, annotated_frame, feed_id):
    """Callback fired by DetectionLoop when anomalies are found."""
    feed_state = feed_manager.get_feed(feed_id)
    feed_name = feed_state.config.name if feed_state else feed_id

    for det in anomalies:
        snapshot = save_snapshot(annotated_frame, det)

        db.execute(
            "INSERT INTO incidents (feed_id, feed_name, anomaly_type, severity, "
            "class_name, confidence, bbox, snapshot) VALUES (?,?,?,?,?,?,?,?)",
            (feed_id, feed_name, det.anomaly_type, det.severity,
             det.class_name, det.confidence, json.dumps(list(det.bbox)), snapshot),
        )

        alerts.send_alert(
            anomaly_type=det.anomaly_type,
            severity=det.severity,
            feed_name=feed_name,
            class_name=det.class_name,
            confidence=det.confidence,
            snapshot_file=snapshot,
        )


def init_detection():
    global detection_loop
    detection_loop = DetectionLoop(
        feed_manager,
        on_detections=_on_anomaly_detected,
        interval=0.5,
    )
    detection_loop.start()

    saved = db.query("SELECT * FROM feed_configs WHERE active=1")
    for row in saved:
        cfg = FeedConfig(
            feed_id=row["feed_id"],
            name=row["name"],
            source=row["source"],
            zone_type=row["zone_type"],
        )
        feed_manager.add_feed(cfg)


# ===================== Auth =====================

@api.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(force=True)
    user, err = auth.signup(
        data.get("username", "").strip(),
        data.get("email", "").strip(),
        data.get("password", ""),
    )
    if err:
        return jsonify({"error": err}), 400
    token = auth.create_token(user["id"], user["username"])
    return jsonify({"token": token, "user": user}), 201


@api.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    token, err = auth.login(
        data.get("username", "").strip(),
        data.get("password", ""),
    )
    if err:
        return jsonify({"error": err}), 401
    return jsonify({"token": token})


@api.route("/me", methods=["GET"])
@auth.login_required
def me():
    return jsonify({"user": request.user})


# ===================== Feed management =====================

@api.route("/feeds", methods=["GET"])
@auth.login_required
def list_feeds():
    return jsonify({"feeds": feed_manager.list_feeds()})


@api.route("/feeds", methods=["POST"])
@auth.login_required
def add_feed():
    data = request.get_json(force=True)
    fid = data.get("feed_id", f"cam-{int(time.time())}")
    name = data.get("name", fid)
    source = data.get("source", "0")
    zone_type = data.get("zone_type", "general")

    cfg = FeedConfig(feed_id=fid, name=name, source=source, zone_type=zone_type)
    feed_manager.add_feed(cfg)

    db.execute(
        "INSERT OR REPLACE INTO feed_configs (feed_id, name, source, zone_type, active) "
        "VALUES (?,?,?,?,1)",
        (fid, name, source, zone_type),
    )
    return jsonify({"feed_id": fid, "status": "started"}), 201


@api.route("/feeds/<feed_id>", methods=["DELETE"])
@auth.login_required
def remove_feed(feed_id):
    feed_manager.remove_feed(feed_id)
    db.execute("UPDATE feed_configs SET active=0 WHERE feed_id=?", (feed_id,))
    return jsonify({"status": "stopped"})


# ===================== MJPEG video stream =====================

@api.route("/feeds/<feed_id>/stream")
def feed_stream(feed_id):
    def generate():
        while True:
            frame = feed_manager.get_jpeg_frame(feed_id)
            if frame:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            time.sleep(0.1)

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@api.route("/feeds/<feed_id>/snapshot")
def feed_snapshot(feed_id):
    frame = feed_manager.get_jpeg_frame(feed_id)
    if frame:
        return Response(frame, mimetype="image/jpeg")
    return jsonify({"error": "No frame available"}), 404


# ===================== Detections =====================

@api.route("/detections", methods=["GET"])
@auth.login_required
def get_detections():
    if detection_loop:
        return jsonify({
            "detections": detection_loop.latest,
            "vlm_descriptions": detection_loop.vlm_descriptions,
        })
    return jsonify({"detections": {}, "vlm_descriptions": {}})


# ===================== Incidents =====================

@api.route("/incidents", methods=["GET"])
@auth.login_required
def get_incidents():
    limit = request.args.get("limit", 100, type=int)
    rows = db.query(
        "SELECT * FROM incidents ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    return jsonify({"incidents": [dict(r) for r in rows]})


# ===================== Alerts =====================

@api.route("/alerts", methods=["GET"])
@auth.login_required
def get_alerts():
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"alerts": alerts.get_recent_alerts(limit)})


# ===================== System =====================

@api.route("/health", methods=["GET"])
def health():
    feed_count = len(feed_manager.list_feeds())
    active = sum(1 for f in feed_manager.list_feeds() if f["running"])
    return jsonify({
        "status": "ok",
        "feeds_total": feed_count,
        "feeds_active": active,
        "detection_running": detection_loop is not None and detection_loop._running,
    })


@api.route("/stats", methods=["GET"])
@auth.login_required
def stats():
    total_incidents = db.query("SELECT COUNT(*) as c FROM incidents", one=True)["c"]
    critical = db.query(
        "SELECT COUNT(*) as c FROM incidents WHERE severity='critical'", one=True
    )["c"]
    today = db.query(
        "SELECT COUNT(*) as c FROM incidents WHERE date(created_at)=date('now')", one=True
    )["c"]
    total_alerts = db.query("SELECT COUNT(*) as c FROM alerts", one=True)["c"]
    return jsonify({
        "total_incidents": total_incidents,
        "critical_incidents": critical,
        "incidents_today": today,
        "total_alerts": total_alerts,
    })
