import os
import re
import logging
from dataclasses import dataclass
from typing import Callable, Optional

from app.common.config import DOWNLOAD_DIR, LOG_PATH

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    success: bool
    filepath: Optional[str] = None
    title: Optional[str]    = None
    error: Optional[str]    = None


_YT_PATTERN = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)"
    r"[\w\-]{11}"
)


def _validate_url(url: str) -> bool:
    return bool(_YT_PATTERN.search(url))


def _sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:200]


def _is_duplicate(filepath: str) -> bool:
    return os.path.isfile(filepath) and os.path.getsize(filepath) > 0


def download_mp3(
    url: str,
    on_progress: Optional[Callable[[str], None]] = None,
) -> DownloadResult:
    """
    YouTube URL을 받아 MP3로 다운로드한다.
    웹·Discord 양쪽에서 이 함수만 호출한다.

    on_progress 콜백 단계:
        "analyzing"        → 메타데이터 추출 중
        "duplicate"        → 중복 파일, 즉시 반환
        "downloading:XX%"  → 다운로드 진행률
        "converting"       → ffmpeg MP3 변환 중
    """
    if not _validate_url(url):
        msg = f"유효하지 않은 URL: {url}"
        logger.warning(msg)
        return DownloadResult(success=False, error=msg)

    def _notify(stage: str):
        if on_progress:
            on_progress(stage)

    def _hook(d: dict):
        status = d.get("status")
        if status == "downloading":
            pct = d.get("_percent_str", "?").strip()
            _notify(f"downloading:{pct}")
        elif status == "finished":
            _notify("converting")

    import yt_dlp

    probe_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
    }

    try:
        _notify("analyzing")
        with yt_dlp.YoutubeDL(probe_opts) as ydl:
            info  = ydl.extract_info(url, download=False)
            title = info.get("title", "unknown")
            safe  = _sanitize_filename(title)
            dest  = os.path.join(DOWNLOAD_DIR, safe + ".mp3")

        if _is_duplicate(dest):
            _notify("duplicate")
            logger.info(f"중복 — 기존 파일 반환: {dest}")
            return DownloadResult(success=True, filepath=dest, title=title)

        dl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(DOWNLOAD_DIR, safe + ".%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "progress_hooks": [_hook],
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(dl_opts) as ydl2:
            ydl2.download([url])

        logger.info(f"다운로드 완료: {dest}")
        return DownloadResult(success=True, filepath=dest, title=title)

    except Exception as e:
        msg = str(e)
        logger.error(f"다운로드 실패 [{url}]: {msg}")
        return DownloadResult(success=False, error=msg)
