# GQ Video Editor — AI BĐS Studio

Trình biên tập video web hướng tới môi giới bất động sản: **Upload → câu lệnh tiếng Việt → AI Edit Plan → Preview → Render MP4**.

## MVP hiện tại

- Upload / kéo thả MP4, MOV, WebM.
- Preview video theo 9:16, 1:1 và 16:9.
- Scrubber, play/pause và timeline nhiều đoạn.
- Lệnh tiếng Việt để tạo edit plan: thời lượng, phong cách, hook, CTA.
- Preset video: Luxury BĐS, Chốt Nhanh, Gia Đình.
- Auto Color preview và filter render: exposure, contrast, saturation, gamma, color balance, sharpen.
- Text / headline / giá / nhãn thương hiệu theo layout Premium Real Estate.
- Export MP4 H.264 + AAC bằng FFmpeg WebAssembly ngay trên trình duyệt.
- Progress khi render và tải file `.mp4` về máy.

## Kiến trúc mở rộng

1. **AI Scene Intelligence**: tách cảnh, nhận diện mặt tiền, phòng khách, phòng ngủ, bếp, đường vào, tiện ích, biển số / thông tin nhạy cảm.
2. **Smart Cut Engine**: phát hiện đoạn rung, out-of-focus, im lặng, lặp cảnh và nhịp cảnh kém.
3. **Real-estate Copy Engine**: tạo hook, USP, giá, vị trí, CTA, caption và keyword highlight theo từng listing.
4. **Caption Engine**: speech-to-text, karaoke timing, keyword highlight và template caption.
5. **Audio Engine**: lọc ồn, voice enhance, auto ducking, beat sync và thư viện nhạc.
6. **Timeline Engine**: drag/resize/split/trim, multi-track, B-roll, ảnh, logo, sticker, transition và keyframe.
7. **Color Lab**: auto-match theo frame tham chiếu, LUT, temperature, tint, exposure, HSL, curves và sharpen.
8. **Export Profiles**: TikTok/Reels/Shorts, Facebook, YouTube, 1080p và 4K; giữ bitrate phù hợp để hạn chế nén không cần thiết.
9. **Project Storage**: lưu project JSON, asset metadata và phiên bản edit; sẵn sàng nối Supabase.
10. **AI API**: lớp adapter độc lập để nối Gemini/OpenAI hoặc model khác mà không khóa editor vào một nhà cung cấp.

## Chạy local

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

> Ghi chú: FFmpeg WebAssembly tải core ở lần export đầu tiên. Rendering video dài/4K sẽ phụ thuộc mạnh vào CPU, RAM và trình duyệt của máy.
