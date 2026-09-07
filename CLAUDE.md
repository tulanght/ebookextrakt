# Project: ExtractPDF-EPUB

## Mô tả
Pipeline chuyển đổi ~500 ebook động vật/thực vật thành bài viết WordPress để kiếm tiền thụ động (AdSense + Affiliate Amazon/Shopee). Workspace dùng chung với Antigravity IDE (Gemini).

## Stack
- Python + CustomTkinter (Dark Navy theme)
- SQLite, Gemini API (cloud translation), TranslateGemma (local GGUF)
- WordPress REST API, VPS Vultr $12/month (2 vCPU, 4GB RAM)

## Cấu trúc thư mục
```
ExtractPDF-EPUB/
├── src/                  ← Source code (Antigravity phụ trách)
├── tests/                ← Unit tests (Antigravity phụ trách)
├── docs/seo/             ← SEO knowledge docs (Claude phụ trách)
├── .claude/commands/     ← Claude slash commands (SEO/content)
└── scripts/              ← Scripts tiện ích
```

## Phân công AI

### Claude (tôi) — SEO & Content Pipeline
- **KHÔNG** đụng vào code implementation
- **KHÔNG** dùng các dev commands (đã có Antigravity lo)
- Tư vấn SEO strategy, review bài viết, AdSense recovery
- Slash commands dưới đây

### Antigravity (Gemini) — Code Implementation
- Toàn bộ code trong `src/`, `tests/`
- Workflow: new-requirement → design → execute-plan → code-review → debug
- Đã tích hợp aidevkittool skills

## Claude Slash Commands (SEO/Content)
| Command | Mục đích |
|---------|----------|
| `/seo-audit` | Audit on-page SEO cho từng bài |
| `/content-optimize` | Tối ưu bài dịch từ ebook thành web content |
| `/wp-publish` | Publish draft lên WordPress REST API |
| `/wp-update` | Update bài cũ không đổi URL |
| `/keyword-plan` | Lập kế hoạch keyword clusters |
| `/content-facebook` | Convert bài sang format Facebook Page/Group |
| `/internal-linking` | Xây dựng internal link network |
| `/schema-markup` | Generate JSON-LD structured data |
| `/site-health` | Kiểm tra sức khỏe WordPress/VPS |
| `/seo-bulk-check` | Bulk audit nhiều bài, xuất bảng ưu tiên |

## Knowledge Docs (docs/seo/)
- `checklist-on-page.md` — 50+ point SEO checklist
- `wordpress-api-guide.md` — WP REST API integration
- `adsense-recovery-guide.md` — Kế hoạch 4 tuần reapply AdSense
- `content-strategy-animals.md` — Chiến lược content 3-tier + KPIs

## Business Context
- **AdSense**: Đang bị tắt → cần reapply (cần 30+ bài 1000+ từ)
- **Facebook**: Page 200k likes + Group 400k members (distribution)
- **Content pipeline**: Ebook → Extract → Translate → 3 variants → Publish

## KPIs
- Tháng 1: 30+ bài 1000+ từ → reapply AdSense
- Tháng 3: 100+ bài, 20k organic sessions/tháng, $50-100/tháng
- Tháng 6: 200+ bài, 50k sessions/tháng, $200-500/tháng

## Giao tiếp
- User giao tiếp bằng tiếng Việt
- Claude phản hồi bằng tiếng Việt
- Code và tên biến viết bằng tiếng Anh
