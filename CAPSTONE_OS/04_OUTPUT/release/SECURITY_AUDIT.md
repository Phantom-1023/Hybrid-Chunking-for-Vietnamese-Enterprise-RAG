# Security Audit trước khi push GitHub

## Kết luận nhanh

Repo chưa nên push ngay nếu chưa kiểm tra staged/tracked files. Audit phát hiện `.env` local có chứa secret pattern đã được mask, cùng nhiều runtime artifacts như `chroma_db/`, cache, log và dữ liệu tạm. `.gitignore` đã được bổ sung để giảm rủi ro, nhưng cần kiểm tra lại trong Git repo thật trước khi commit.

## Phát hiện bảo mật

| Mức độ | Hạng mục | Kết quả | Hành động |
|---|---|---|---|
| Critical | `.env` | Tồn tại và có secret/API key pattern đã mask | Không được commit. Phải được ignore. |
| Critical | `.env` tracked status | Không xác định vì thư mục hiện tại chưa phải Git repo | Khi vào repo thật, chạy `git ls-files .env`. |
| High | `chroma_db/` | Tồn tại runtime vector database | Không push mặc định. Có thể tái tạo bằng `python main.py --mode index`. |
| High | `data/raw/`, `data/temp/` | Tồn tại dữ liệu local/runtime | Không push nếu không có quyết định của team. |
| Medium | `__pycache__/`, `*.pyc` | Tồn tại cache Python | Không push. |
| Medium | `*.log` | Tồn tại log Streamlit/runtime | Không push. |
| Medium | `.streamlit/secrets.toml` | Đã thêm vào `.gitignore` | Không commit nếu xuất hiện. |
| Low | `.env.example` | Tồn tại, dùng placeholder | Được push nếu không có key thật. |
| Low | `benchmark_results.csv` | Kết quả benchmark-lite thật | Được push. |
| Low | PPTX output | File slide Review 2 | Được push. |

## Secret scan đã mask

Các pattern nhạy cảm được phát hiện nhưng không in giá trị thật:

- `.env`: generic token assignment.
- `.env`: `DEEPSEEK_API_KEY` pattern.
- `.env`: OpenAI/project key pattern.
- `.env`: `GEMINI_API_KEY` pattern.
- `.env`: Google API key pattern.
- `.env.example`: có key-name placeholders, cần giữ dạng placeholder.
- Một số file code/docs có tên biến API key, không phải secret value.

## File/thư mục cần loại khỏi commit

- `.env`
- `*.env` ngoại trừ `.env.example`
- `chroma_db/`
- `data/raw/`
- `data/temp/`
- `__pycache__/`
- `*.pyc`
- `*.log`
- `.venv/`, `venv/`
- `node_modules/`
- `.streamlit/secrets.toml`

## Git status hiện tại

Các lệnh Git trả về lỗi vì thư mục hiện tại chưa phải Git repository:

```text
fatal: not a git repository (or any of the parent directories): .git
```

Do đó audit không thể xác nhận `.env` đã từng bị track hay chưa. Khi team clone/init repo thật, phải kiểm tra lại trước khi add/commit.

## Khuyến nghị push

Chưa push trực tiếp từ thư mục này. Hãy chuyển vào Git repo đúng của team hoặc khởi tạo repo, kiểm tra `.gitignore`, sau đó chỉ add file an toàn bằng lệnh rõ ràng. Nếu `git status --short` cho thấy `.env`, `chroma_db/`, log, cache hoặc data raw/temp xuất hiện trong staged files thì phải gỡ ra trước khi commit.
