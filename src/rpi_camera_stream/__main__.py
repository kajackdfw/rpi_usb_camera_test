"""Entry point for the camera streaming server."""

import argparse
import sys

from .app import run_server
from .config import CameraConfig, Config, ServerConfig


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Raspberry Pi USB Camera Streaming Server"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to listen on (default: 5000)",
    )
    parser.add_argument(
        "--device",
        default="/dev/video0",
        help="Camera device path (default: /dev/video0)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Capture width (default: 1280)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Capture height (default: 720)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Capture frame rate (default: 30)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Enable local preview window",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    args = parser.parse_args()

    config = Config(
        camera=CameraConfig(
            device=args.device,
            width=args.width,
            height=args.height,
            fps=args.fps,
        ),
        server=ServerConfig(
            host=args.host,
            port=args.port,
            debug=args.debug,
        ),
        enable_preview=args.preview,
    )

    try:
        run_server(config)
        return 0
    except KeyboardInterrupt:
        print("\nShutting down...")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
