"""Lớp trừu tượng cho LLM + chính sách chọn model theo vai trò và độ khó.

Cách tách này cho phép chạy hybrid: 75% lưu lượng dùng model local (gần như
miễn phí biên), chỉ bài khó mới gọi API model mạnh.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""
    finish_reason: str = ""

    def json(self) -> dict:
        """Bóc ```json fence nếu có rồi parse."""
        t = self.text.strip()
        if t.startswith("```"):
            t = t.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(t)


class LLMClient(ABC):
    @abstractmethod
    def complete(
        self, system: str, user: str, *, model: str, max_tokens: int = 4000,
        temperature: float = 0.2, thinking: bool = False, images: list[str] | None = None,
    ) -> LLMResponse: ...

    def stream(
        self, system: str, messages: list[dict], *, model: str, max_tokens: int = 4000,
        temperature: float = 0.3, usage: dict | None = None,
    ) -> Iterator[str]:
        """Hội thoại nhiều lượt, trả từng đoạn chữ. `usage` (nếu truyền) được điền token lúc xong.

        Mặc định: gọi `complete` với lượt cuối và trả một lần — đủ cho client chưa hỗ trợ stream
        và cho LLM giả trong test. Client thật ghi đè để trả dần.
        """
        history = "\n\n".join(f"[{m['role']}]\n{m['content']}" for m in messages[:-1])
        user = (history + "\n\n[user]\n" if history else "") + messages[-1]["content"]
        resp = self.complete(system, user, model=model, max_tokens=max_tokens, temperature=temperature)
        if usage is not None:
            usage.update(input=resp.tokens_in, output=resp.tokens_out, model=resp.model or model)
        yield resp.text


class OpenAICompatClient(LLMClient):
    """Endpoint tương thích OpenAI: api.openai.com, hoặc vLLM / Ollama / SGLang local."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None, timeout: float = 120.0):
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.timeout = timeout

    def complete(self, system, user, *, model, max_tokens=4000, temperature=0.2, thinking=False, images=None):
        import httpx

        content: str | list[dict] = user
        if images:
            content = [{"type": "text", "text": user}] + [
                {"type": "image_url", "image_url": {"url": to_data_url(i)}} for i in images
            ]
        body: dict = {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}],
            "max_completion_tokens": max_tokens,
        }
        self._set_temperature(body, model, temperature)
        headers = self._headers()

        r = httpx.post(f"{self.base_url}/chat/completions", json=body, headers=headers, timeout=self.timeout)
        if r.status_code == 400 and "temperature" in r.text and "temperature" in body:
            self._no_temperature.add(model)          # nhớ lại: lần sau khỏi tốn một request bị từ chối
            body.pop("temperature")
            r = httpx.post(f"{self.base_url}/chat/completions", json=body, headers=headers, timeout=self.timeout)
        if r.status_code >= 400:
            raise RuntimeError(f"LLM trả về HTTP {r.status_code} (model={model}): {r.text[:500]}")
        data = r.json()
        usage = data.get("usage") or {}
        choice = data["choices"][0]
        text = choice["message"].get("content") or ""
        finish = choice.get("finish_reason", "")
        if not text.strip():
            # Model kiểu reasoning có thể tiêu hết max_completion_tokens vào phần suy nghĩ
            reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens")
            raise RuntimeError(
                f"LLM trả về rỗng (model={model}, finish_reason={finish}, "
                f"completion_tokens={usage.get('completion_tokens')}, reasoning_tokens={reasoning}). "
                "Thường do max_tokens quá thấp cho model reasoning."
            )
        return LLMResponse(
            text=text,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            model=data.get("model", model),
            finish_reason=finish,
        )

    # Model reasoning (vd gpt-5.x) chỉ nhận temperature mặc định: gửi là bị HTTP 400.
    _no_temperature: set[str] = set()

    def _set_temperature(self, body: dict, model: str, temperature: float) -> None:
        if temperature != 1.0 and model not in self._no_temperature:
            body["temperature"] = temperature

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def stream(self, system, messages, *, model, max_tokens=4000, temperature=0.3, usage=None):
        """Stream thật qua SSE của /chat/completions — học sinh thấy chữ hiện dần, không phải chờ."""
        import httpx

        body: dict = {
            "model": model, "stream": True, "stream_options": {"include_usage": True},
            "messages": [{"role": "system", "content": system}, *messages],
            "max_completion_tokens": max_tokens,
        }
        self._set_temperature(body, model, temperature)
        for attempt in (1, 2):
            with httpx.stream("POST", f"{self.base_url}/chat/completions", json=body,
                              headers=self._headers(), timeout=self.timeout) as r:
                if r.status_code == 400 and attempt == 1 and "temperature" in body:
                    if "temperature" in r.read().decode(errors="ignore"):
                        self._no_temperature.add(model)
                        body.pop("temperature")
                        continue
                if r.status_code >= 400:
                    raise RuntimeError(f"LLM trả về HTTP {r.status_code} (model={model}): {r.read().decode(errors='ignore')[:500]}")
                got_text = False
                for line in r.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    if chunk.get("usage") and usage is not None:
                        u = chunk["usage"]
                        usage.update(input=u.get("prompt_tokens", 0), output=u.get("completion_tokens", 0),
                                     model=chunk.get("model", model))
                    for ch in chunk.get("choices") or []:
                        piece = (ch.get("delta") or {}).get("content")
                        if piece:
                            got_text = True
                            yield piece
                if not got_text:
                    raise RuntimeError(f"LLM không trả chữ nào (model={model}) — có thể do max_tokens quá thấp cho model reasoning")
                return


LocalOpenAICompatClient = OpenAICompatClient


def load_env(path: str | os.PathLike | None = None) -> None:
    """Nạp .env vào os.environ (không ghi đè biến đã có). Chịu được khoảng trắng quanh '='.

    Mặc định tìm `.env` ở thư mục gốc dự án, không phụ thuộc thư mục hiện hành."""
    from pathlib import Path

    p = Path(path) if path else Path(__file__).resolve().parents[4] / ".env"
    if not p.exists():
        p = Path(".env")
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def client_from_env() -> LLMClient:
    """Chọn client theo biến môi trường: ưu tiên OPENAI_API_KEY, rồi tới LOCAL_LLM_URL."""
    load_env()
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAICompatClient()
    return OpenAICompatClient(base_url=os.environ.get("LOCAL_LLM_URL", "http://localhost:8001/v1"), api_key="")


def default_model() -> str:
    """Tên model mặc định. `.env` hiện đặt tên model trong MODEL_API_KEY (tên biến gây hiểu nhầm)."""
    load_env()
    return os.environ.get("MODEL_NAME") or os.environ.get("MODEL_API_KEY") or "gpt-4.1-mini"


def to_data_url(image: str | os.PathLike) -> str:
    """Nhận data URL sẵn có, hoặc đường dẫn file ảnh -> data URL base64."""
    import base64
    import mimetypes
    from pathlib import Path

    s = str(image)
    if s.startswith("data:"):
        return s
    p = Path(s)
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


# --- chính sách định tuyến model -----------------------------------------

#: (vai trò, độ khó) -> tên model. Sửa ở ĐÂY, không rải rác trong agent.
MODEL_POLICY: dict[tuple[str, int], str] = {
    ("parser", 1): "api:vision",
    ("parser", 2): "api:vision",
    ("parser", 3): "api:vision",
    ("router", 1): "local:qwen3-8b",
    ("router", 2): "local:qwen3-8b",
    ("router", 3): "local:qwen3-8b",
    ("draftsman", 1): "local:qwen3-14b",
    ("draftsman", 2): "local:qwen3-32b",
    ("draftsman", 3): "local:qwen3-32b",
    ("solver", 1): "local:qwen3-32b",
    ("solver", 2): "api:strong",
    ("solver", 3): "api:strong",
    ("critic", 1): "local:qwen3-14b",
    ("critic", 2): "local:qwen3-32b",
    ("critic", 3): "api:strong",
    ("pedagogue", 1): "local:qwen3-8b",
    ("pedagogue", 2): "local:qwen3-8b",
    ("pedagogue", 3): "local:qwen3-8b",
}


def pick_model(role: str, difficulty: int) -> str:
    return MODEL_POLICY.get((role, difficulty), "api:strong")
