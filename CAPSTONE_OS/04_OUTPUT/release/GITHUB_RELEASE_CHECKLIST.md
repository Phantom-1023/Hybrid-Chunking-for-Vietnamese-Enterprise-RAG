# GitHub Release Checklist

## 1. File được phép push

- Source code cần cho MVP: `main.py`, `src/`, `config/`, `ui/`, `scripts/`.
- Dependency/config mẫu: `requirements.txt`, `.env.example`.
- Tài liệu dự án trong `CAPSTONE_OS/`.
- `README.md`.
- `.gitignore`.
- `benchmark_results.csv`.
- PowerPoint Review 2: `CAPSTONE_OS/04_OUTPUT/slides/RAG_ENTERPRISE_REVIEW2.pptx`.
- Build/review notes không chứa secret.

## 2. File không được push

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
- Tài liệu cá nhân không liên quan bài nộp.
- Bất kỳ file nào chứa API key/token thật.

## 3. Lệnh kiểm tra Git

```powershell
git status --short
git remote -v
git branch --show-current
git check-ignore -v .env
git ls-files .env
```

Kỳ vọng:

- `.env` phải được ignore.
- `git ls-files .env` không được trả ra `.env`.
- Không có `chroma_db/`, log, cache, raw/temp data trong staged files.

## 4. Tạo branch release

Nếu repo đã tồn tại:

```powershell
git checkout -b review2-mvp-demo
```

Nếu thư mục chưa phải Git repo:

```powershell
git init
git remote add origin <TEAM_REPO_URL>
git checkout -b review2-mvp-demo
```

## 5. Add file an toàn

Ưu tiên add rõ ràng:

```powershell
git add .gitignore README.md requirements.txt main.py config src ui scripts benchmark_results.csv .env.example
git add CAPSTONE_OS/00_CONTEXT CAPSTONE_OS/01_COMMAND CAPSTONE_OS/02_KNOWLEDGE CAPSTONE_OS/04_OUTPUT
git status --short
```

Nếu lỡ stage file nguy hiểm:

```powershell
git restore --staged .env
git restore --staged chroma_db
git restore --staged data/raw
git restore --staged data/temp
git restore --staged __pycache__
```

Sau đó kiểm tra lại:

```powershell
git status --short
git ls-files .env
```

## 6. Commit

Chỉ commit sau khi người phụ trách kiểm tra danh sách staged files:

```powershell
git commit -m "Prepare Review 2 MVP demo release"
```

## 7. Push branch

Chỉ push sau khi đã được duyệt:

```powershell
git push -u origin review2-mvp-demo
```

## 8. Checklist duyệt cuối

- `.env` không bị staged/tracked.
- Không có API key/token thật trong README, docs, slides.
- `benchmark_results.csv` là benchmark-lite thật, không fake.
- Slide có ghi rõ evaluation-lite chưa phải full RAGAS.
- README có hướng dẫn setup bằng placeholder.
- `chroma_db/` không được push.
- Log/cache/runtime data không được push.
- Branch đúng tên: `review2-mvp-demo`.
