# Bộ dựng video EA Bot vàng (ea kit) — bản 1.1, 13/10/2026

Bản 1.1: thêm cảnh `chart` `mode: dca` / `pause` cho dòng DCA; hai cảnh `bot` liền nhau cắt thẳng (không hoà hình).

Kịch bản JSON → video dọc 9:16 (1080×1920) kiểu quảng cáo tài chính cao cấp: nhân vật robot **AURUS** nói (mắt LED chớp, miệng nhảy theo giọng), chữ serif + chữ đậm + nghiêng vàng, biểu đồ nến XAUUSD tự dựng, đồng hồ 24/7, 3 khung H4/H1/M15, SL cứng, checklist, CTA, phụ đề sáng từng chữ, dòng cảnh báo rủi ro, nhạc nền tổng hợp tự hạ khi có giọng, tiếng động. Không cần footage.

Bộ công cụ của skill `video-ea-bot-vang`. Bản gốc nằm trên artifact; skill tải về mỗi lần dựng.

## Tải về

```bash
base64 -d kit_bundle.b64.txt | tar xz        # -> ./kit/...; kit/GOI.txt ghi ngày gói và danh sách file
python3 -c "import skia, sherpa_onnx, soundfile" 2>/dev/null || pip install --break-system-packages -q skia-python sherpa-onnx soundfile
```

Model giọng (~65MB) và máy nghe (~256MB) tự tải từ GitHub releases của sherpa-onnx lần đầu cần, vào `kit/models/` (đổi chỗ bằng biến `EA_MODELS`).

## Script

| File | Việc |
|---|---|
| `ea_render.py` | Lệnh chính: `--describe`, `--sheet`, `--frames`, `--preview --out`, `--out`, `--cover`, `--revoice`, `--force` |
| `ea_voice.py` | Giọng: máy đọc offline, file từng cảnh, một file cả bài (máy nghe chia cảnh), A-roll; mốc từng chữ; bảng cách đọc `DOC`; dải miệng avatar |
| `ea_avatar.py` | Nhân vật AURUS + phông studio; `--sheet` xem 6 trạng thái |
| `ea_text.py` | 8 kiểu chữ (title, headline, box, stack, chapter, checklist, stat, cta), phụ đề, dòng rủi ro, watermark |
| `ea_broll.py` | Cảnh phụ tự dựng: chart (trend/range/sl/drop, dca, pause), mtf, clock; đọc video thật |
| `ea_audio.py` | Nhạc tổng hợp (dark_pad, pulse), tiếng động, trộn + hạ nhạc theo giọng |
| `ea_style.py` | Màu, font, chữ nhiều kiểu (`*nghiêng vàng*`, `{vàng}`, `[đỏ]`) |
| `ea_asr_check.py` | Nghe lại giọng đã dựng, so với lời từng cảnh |
| `ea_pack.py` | Gói lại `kit_bundle.b64.txt` |
| `brand_ea.json` | Nhận diện: sản phẩm, dòng rủi ro, avatar, cách đọc tên riêng, Zalo (không hiện lên hình) |
| `vi_du/kich_ban_mau.json` | Kịch bản mẫu AURUS SENTINEL 9 cảnh |
| `vi_du/kich_ban_dca_atr.json`, `vi_du/brand_elite_dca.json` | Kịch bản mẫu bot DCA âm theo ATR (AURUS ELITE DCA) 9 cảnh, mắt avatar xanh |

## Tài liệu (`kit/docs/`)

| File | Đọc khi |
|---|---|
| `kich_ban.md` | Viết kịch bản: công thức 6 nhịp, luật nội dung, mọi khoá, kiểu chữ |
| `giong_va_nhan_vat.md` | Chọn giọng (offline / Giang thu / vidIQ ElevenLabs / A-roll), sửa cách đọc, đổi màu – tên nhân vật |
| `dang_bai_ea.md` | Gói đăng bài, lưu ý chính sách quảng cáo tài chính |

## Sửa bộ công cụ

Sửa file nào thì đăng lại file đó lên artifact (giữ đường dẫn `kit/...`), rồi `python3 kit/ea_pack.py` và đăng lại `kit_bundle.b64.txt`. Font: Be Vietnam Pro, Playfair Display, IBM Plex Mono (Google Fonts, SIL OFL 1.1).
