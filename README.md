# GQ Video Editor — AI BĐS Studio

Trình biên tập video web hướng tới môi giới bất động sản: **Upload → câu lệnh tiếng Việt → AI Edit Plan → Preview → Render MP4**.

## Đã có trong nền tảng

- Upload / kéo thả MP4, MOV, WebM.
- Preview video theo 9:16, 1:1 và 16:9.
- Scrubber, play/pause, nhảy thời gian và timeline nhiều đoạn.
- Lệnh tiếng Việt để tạo edit plan: thời lượng, phong cách, hook, CTA, tỷ lệ khung hình và nhóm cảnh BĐS.
- Preset video: Luxury BĐS, Chốt Nhanh, Gia Đình.
- Auto Color preview và filter render: exposure, contrast, saturation, gamma, color balance, sharpen.
- Text / headline / giá / nhãn thương hiệu theo layout Premium Real Estate.
- Export MP4 H.264 + AAC bằng FFmpeg WebAssembly ngay trên trình duyệt.
- Render có progress, color space BT.709 và audio loudness/voice enhancement tùy chọn trong engine.
- Project JSON local: lưu, import và export cấu hình dự án.
- Speech-to-caption tiếng Việt bằng Web Speech API khi trình duyệt hỗ trợ.
- AI planner tách riêng trong `src/lib/ai.js`, dễ nối model cloud.
- Vercel API function `api/ai.js` cho AI planner từ xa; không có API key thì tự động dùng fallback planner an toàn.

## Kiến trúc sản phẩm A-Z

### 1. AI Scene Intelligence
Nhận diện và xếp hạng các cảnh như mặt tiền, đường vào, phòng khách, bếp, phòng ngủ, WC, sân/vườn, pháp lý và CTA. Bản planner hiện đã có schema; bước tiếp theo là gắn model vision để phân tích frame thật.

### 2. Smart Cut Engine
Mục tiêu: loại đoạn rung, out-of-focus, im lặng, lặp cảnh, dư đầu/cuối và cảnh có điểm nhấn thấp; sau đó giữ lại các đoạn có giá trị bán hàng cao.

### 3. Real-estate Copy Engine
Sinh hook, USP, giá, vị trí, pháp lý, CTA, caption và keyword highlight. Không tự bịa dữ kiện căn nhà; dữ kiện thiếu sẽ được để dạng placeholder.

### 4. Caption Engine
Speech-to-text, chia câu thành dòng dễ đọc, karaoke timing, keyword highlight và template caption. Engine trình duyệt nằm tại `src/lib/captions.js`.

### 5. Audio Engine
Voice enhance, auto ducking, loudness chuẩn hóa, beat sync và thư viện nhạc sẽ dùng timeline audio riêng ở phase kế tiếp.

### 6. Timeline Engine
Kéo/đổi kích thước/split/trim, multi-track, B-roll, ảnh, logo, sticker, transition và keyframe là hướng mở rộng của timeline hiện tại.

### 7. Color Lab
Auto exposure/contrast/saturation/gamma, temperature, tint, HSL, curves, LUT và auto-match theo frame tham chiếu.

### 8. Export Profiles
Preset TikTok/Reels/Shorts, Facebook, YouTube; 1080p/4K; H.264/AAC; giữ chất lượng bằng CRF và BT.709. Render dài/4K phụ thuộc CPU, RAM và trình duyệt.

### 9. Project Storage
Mỗi project có metadata, timeline, text, audio, export profile và version. Hiện có local JSON; có thể nối Supabase sau.

### 10. AI Provider Adapter
`api/ai.js` hỗ trợ endpoint tương thích Chat Completions thông qua `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL`. Có thể thay provider mà không khóa editor vào một hãng.

## Luồng sử dụng mục tiêu

1. Upload footage căn nhà.
2. Nhập: `Làm video 45 giây, hook mạnh 3 giây đầu, phong cách sang, nhấn vị trí + giá, caption đẹp, CTA gọi xem nhà.`
3. AI tạo plan.
4. AI Scene Intelligence chọn các đoạn tốt.
5. Smart Cut dựng nhịp.
6. Text/Caption/Color/Audio tự áp preset BĐS.
7. Người dùng chỉnh timeline nếu cần.
8. Preview.
9. Export MP4.

## Chạy local

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## AI cloud trên Vercel

Tạo Environment Variables:

```text
AI_API_KEY=...
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4.1-mini
```

Không cấu hình API key thì app vẫn có fallback planner cục bộ để thao tác UI và dựng quy trình.
