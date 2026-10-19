# Kiểm chứng bộ tài liệu

Ngày: **2026-10-19**, múi giờ người dùng Asia/Saigon. Phạm vi: bổ sung tài liệu và đồng bộ hướng dẫn, không triển khai backend/frontend hoặc deploy dịch vụ.

## Cách tái kiểm tra

Cài dependency cho công cụ tài liệu trong virtualenv riêng, rồi chạy:

```powershell
python -m pip install -r scripts/requirements-docs.txt
python scripts/validate-docs.py
git diff --check
```

Trong lượt này dependency được cài vào thư mục tạm, không cài vào application hoặc ghi secret vào repo. Bộ kiểm tra dùng openapi-spec-validator 0.9.0 và OAS30Validator cho examples.

## Kết quả thực chạy

| Kiểm tra | Kết quả |
| --- | --- |
| OpenAPI 3.0.3 | PASS — 45 operations, 61 schemas |
| Ví dụ JSON theo schema | PASS — 129 examples |
| OpenAPI local references | PASS — 436 references |
| Markdown file targets | PASS — 144 targets trong 34 file Markdown |
| Truy vết yêu cầu | PASS — đủ 43 AC của PRD trong test plan; operation liên kết task/AC hợp lệ |
| Skill frontmatter/name | PASS — quick_validate.py cho cả 7 skill đã đồng bộ |
| Diff whitespace | PASS — git diff --check |

Việc sửa SKILL.md được giới hạn trong 7 skill SocialCart có sẵn. Các prompt thiết kế đã được chuyển từ ví dụ Kanban sang flow SocialCart và sửa link local. Không chạy ứng dụng hoặc sửa prototype trong lượt này.

## Giới hạn bằng chứng

Validator chứng minh định dạng OpenAPI, references, examples theo schema và file đích của liên kết local. Nó không kiểm HTTP service thật, route drift của FastAPI, neo heading Markdown, mọi URL bên ngoài, khả năng truy cập provider, hay quyết định nghiệp vụ đã được người dùng nghiệm thu. AC có mặt trong test plan chỉ chứng minh truy vết tài liệu, không chứng minh test đã pass.

Backend/frontend build/test, migrations/seed, Compose, audit trình duyệt P4.5, Facebook/Zalo/Gemini live: **NOT RUN**, vì chưa có application và/hoặc credential phù hợp. EXT-01–03 và UX-01 vẫn được theo dõi trong decision log. Không ghi model thay thế là đã chọn.

Nguồn bên ngoài thực sự đã đọc: [Google deprecations](https://ai.google.dev/gemini-api/docs/deprecations) và [Google changelog](https://ai.google.dev/gemini-api/docs/changelog#september-29-2025), qua HTTPS ngày 2026-10-19. Changelog ghi Gemini 1.5 Pro shutdown ngày 2025-09-29; không chạy inference live.
