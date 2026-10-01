# Adapter nguồn

M��i site một file. Khi có link mới, thêm một class kế thừa `SourceAdapter`.

## Khung mẫu

```python
from .base import DocumentRef, SourceAdapter

class SoGdHaNoiAdapter(SourceAdapter):
    name = "sogd-hanoi"
    base_url = "https://..."
    verified_public = True      # chỉ bật khi đã xác nhận: công khai, không tường phí

    def discover(self) -> list[DocumentRef]:
        # 1. tải trang danh sách
        # 2. trích link PDF/DOC
        # 3. suy ra year, province, kind từ tiêu đề hoặc URL
        ...
```

## Kiểm tra trước khi bật `verified_public`

- [ ] Truy cập được khi chưa đăng nhập, ở chế độ ẩn danh
- [ ] Không có tường phí, không đòi tài khoản
- [ ] `robots.txt` không cấm đường dẫn này
- [ ] Không phải bản scan SGK hoặc SBT
- [ ] Có ghi rõ nguồn để trích dẫn lại trong `DocumentRef.meta`

Pipeline **từ chối chạy** adapter có `verified_public = False`.
