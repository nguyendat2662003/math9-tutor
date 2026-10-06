"""Tầng tải tài liệu: tôn trọng robots.txt, giới hạn tốc độ, có cache và resume.

Ba nguyên tắc bắt buộc:
1. Đọc robots.txt trước, tuân thủ. Không có ngoại lệ.
2. Giới hạn tốc độ theo domain — mặc định 1 request/2 giây. Cổng thông tin của
   Sở GD&ĐT thường chạy trên hạ tầng yếu, crawl nhanh là gây hại thật.
3. Cache theo hash URL. Chạy lại pipeline KHÔNG được tải lại từ đầu.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

log = logging.getLogger(__name__)

USER_AGENT = "math9-tutor-research/0.1 (+liên hệ: your-email@example.com)"


@dataclass
class FetchConfig:
    cache_dir: Path = Path("data/raw/cache")
    delay_per_domain: float = 2.0
    timeout: float = 30.0
    max_bytes: int = 40 * 1024 * 1024
    respect_robots: bool = True
    allowed_content_types: tuple[str, ...] = (
        "text/html", "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    )
    #: Chặn cứng — không crawl site có tường phí hoặc yêu cầu đăng nhập.
    blocked_hosts: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class Fetched:
    url: str
    path: Path
    content_type: str
    from_cache: bool
    status: int


class Fetcher:
    def __init__(self, cfg: FetchConfig | None = None):
        self.cfg = cfg or FetchConfig()
        self.cfg.cache_dir.mkdir(parents=True, exist_ok=True)
        self._last: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser] = {}
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT}, follow_redirects=True,
            timeout=self.cfg.timeout,
        )

    # -- robots ----------------------------------------------------------

    def _allowed(self, url: str) -> bool:
        host = urlparse(url).netloc
        if any(b in host for b in self.cfg.blocked_hosts):
            log.warning("Bỏ qua host bị chặn: %s", host)
            return False
        if not self.cfg.respect_robots:
            return True
        if host not in self._robots:
            rp = RobotFileParser()
            rp.set_url(f"{urlparse(url).scheme}://{host}/robots.txt")
            try:
                rp.read()
            except Exception:
                rp.allow_all = True
            self._robots[host] = rp
        return self._robots[host].can_fetch(USER_AGENT, url)

    def _throttle(self, url: str) -> None:
        host = urlparse(url).netloc
        wait = self.cfg.delay_per_domain - (time.time() - self._last.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        self._last[host] = time.time()

    # -- cache -----------------------------------------------------------

    def _cache_path(self, url: str) -> Path:
        h = hashlib.blake2b(url.encode(), digest_size=16).hexdigest()
        return self.cfg.cache_dir / h[:2] / h

    def fetch(self, url: str) -> Fetched | None:
        cp = self._cache_path(url)
        meta = cp.with_suffix(".json")
        if cp.exists() and meta.exists():
            m = json.loads(meta.read_text())
            return Fetched(url, cp, m["content_type"], True, m["status"])

        if not self._allowed(url):
            log.warning("robots.txt không cho phép: %s", url)
            return None

        self._throttle(url)
        try:
            r = self._client.get(url)
        except httpx.HTTPError as e:
            log.error("Lỗi tải %s: %s", url, e)
            return None

        ct = r.headers.get("content-type", "").split(";")[0].strip()
        if ct and not any(ct.startswith(a) for a in self.cfg.allowed_content_types):
            log.info("Bỏ qua content-type %s tại %s", ct, url)
            return None
        if len(r.content) > self.cfg.max_bytes:
            log.warning("File quá lớn, bỏ qua: %s", url)
            return None

        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_bytes(r.content)
        meta.write_text(json.dumps(
            {"url": url, "content_type": ct, "status": r.status_code,
             "fetched_at": time.time()}, ensure_ascii=False))
        return Fetched(url, cp, ct, False, r.status_code)

    def close(self) -> None:
        self._client.close()
