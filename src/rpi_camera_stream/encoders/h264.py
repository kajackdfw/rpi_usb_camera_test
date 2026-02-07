"""H.264 encoding using FFmpeg subprocess."""

import logging
import shutil
import subprocess
import threading
from queue import Empty, Queue
from typing import Callable, Optional

import numpy as np

from ..config import H264Config, QualityPreset

logger = logging.getLogger(__name__)


class H264Encoder:
    """H.264 encoder using FFmpeg subprocess.

    Receives BGR frames and outputs H.264 NAL units via callback.
    Uses hardware encoding (h264_v4l2m2m) on Pi 4, falls back to libx264.
    """

    def __init__(
        self,
        config: H264Config,
        preset: QualityPreset,
        on_data: Callable[[bytes], None],
    ):
        self.config = config
        self.preset = preset
        self.on_data = on_data
        self._process: Optional[subprocess.Popen] = None
        self._running = False
        self._frame_queue: Queue[np.ndarray] = Queue(maxsize=5)
        self._input_thread: Optional[threading.Thread] = None
        self._output_thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        """Start the FFmpeg encoder process."""
        if self._running:
            return True

        encoder = self._select_encoder()
        if encoder is None:
            logger.error("No suitable H.264 encoder found")
            return False

        cmd = self._build_ffmpeg_command(encoder)
        logger.info(f"Starting FFmpeg: {' '.join(cmd)}")

        try:
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            logger.error(f"Failed to start FFmpeg: {e}")
            return False

        self._running = True
        self._input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self._output_thread = threading.Thread(target=self._output_loop, daemon=True)
        self._input_thread.start()
        self._output_thread.start()

        logger.info(f"H.264 encoder started using {encoder}")
        return True

    def stop(self) -> None:
        """Stop the encoder."""
        self._running = False

        if self._process is not None:
            if self._process.stdin:
                self._process.stdin.close()
            self._process.terminate()
            try:
                self._process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

        if self._input_thread is not None:
            self._input_thread.join(timeout=1.0)
        if self._output_thread is not None:
            self._output_thread.join(timeout=1.0)

        logger.info("H.264 encoder stopped")

    def encode_frame(self, frame: np.ndarray) -> None:
        """Queue a frame for encoding."""
        if not self._running:
            return
        try:
            self._frame_queue.put_nowait(frame)
        except:
            pass

    def _select_encoder(self) -> Optional[str]:
        """Select the best available H.264 encoder."""
        if not shutil.which("ffmpeg"):
            logger.error("FFmpeg not found in PATH")
            return None

        if self.config.use_hardware:
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
            )
            if "h264_v4l2m2m" in result.stdout:
                return "h264_v4l2m2m"
            logger.info("Hardware encoder not available, using software")

        return "libx264"

    def _build_ffmpeg_command(self, encoder: str) -> list[str]:
        """Build the FFmpeg command line."""
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "warning",
            "-f", "rawvideo",
            "-pixel_format", "bgr24",
            "-video_size", f"{self.preset.width}x{self.preset.height}",
            "-framerate", str(self.preset.fps),
            "-i", "-",
        ]

        if encoder == "h264_v4l2m2m":
            cmd.extend([
                "-c:v", "h264_v4l2m2m",
                "-b:v", self.preset.bitrate,
            ])
        else:
            cmd.extend([
                "-c:v", "libx264",
                "-preset", self.config.preset,
                "-tune", self.config.tune,
                "-b:v", self.preset.bitrate,
                "-g", str(self.config.gop_size),
            ])

        cmd.extend([
            "-f", "h264",
            "-",
        ])

        return cmd

    def _input_loop(self) -> None:
        """Feed frames to FFmpeg stdin."""
        while self._running and self._process is not None:
            try:
                frame = self._frame_queue.get(timeout=0.1)
            except Empty:
                continue

            if self._process.stdin is None:
                break

            resized = self._resize_frame(frame)
            try:
                self._process.stdin.write(resized.tobytes())
            except (BrokenPipeError, OSError):
                logger.warning("FFmpeg stdin closed")
                break

    def _output_loop(self) -> None:
        """Read H.264 data from FFmpeg stdout."""
        buffer_size = 4096
        while self._running and self._process is not None:
            if self._process.stdout is None:
                break

            try:
                data = self._process.stdout.read(buffer_size)
                if not data:
                    break
                self.on_data(data)
            except Exception as e:
                logger.error(f"Error reading FFmpeg output: {e}")
                break

    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame to match encoder preset if needed."""
        import cv2

        h, w = frame.shape[:2]
        if w != self.preset.width or h != self.preset.height:
            return cv2.resize(frame, (self.preset.width, self.preset.height))
        return frame

    @property
    def is_running(self) -> bool:
        """Return whether the encoder is running."""
        return self._running
