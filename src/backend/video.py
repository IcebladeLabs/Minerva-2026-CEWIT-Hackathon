"""
Multi-source video feed manager.
Supports USB cameras (/dev/videoN or integer), RTSP streams, and local .mp4 files.
MP4 files loop indefinitely. Webcams stream live.
"""
from __future__ import annotations
import threading, time, logging, os
from typing import Optional
from dataclasses import dataclass, field

try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore

log = logging.getLogger(__name__)


@dataclass
class FeedConfig:
    feed_id: str
    name: str
    source: str | int
    zone_type: str = "general"
    fps_limit: int = 5


@dataclass
class FeedState:
    config: FeedConfig
    running: bool = False
    frame: Optional[bytes] = field(default=None, repr=False)
    raw_frame: object = field(default=None, repr=False)
    frame_count: int = 0
    fps: float = 0.0
    last_error: str = ""
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _thread: Optional[threading.Thread] = field(default=None, repr=False)


def _resolve_source(source):
    """Convert source string to what cv2.VideoCapture expects."""
    if isinstance(source, int):
        return source, True
    s = str(source).strip()
    if s.isdigit():
        return int(s), True
    if s.startswith("/dev/video"):
        return s, True
    # RTSP or file path
    is_live = s.lower().startswith("rtsp://") or s.lower().startswith("http://")
    return s, is_live


class FeedManager:
    def __init__(self):
        self._feeds: dict[str, FeedState] = {}
        self._lock = threading.Lock()

    def add_feed(self, cfg: FeedConfig) -> str:
        state = FeedState(config=cfg)
        with self._lock:
            self._feeds[cfg.feed_id] = state
        self._start_capture(state)
        return cfg.feed_id

    def remove_feed(self, feed_id: str):
        with self._lock:
            state = self._feeds.pop(feed_id, None)
        if state:
            state.running = False

    def get_feed(self, feed_id: str) -> FeedState | None:
        return self._feeds.get(feed_id)

    def list_feeds(self) -> list[dict]:
        return [
            {
                "feed_id": s.config.feed_id,
                "name": s.config.name,
                "source": str(s.config.source),
                "zone_type": s.config.zone_type,
                "running": s.running,
                "fps": round(s.fps, 1),
                "frame_count": s.frame_count,
                "last_error": s.last_error,
            }
            for s in self._feeds.values()
        ]

    def get_jpeg_frame(self, feed_id: str) -> bytes | None:
        state = self._feeds.get(feed_id)
        if state:
            with state._lock:
                return state.frame
        return None

    def get_raw_frame(self, feed_id: str):
        state = self._feeds.get(feed_id)
        if state:
            with state._lock:
                return state.raw_frame
        return None

    def stop_all(self):
        for s in self._feeds.values():
            s.running = False

    def _start_capture(self, state: FeedState):
        if cv2 is None:
            state.last_error = "OpenCV not installed"
            log.error("OpenCV not available, cannot start feed %s", state.config.feed_id)
            return

        def _run():
            src, is_live = _resolve_source(state.config.source)
            is_file = isinstance(src, str) and not is_live

            if is_file and not os.path.isfile(src):
                state.last_error = f"File not found: {src}"
                log.error("Feed %s: file not found: %s", state.config.feed_id, src)
                return

            log.info("Feed %s: opening source %r (file=%s, live=%s)",
                     state.config.feed_id, src, is_file, is_live)

            cap = cv2.VideoCapture(src)
            if not cap.isOpened():
                state.last_error = f"Cannot open: {src}"
                log.error("Feed %s: cv2.VideoCapture failed for %r", state.config.feed_id, src)
                return

            state.running = True
            state.last_error = ""
            interval = 3.0 / max(state.config.fps_limit, 1)
            t0 = time.monotonic()
            frame_count_window = 0

            log.info("Feed %s: streaming started", state.config.feed_id)

            try:
                while state.running:
                    ret, frame = cap.read()

                    if not ret:
                        if is_file:
                            # Loop mp4: rewind to start
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            ret, frame = cap.read()
                            if not ret:
                                # Truly broken file
                                state.last_error = "Cannot read video file"
                                log.error("Feed %s: cannot read after rewind", state.config.feed_id)
                                break
                        else:
                            state.last_error = "Feed ended or lost"
                            log.warning("Feed %s: stream ended", state.config.feed_id)
                            break

                    ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    if ok:
                        with state._lock:
                            state.frame = jpeg.tobytes()
                            state.raw_frame = frame
                            state.frame_count += 1

                    frame_count_window += 1
                    elapsed = time.monotonic() - t0
                    if elapsed >= 1.0:
                        state.fps = frame_count_window / elapsed
                        frame_count_window = 0
                        t0 = time.monotonic()

                    time.sleep(interval)
            except Exception as e:
                state.last_error = str(e)
                log.exception("Feed %s: crashed", state.config.feed_id)
            finally:
                cap.release()
                state.running = False
                log.info("Feed %s: stopped", state.config.feed_id)

        t = threading.Thread(target=_run, daemon=True, name=f"feed-{state.config.feed_id}")
        state._thread = t
        t.start()


feed_manager = FeedManager()
