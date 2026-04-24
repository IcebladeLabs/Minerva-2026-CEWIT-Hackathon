"""
Vision-Language Model client.
Talks to the InternVL3 inference server running on the Jetson via Docker.
Used to generate natural-language descriptions of anomaly snapshots.
"""
from __future__ import annotations
import base64, time, logging, threading
from typing import Optional

try:
    import requests as _req
except ImportError:
    _req = None  # type: ignore

log = logging.getLogger(__name__)

VLM_URL = "http://localhost:8000"

PROMPTS = {
    "fire": (
        "You are a factory safety AI. Describe what you see. "
        "Is there fire, smoke, or thermal hazard? Rate severity: LOW / MEDIUM / HIGH / CRITICAL."
    ),
    "intruder": (
        "You are a factory security AI. A person has been detected in a restricted zone. "
        "Describe the scene. Is the person wearing PPE? Are they near dangerous machinery?"
    ),
    "line_fault": (
        "You are a manufacturing quality AI. Something unexpected was detected on the production line. "
        "Describe what you see and whether it could cause a fault or stoppage."
    ),
    "safety": (
        "You are a factory safety AI. A person is near active machinery. "
        "Describe the scene and any safety concerns."
    ),
    "general": (
        "You are monitoring a factory floor. Briefly describe what you see "
        "and flag any hazards or anomalies."
    ),
}


def ask_vlm(image_path: str, anomaly_type: str = "general", max_tokens: int = 96) -> str:
    if _req is None:
        return "[requests library not available]"

    prompt = PROMPTS.get(anomaly_type, PROMPTS["general"])

    try:
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        r = _req.post(f"{VLM_URL}/infer", json={
            "image_b64": image_b64,
            "prompt": prompt,
            "max_tokens": max_tokens,
        }, timeout=10)
        job_id = r.json()["job_id"]

        for _ in range(30):
            result = _req.get(f"{VLM_URL}/result/{job_id}", timeout=5).json()
            if result["status"] == "ready":
                return result["text"]
            time.sleep(0.5)

        return "[VLM timeout]"
    except Exception as e:
        log.warning("VLM request failed: %s", e)
        return f"[VLM unavailable: {e}]"


def ask_vlm_async(image_path: str, anomaly_type: str, callback):
    """Fire-and-forget VLM query in a background thread."""
    def _run():
        text = ask_vlm(image_path, anomaly_type)
        callback(text)
    threading.Thread(target=_run, daemon=True).start()
