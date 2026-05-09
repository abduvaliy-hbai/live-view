import os
import time
from urllib.parse import quote

os.environ.setdefault("QT_QPA_FONTDIR", "/usr/share/fonts/truetype/dejavu")

import cv2
from dotenv import load_dotenv


def env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_rtsp_url() -> str:
    load_dotenv()

    custom_url = os.getenv("HIKVISION_RTSP_URL", "").strip()
    if custom_url:
        return custom_url

    ip = os.getenv("HIKVISION_IP", "").strip()
    username = os.getenv("HIKVISION_USERNAME", "").strip()
    password = os.getenv("HIKVISION_PASSWORD", "").strip()
    port = os.getenv("HIKVISION_RTSP_PORT", "554").strip()
    channel = os.getenv("HIKVISION_CHANNEL", "101").strip()

    missing = [
        name
        for name, value in {
            "HIKVISION_IP": ip,
            "HIKVISION_USERNAME": username,
            "HIKVISION_PASSWORD": password,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required .env values: {', '.join(missing)}")

    safe_username = quote(username, safe="")
    safe_password = quote(password, safe="")
    return (
        f"rtsp://{safe_username}:{safe_password}@{ip}:{port}"
        f"/Streaming/Channels/{channel}"
    )


def open_stream(rtsp_url: str) -> cv2.VideoCapture:
    # FFMPEG usually handles Hikvision RTSP streams best through OpenCV.
    capture = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return capture


def main() -> None:
    load_dotenv()
    rtsp_url = build_rtsp_url()
    enable_motion_tracking = env_flag("ENABLE_MOTION_TRACKING", True)
    min_motion_area = int(os.getenv("MIN_MOTION_AREA", "900"))
    window_width = int(os.getenv("WINDOW_WIDTH", "1980"))
    window_height = int(os.getenv("WINDOW_HEIGHT", "1200"))
    window_name = "Hikvision Live View"
    background = cv2.createBackgroundSubtractorMOG2(
        history=500,
        varThreshold=32,
        detectShadows=True,
    )

    print("Connecting to Hikvision camera...")
    print("Press q in the video window to quit.")

    capture = open_stream(rtsp_url)
    last_frame_time = time.time()
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, window_width, window_height)

    while True:
        ok, frame = capture.read()

        if not ok:
            print("Stream unavailable. Reconnecting in 3 seconds...")
            capture.release()
            time.sleep(3)
            capture = open_stream(rtsp_url)
            continue

        now = time.time()
        fps = 1.0 / max(now - last_frame_time, 0.001)
        last_frame_time = now

        if enable_motion_tracking:
            mask = background.apply(frame)
            _, mask = cv2.threshold(mask, 244, 255, cv2.THRESH_BINARY)
            mask = cv2.erode(mask, None, iterations=1)
            mask = cv2.dilate(mask, None, iterations=2)

            contours, _ = cv2.findContours(
                mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            for contour in contours:
                if cv2.contourArea(contour) < min_motion_area:
                    continue
                x, y, width, height = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 180, 255), 2)
                cv2.putText(
                    frame,
                    "motion",
                    (x, max(y - 8, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 180, 255),
                    2,
                    cv2.LINE_AA,
                )

        cv2.putText(
            frame,
            f"Live | FPS: {fps:.1f}",
            (12, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
