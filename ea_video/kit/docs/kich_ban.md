# Viết kịch bản video EA (`kich_ban.json`)

## Công thức 6 nhịp (rút từ video mẫu NHK Academy, ~35–45 giây)

| Nhịp | Thời lượng | Lời | Hình + chữ |
|---|---|---|---|
| 1. Hook nỗi đau | 3–5s | Câu hỏi đúng nỗi đau khách: bận, không canh chart, sợ cảm xúc | `bot` + `title` serif 3 dòng: `[TỪ ĐỎ]` + `{câu hỏi vàng?}` |
| 2. Ngộ nhận / vấn đề | 5–8s | "Nhiều người nghĩ… nhưng…" | `chart` có `blur` + `headline` 2 dòng + 3–4 `bullets` hiện đúng lúc nói |
| 3. Đảo chiều | 2–4s | Một câu ngắn lật lại ("Bận không có nghĩa là bỏ lỡ cơ hội") | `bot` + `box` các cụm thay nhau, cụm cuối `*nghiêng vàng*` |
| 4. Giải pháp | 4–6s | Tên EA + nó là gì (1 câu) | `bot` + `stack` (nhãn nhỏ + 3 dòng chữ đậm, dòng cuối `{vàng}`) |
| 5. Tính năng đánh số | 3–4 cảnh × 3–5s | Mỗi cảnh một tính năng thật | `clock` / `mtf` / `chart` `mode: sl` + `chapter` "01 / …"; gom lại bằng `checklist` |
| 6. CTA | 4–6s | Hành động cụ thể, không có số điện thoại | `bot` `mood: smile` + `cta`, `hold` 1–1,5s |

Dòng EA DCA / lưới: nói thẳng là DCA, có một cảnh nói rủi ro (`box` "DCA VẪN CÓ *Rủi Ro*"), tính năng minh hoạ bằng `chart` `mode: dca` / `pause`. Ví dụ: `kit/vi_du/kich_ban_dca_atr.json`.

Một cảnh = một ý = một câu `say`. Chữ trên hình **là từ khoá của lời**, không chép nguyên câu (phụ đề đã chép).

## Luật nội dung (bộ dựng tự soát, `[LOI]` chặn bản xuất)

- Chỉ nói **tính năng và cách EA làm việc** (khung thời gian, SL cứng, lot theo % vốn, chạy 24/7 trên MT5/VPS). Không hứa lợi nhuận, không % lãi/tháng, không "an toàn tuyệt đối", "không bao giờ cháy", "chắc thắng", "x2 tài khoản".
- Tính năng lấy từ lời Giang / file EA / ghi chú sản phẩm. Thiếu thì ghi `[CẦN XÁC NHẬN]` và hỏi, không tự bịa (ví dụ "bản dùng thử", "miễn phí", "backtest 5 năm").
- Không hình kết quả giả (lịch sử lệnh, số dư, % lợi nhuận). Biểu đồ trong bộ dựng là minh hoạ, không phải kết quả.
- Số điện thoại không lên hình; CTA là câu không số ("NHẮN ZALO", "BẤM TÌM HIỂU THÊM"). Số / link để ở mô tả và bình luận ghim.
- Dòng cảnh báo rủi ro luôn bật (`"disclaimer": true`, chữ trong `brand_ea.json`).

## Khoá của kịch bản

```json
{
 "title": "tên video",
 "fps": 30,
 "brand": "brand_ea.json",                 // bỏ trống = kit/brand_ea.json
 "voice": {"engine": "offline", "speed": 1.0},
 "music": {"style": "dark_pad", "volume": 0.15},   // "pulse" | "none" | {"file": "nhac.mp3"}
 "disclaimer": true, "karaoke": true, "caption_words": 4, "watermark": "AURUS SENTINEL",
 "scenes": [ ... ]
}
```

Mỗi cảnh:

| Khoá | Ý nghĩa |
|---|---|
| `visual` | `bot` (avatar nói), `chart`, `mtf`, `clock`, `video` (file thật, phủ tối), `aroll` (clip người thật / AI avatar có tiếng) |
| `say` | Lời của cảnh, viết như phụ đề (có dấu, số, "24/7", "MT5"). Máy đọc tự đổi cách đọc theo `doc` |
| `mood` | `neutral` / `smile` / `focus` (chỉ `bot`) |
| `shot` | `medium` / `close` / `wide`; bỏ trống thì cảnh `bot` liền nhau tự đổi medium ↔ close |
| `look` | `left` / `right` / `down` / `center`; bỏ trống thì avatar tự nhìn về phía chữ |
| `mode` | `chart`: `trend` / `range` / `sl` / `drop`, và cho dòng DCA: `dca` (lưới L1…L5 cách nhau theo ATR, giãn khi biến động mạnh, "CHỐT CẢ RỔ" khi hồi) / `pause` (vùng đỏ "KHÔNG HỒI · DỪNG DCA" khi giá chạy một mạch, "DCA LẠI KHI HỒI"); `seed` đổi hình nến (`dca` mặc định 45, `pause` 26 — đã chọn sẵn cho đẹp); `labels` đổi chữ nhãn: `{"pause": ..., "resume": ..., "tp": ..., "gap": ...}` |
| `notes` | `mtf`: 3 nhãn (mặc định XU HƯỚNG / VÙNG HỒI / TÍN HIỆU) |
| `center`, `sub` | `clock`: chữ giữa ("24/7") và dòng dưới |
| `file`, `start` | `video`: file + giây bắt đầu. `aroll`: `file`, `in`, `out` (giây) |
| `blur`, `dim` | 0..1, làm mờ / tối cảnh phụ để chữ nổi |
| `pip` | `true`: avatar nhỏ trong vòng tròn góc phải trên cảnh phụ (vẫn nói) |
| `hold` | giữ cảnh thêm N giây sau lời (CTA, checklist dài) |
| `dur` | cảnh không lời: dài bao lâu |
| `caption` | `false` để tắt phụ đề cảnh đó |
| `voice_file` | với `"engine": "files"`: file giọng của cảnh |
| `text` | một kiểu chữ hoặc danh sách kiểu chữ (bảng dưới) |

## Kiểu chữ (`text`)

Đánh dấu trong chuỗi: `*chữ*` nghiêng serif vàng · `{chữ}` vàng · `[chữ]` đỏ.

| `style` | Khoá | Dùng cho |
|---|---|---|
| `title` | `lines` (2–3 dòng), `size`, `y` | Hook: serif lớn giữa màn hình, gạch vàng dưới dòng 1 |
| `headline` | `lines`, `bullets`, `size` | Vấn đề: tiêu đề góc trái trên + gạch đầu dòng |
| `box` | `items` | Đảo chiều: hộp lower-third, các cụm thay nhau |
| `stack` | `label`, `lines` | Giải pháp: nhãn nhỏ + chữ xếp chồng bên trái |
| `chapter` | `num`, `label`, `lines` | Tính năng đánh số trên cảnh phụ |
| `checklist` | `title`, `items` | Tóm tính năng (tối đa 4–5 dòng) |
| `stat` | `value`, `label` | Một con số tính năng ("24/7", "3 khung") — không dùng cho lợi nhuận |
| `cta` | `label`, `lines` | Kêu gọi cuối video |

Thời điểm: `"at"` = giây từ đầu cảnh, hoặc `"@cụm lời"` = lúc cụm đó được nói. `bullets` / `items` tự khớp vào lúc lời nói tới từ đó (viết chữ trùng với lời là khớp); muốn ép thì `{"text": "...", "at": "@..."}`. `"until"` để tắt chữ sớm.

## Ví dụ đầy đủ

`kit/vi_du/kich_ban_mau.json` (AURUS SENTINEL, 9 cảnh, ~44s). Chép ra thư mục làm việc rồi sửa.

## Soát trước khi gửi

`--describe` in mốc từng cảnh, mốc từng mục con, `[nhip]` (chữ hiện quá nhanh), `[LOI]` / `[CANH BAO]`. `--sheet` cho bảng khung mỗi 1,5s; mở bằng Read và tìm: chữ chồng nhau, chữ đè mặt avatar, chữ tràn mép, chữ trùng phụ đề, cảnh trống quá lâu.
