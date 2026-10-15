# Giọng đọc và nhân vật

## Giọng (`"voice"` trong kịch bản)

| Nguồn | Khoá | Khi nào |
|---|---|---|
| Máy đọc tiếng Việt chạy tại chỗ | `{"engine": "offline", "speed": 1.0}` | Mặc định, bản xem nhanh, video số lượng nhiều. Giọng nữ miền Bắc (piper vais1000), lần đầu tải ~65MB từ GitHub. Máy nghe lại đúng ~90% |
| Giang tự thu từng câu | `{"engine": "files"}` + mỗi cảnh `"voice_file": "giong/c01.m4a"` | Giọng thật, đáng tin nhất cho quảng cáo. Thu bằng điện thoại, mỗi cảnh một file, nói đúng câu `say` |
| Một file cho cả bài | `{"engine": "file", "file": "giong.mp3"}` | Giang thu một mạch, hoặc file từ ElevenLabs / vidIQ / Vbee / FPT.AI / CapCut. Máy nghe zipformer (tải ~256MB lần đầu) chia cảnh và mốc từng chữ; dòng `khop chu kich ban` dưới 60% là lời thu khác kịch bản → sửa `say` cho đúng lời |
| Clip có người nói (A-roll) | cảnh `"visual": "aroll", "file": ..., "in": ..., "out": ...` | Clip Giang quay mặt thật, hoặc clip AI avatar (HeyGen…). Tiếng lấy từ clip; `say` gõ đúng lời để ra phụ đề |

- **Tài khoản ElevenLabs riêng của Giang (nghe hay nhất)**: model **Eleven v3** (có tiếng Việt, biểu cảm nhất; Flash v2.5 cũng có tiếng Việt nhưng phẳng hơn; Multilingual v2 không có tiếng Việt), Stability **Natural**, giọng chọn trong Voice Library lọc Vietnamese (giọng người Việt thật, chọn miền theo khách) hoặc clone giọng chính Giang. Mỗi cảnh tạo một file, đặt tên `c01.mp3`… theo thứ tự cảnh, Giang tải về rồi đính kèm vào chat hoặc để vào thư mục đã kết nối → `"voice": {"engine": "files"}` + `"voice_file"` từng cảnh. Gửi Giang danh sách lời dạng `cNN.mp3 | câu say` để dán. Từ viết tắt đọc chưa đúng (DCA, ATR, MT5…): Giang thay bằng cách viết phiên âm ngay trong ElevenLabs, `say` trong kịch bản giữ nguyên để phụ đề đúng chữ. Connector ElevenLabs trên claude.ai (13/10/2026) chỉ quản lý voice agent, không tạo file giọng; máy dựng không gọi được API ElevenLabs.
- **vidIQ (ElevenLabs)**: `vidiq_voiceover_list_voices` (miễn phí) → `vidiq_voiceover_generate` (14 credit / 1000 ký tự, làm tròn lên theo **từng lần tạo** → tạo cả bài một lần rồi dùng `engine: file`, đừng tạo từng câu; giọng có sẵn là giọng nước ngoài nói tiếng Việt, không có Voice Library tiếng Việt) → `vidiq_job_poll` lấy link MP3. Máy dựng **không tải được link này** (mạng bị chặn): gửi link cho Giang tải về, Giang đính kèm vào chat hoặc để vào thư mục đã kết nối, rồi dùng `engine: file`. Báo số credit trước khi tạo (xem `vidiq_balance`). Viết lời có dấu đầy đủ, tách câu bằng dấu chấm.
- **Cách đọc**: `say` viết như phụ đề. Từ tiếng Anh / viết tắt được đổi cách đọc bằng bảng `DOC` trong `ea_voice.py` (EA, MT5, SL, H4, 24/7, Zalo, chart…) và `"doc"` trong `brand_ea.json` (tên sản phẩm). Máy đọc sai từ nào: thêm vào `"doc"` của brand, chạy lại với `--revoice`.
- Claude không nghe được âm thanh. Kiểm bằng máy nghe: `python3 kit/ea_asr_check.py work` in lại lời máy nghe được; từ sai nhiều thì sửa `doc`. Vẫn nói Giang nghe lại bản xem nhanh.

## Nhân vật avatar AURUS (`"avatar"` trong `brand_ea.json`)

```json
"avatar": {"name": "AURUS", "badge": "A", "chest": "24/7", "eye": "#F6D678", "accent": "#D4AF37"}
```

- `name`: chữ khắc trên trán; `badge`: chữ trong huy hiệu lục giác ngực trái; `chest`: chữ trên đèn trạng thái ngực phải.
- `eye` / `accent`: màu mắt LED và viền. Mỗi dòng EA một bộ màu: Sentinel vàng `#F6D678`; dòng DCA có thể mắt xanh `#6FE3E8`; dòng Quant X mắt đỏ cam `#FF9F5A`. Không đổi khung hình nhân vật giữa các video của cùng một dòng — nhận diện nằm ở chỗ khách thấy lặp lại.
- Biểu cảm: `neutral` (mặc định), `smile` (mắt cười — CTA, tóm tắt), `focus` (mắt nheo — câu đảo chiều, quản lý rủi ro). Mắt tự chớp, tự nhìn về phía chữ, miệng LED nhảy theo 7 dải tần của giọng.
- Xem nhanh nhân vật: `python3 kit/ea_avatar.py --sheet work/avatar.jpg` (6 trạng thái).
- Muốn nhân vật khác hẳn (robot khác dáng, người hoạt hình): thêm lớp mới trong `ea_avatar.py` có cùng hàm `draw(...)`, chọn bằng `"avatar": {"type": ...}`; không sửa AURUS.
- Nhân vật người thật / AI avatar ngoài (HeyGen, vidIQ video): bộ dựng không tự tạo được mặt người nói; Giang tạo clip ở công cụ đó rồi dùng cảnh `aroll`. Tạo video AI qua vidIQ (`vidiq_generate_video`) rất tốn credit — chỉ làm khi Giang bảo và đã báo giá.
