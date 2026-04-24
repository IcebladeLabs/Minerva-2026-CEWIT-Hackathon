"""
YOLOv8 detection engine with anomaly classification.

Anomaly categories:
  - fire        : fire / smoke detected
  - intruder    : person in a restricted zone
  - line_fault  : unexpected object or missing expected object on production line
  - safety      : person without expected PPE proximity
"""
from __future__ import annotations
import threading, time, logging, os, json
from dataclasses import dataclass
from typing import Optional

from backend.config import YOLO_MODEL, YOLO_CONFIDENCE, SNAPSHOTS_DIR

log = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
    _model: Optional[YOLO] = None
except ImportError:
    YOLO = None  # type: ignore
    _model = None

try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore

# COCO class names we care about for manufacturing anomalies
PERSON_CLASSES = {"person"}
FIRE_KEYWORDS = {"fire", "flame", "smoke"}
VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle"}
EXPECTED_LINE_OBJECTS = {"bottle", "cup", "bowl", "box", "suitcase", "handbag", "backpack"}


@dataclass
class Detection:
    class_name: str
    confidence: float
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    anomaly_type: str = ""           # fire | intruder | line_fault | safety | ""
    severity: str = "info"           # info | warning | critical
    feed_id: str = ""


def load_model():
    global _model
    if YOLO is None:
        log.warning("Ultralytics not installed -- detection disabled")
        return
    if _model is None:
        log.info("Loading YOLOv8 model: %s", YOLO_MODEL)
        _model = YOLO(YOLO_MODEL)
        log.info("Model loaded")


def detect_frame(frame, feed_id: str = "", zone_type: str = "general") -> list[Detection]:
    """Run YOLOv8 on a single frame, return classified detections."""
    if _model is None or frame is None:
        return []

    results = _model(frame, conf=YOLO_CONFIDENCE, verbose=False)
    detections: list[Detection] = []

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            cls_name = r.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]

            det = Detection(
                class_name=cls_name,
                confidence=conf,
                bbox=(x1, y1, x2, y2),
                feed_id=feed_id,
            )

            _classify_anomaly(det, zone_type)
            detections.append(det)

    return detections


def _classify_anomaly(det: Detection, zone_type: str):
    """Assign anomaly_type and severity based on object class and zone context."""
    name = det.class_name.lower()

    if any(kw in name for kw in FIRE_KEYWORDS):
        det.anomaly_type = "fire"
        det.severity = "critical"
        return

    if name in PERSON_CLASSES:
        if zone_type == "restricted":
            det.anomaly_type = "intruder"
            det.severity = "critical"
        elif zone_type == "production_line":
            det.anomaly_type = "safety"
            det.severity = "warning"
        return

    if zone_type == "production_line":
        if name in VEHICLE_CLASSES:
            det.anomaly_type = "line_fault"
            det.severity = "warning"
        elif name not in EXPECTED_LINE_OBJECTS and det.confidence > 0.6:
            det.anomaly_type = "line_fault"
            det.severity = "warning"


def annotate_frame(frame, detections: list[Detection]):
    """Draw bounding boxes and labels on the frame. Returns annotated copy."""
    if cv2 is None or frame is None:
        return frame
    img = frame.copy()

    colors = {
        "critical": (0, 0, 255),
        "warning": (0, 165, 255),
        "info": (0, 255, 0),
    }

    for det in detections:
        color = colors.get(det.severity, (0, 255, 0))
        x1, y1, x2, y2 = det.bbox
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        label = det.class_name
        if det.anomaly_type:
            label = f"[{det.anomaly_type.upper()}] {label}"
        label += f" {det.confidence:.0%}"

        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
        cv2.putText(img, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return img


def save_snapshot(frame, detection: Detection) -> str:
    """Save a detection frame to disk, return the filename."""
    if cv2 is None:
        return ""
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    fname = f"{ts}_{detection.feed_id}_{detection.anomaly_type}.jpg"
    path = os.path.join(SNAPSHOTS_DIR, fname)
    cv2.imwrite(path, frame)
    return fname


class DetectionLoop:
    """
    Continuously pulls frames from all feeds, runs detection,
    and pushes results to a callback.  Optionally fires VLM queries
    on anomaly snapshots for natural-language descriptions.
    """
    def __init__(self, feed_manager, on_detections=None, interval: float = 0.5):
        self._fm = feed_manager
        self._on_detections = on_detections
        self._interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._latest: dict[str, list[dict]] = {}
        self._vlm_descriptions: dict[str, str] = {}
        self._lock = threading.Lock()

    @property
    def latest(self) -> dict[str, list[dict]]:
        with self._lock:
            return dict(self._latest)

    @property
    def vlm_descriptions(self) -> dict[str, str]:
        with self._lock:
            return dict(self._vlm_descriptions)

    def start(self):
        load_model()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="detection-loop")
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        from backend.vlm import ask_vlm_async

        while self._running:
            for info in self._fm.list_feeds():
                if not info["running"]:
                    continue
                fid = info["feed_id"]
                raw = self._fm.get_raw_frame(fid)
                if raw is None:
                    continue

                dets = detect_frame(raw, feed_id=fid, zone_type=info.get("zone_type", "general"))
                det_dicts = [
                    {
                        "class_name": d.class_name,
                        "confidence": round(d.confidence, 3),
                        "bbox": list(d.bbox),
                        "anomaly_type": d.anomaly_type,
                        "severity": d.severity,
                        "feed_id": d.feed_id,
                        "timestamp": time.time(),
                    }
                    for d in dets
                ]

                with self._lock:
                    self._latest[fid] = det_dicts

                anomalies = [d for d in dets if d.anomaly_type]
                if anomalies and self._on_detections:
                    annotated = annotate_frame(raw, dets)
                    self._on_detections(anomalies, annotated, fid)

                    # Fire async VLM query on the snapshot for richer description
                    snapshot_path = save_snapshot(annotated, anomalies[0])
                    if snapshot_path:
                        full_path = os.path.join(SNAPSHOTS_DIR, snapshot_path)
                        atype = anomalies[0].anomaly_type
                        def _vlm_cb(text, _fid=fid):
                            with self._lock:
                                self._vlm_descriptions[_fid] = text
                        ask_vlm_async(full_path, atype, _vlm_cb)

                # Always update the feed's JPEG with annotated frame
                annotated = annotate_frame(raw, dets) if dets else raw
                if cv2 is not None and annotated is not None:
                    _, jpeg = cv2.imencode(".jpg", annotated,
                                           [cv2.IMWRITE_JPEG_QUALITY, 70])
                    state = self._fm.get_feed(fid)
                    if state:
                        with state._lock:
                            state.frame = jpeg.tobytes()

            time.sleep(self._interval)
