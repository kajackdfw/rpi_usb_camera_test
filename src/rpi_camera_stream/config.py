"""Configuration settings for the camera streaming server."""

from dataclasses import dataclass, field


@dataclass
class CameraConfig:
    """Camera capture configuration."""

    device: str = "/dev/video0"
    width: int = 1280
    height: int = 720
    fps: int = 30
    fourcc: str = "MJPG"


@dataclass
class H264Config:
    """H.264 encoder configuration."""

    bitrate: str = "2M"
    preset: str = "ultrafast"
    tune: str = "zerolatency"
    gop_size: int = 30
    use_hardware: bool = True


@dataclass
class QualityPreset:
    """Video quality preset."""

    width: int
    height: int
    fps: int
    bitrate: str


QUALITY_PRESETS: dict[str, QualityPreset] = {
    "low": QualityPreset(640, 480, 15, "500k"),
    "medium": QualityPreset(1280, 720, 30, "1M"),
    "high": QualityPreset(1920, 1080, 30, "2M"),
}


@dataclass
class ServerConfig:
    """Server configuration."""

    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    cors_origins: list[str] = field(default_factory=lambda: ["*"])


@dataclass
class Config:
    """Application configuration."""

    camera: CameraConfig = field(default_factory=CameraConfig)
    h264: H264Config = field(default_factory=H264Config)
    server: ServerConfig = field(default_factory=ServerConfig)
    enable_preview: bool = False
