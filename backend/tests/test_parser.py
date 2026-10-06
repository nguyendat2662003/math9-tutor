"""Parser đọc đề từ ảnh — dùng LLM giả, không gọi mạng."""

import json

import pytest
from math9_core.agents.parser import ImageNotMathError, ParserAgent
from math9_core.llm.client import LLMClient, LLMResponse, to_data_url
from math9_core.state import ProblemState

STATEMENT = "Cho tam giác ABC vuông tại A, đường cao AH.\na) Chứng minh AB² = BH·BC."


class FakeVLM(LLMClient):
    def __init__(self, payload: dict):
        self.payload = payload
        self.images: list[str] | None = None

    def complete(self, system, user, *, model, max_tokens=4000, temperature=0.2, thinking=False, images=None):
        self.images = images
        return LLMResponse(text=json.dumps(self.payload, ensure_ascii=False), model=model)


@pytest.fixture
def png(tmp_path):
    p = tmp_path / "de.png"
    p.write_bytes(bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a"
        "49444154789c6360000002000100ffff03000006000557bfabd40000000049454e44ae426082"
    ))
    return p


def test_reads_statement_from_image(png):
    llm = FakeVLM({"statement": STATEMENT, "is_math": True, "has_figure": True, "figure_note": "tam giác vuông", "note": ""})
    s = ParserAgent(llm, "fake").run(ProblemState(raw_input="", image_path=str(png)))
    assert s.latex == STATEMENT
    assert s.raw_input == STATEMENT            # đề rỗng -> lấy từ ảnh
    assert s.ocr["has_figure"] is True
    assert llm.images and llm.images[0] == str(png)


def test_user_text_kept_alongside_image(png):
    llm = FakeVLM({"statement": STATEMENT, "is_math": True})
    s = ParserAgent(llm, "fake").run(ProblemState(raw_input="Em chỉ cần ý a", image_path=str(png)))
    assert s.raw_input == "Em chỉ cần ý a" and s.latex == STATEMENT


def test_non_math_image_rejected(png):
    llm = FakeVLM({"statement": "", "is_math": False, "note": "Ảnh chụp phong cảnh"})
    with pytest.raises(ImageNotMathError, match="phong cảnh"):
        ParserAgent(llm, "fake").run(ProblemState(raw_input="", image_path=str(png)))


def test_text_input_skips_llm():
    llm = FakeVLM({})
    s = ParserAgent(llm, "fake").run(ProblemState(raw_input="Giải phương trình x² = 4."))
    assert s.latex == "Giải phương trình x² = 4." and llm.images is None and s.ocr is None


def test_to_data_url(png):
    url = to_data_url(png)
    assert url.startswith("data:image/png;base64,")
    assert to_data_url(url) == url             # đã là data URL thì giữ nguyên
