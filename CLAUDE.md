# Quy tắc dự án Videoeditortruonggiang

## Xuất video: chất lượng và độ nét là ưu tiên số 1

Giang đăng video lên TikTok, Facebook Reels, Instagram Reels, YouTube Shorts. Video không được mờ, bể khối hay vỡ chữ. Mọi lần xuất video phải theo các mục dưới, trừ khi Giang nói khác.

### Độ phân giải
- Giữ đúng độ phân giải gốc của footage. Video dọc mặc định 1080×1920, 30fps (hoặc fps gốc của nguồn).
- Không hạ độ phân giải để file nhỏ hơn.
- Không upscale lên 4K từ nguồn 1080p: chỉ phóng to, không thêm chi tiết, nền tảng vẫn nén về 1080p.
- Nguồn quay 4K thì giữ 4K cho bản master; bản đăng xuất 1080×1920 bitrate cao.

### Bản master (lưu trữ, sửa tiếp)
- HyperFrames: `npx hyperframes render --quality high`.
- Matting (`remove-background`) dùng `--quality best` khi đặt chữ sau người, để không có viền và lệch màu.

### Bản đăng (gửi Giang, đăng mạng xã hội)
- Bitrate phải **cao hơn hoặc bằng nguồn gốc**, không bao giờ thấp hơn. Đo nguồn bằng `ffprobe` trước khi xuất.
- Mặc định HEVC (hợp iPhone), CRF 17, preset slow, tag `hvc1`, AAC 192k, faststart:
  ```bash
  ffmpeg -i master.mp4 -c:v libx265 -preset slow -crf 17 \
    -x265-params "vbv-maxrate=16000:vbv-bufsize=24000" -tag:v hvc1 -pix_fmt yuv420p \
    -c:a aac -b:a 192k -movflags +faststart ban_dang_hd.mp4
  ```
  Kết quả với 1080×1920 / 18s: khoảng 16–17 Mbps, khoảng 2MB mỗi giây video.
- Cần H.264 (máy cũ, nền tảng không nhận HEVC): `-c:v libx264 -preset slow -crf 16 -profile:v high`, tối thiểu 12 Mbps cho 1080×1920.
- Không dùng bitrate thấp kiểu 6 Mbps cho bản đăng. Mức đó chỉ dùng khi buộc phải ép file nhỏ, và phải nói rõ với Giang là bản đã giảm chất lượng.
- Không nén nhiều lần: luôn xuất bản đăng từ bản master, không nén lại từ một bản đã nén.

### Chữ trên video không bị vỡ
- Chữ quan trọng (giá, tiêu đề hook) tối thiểu khoảng 90px chiều cao ở khung 1080×1920, chữ đậm, có bóng hoặc nền để tách khỏi hình.
- Đặt chữ trong vùng an toàn: tránh khoảng 15% trên cùng và 20% dưới cùng, nơi nút và caption của TikTok/Reels che.

### Gửi file cho Giang
- Giang tải về iPhone qua thẻ file trong app Claude. File khoảng 7–14MB lưu được, còn file 102MB thì app không hiện nút lưu.
- Luôn gửi bản đăng HD (theo mục trên). Nếu Giang báo không lưu được, gửi thêm một bản nhỏ hơn và ghi rõ bản đó chất lượng thấp hơn.
- Báo kèm thông số: độ phân giải, bitrate, dung lượng, codec, và so với video gốc.

### Nhắc Giang khi đăng
- Bật "Tải lên chất lượng cao / HD" trong cài đặt TikTok, Facebook, Instagram trước khi đăng, nếu không các app sẽ nén mạnh.
