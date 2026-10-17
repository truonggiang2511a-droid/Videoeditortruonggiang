---
name: quang-cao-facebook-bds
description: Quy trình chuẩn chạy quảng cáo tin nhắn Facebook / Instagram (Meta Ads) để bán một căn nhà, lô đất của Giang / Minh Thùy. Dùng khi Giang hỏi "chạy quảng cáo căn này", "target thế nào", "setup chiến dịch", "nhóm quảng cáo", "mẫu quảng cáo", "ngân sách bao nhiêu", "tắt bật nhóm nào", hoặc gửi số liệu quảng cáo nhờ đọc. Soạn sẵn cấu hình, chữ quảng cáo, tin nhắn chào; Giang tự bấm trong Trình quản lý quảng cáo.
---

# Quảng cáo tin nhắn Facebook cho nhà đất (quy trình chuẩn)

Giang tự bấm trong Trình quản lý quảng cáo (Claude không có quyền tạo chiến dịch). Việc của Claude: soạn **phiếu chạy quảng cáo** cho từng căn theo khuôn dưới, viết chữ quảng cáo, tin nhắn chào, rồi đọc số liệu và khuyên tắt / tăng. Trả lời bằng tiếng Việt, ngắn, từng bước bấm được.

## Luật

1. Chữ quảng cáo chỉ dùng thông tin có trong tin đăng / lời Giang (giống skill `kich-ban-video-bds`). Không "rẻ nhất", "cam kết tăng giá", "lời chắc chắn" (dễ bị Facebook từ chối, mất uy tín).
2. **Số điện thoại không nằm trên hình video**; được ghi trong nội dung bài viết và tin nhắn.
3. **Ghi rõ giá** trong chữ quảng cáo: lọc bớt người không đủ tài chính.
4. Nếu Facebook bắt khai **Danh mục quảng cáo đặc biệt – Nhà ở** thì phải khai (khi đó không chọn được tuổi / giới tính, vị trí có bán kính tối thiểu): dựa vào video + chữ để lọc khách.
5. Không bịa con số chi phí; mọi mức ngân sách là mức khởi động, chỉnh theo số liệu thật sau 3–5 ngày.

## Bước 0 — Chuẩn bị (mỗi căn)

- Video dọc 9:16 HD (dựng theo `tron-video-aroll-broll`, xuất theo `CLAUDE.md`).
- **Đăng video lên fanpage trước** với nội dung đầy đủ (cách chuẩn): tương tác của mọi nhóm dồn về một bài → khách tin hơn, quảng cáo rẻ hơn. Không dùng nút "Quảng cáo bài viết" trên trang.
- Bật thông báo Messenger / Business Suite trên điện thoại người trả lời: **trả lời trong 5 phút**.

## Bước 1 — Chiến dịch (1 chiến dịch / căn)

- Mục tiêu: **Tương tác → Tin nhắn** (Messenger, thêm Instagram).
- Ngân sách đặt ở **nhóm quảng cáo** khi thử nghiệm (để so nhóm công bằng); khi đã rõ nhóm tốt mới chuyển ngân sách chiến dịch (Advantage+).
- Tên gợi ý: `TN | <tên căn> | <ngày>`.

## Bước 2 — Nhóm quảng cáo (3 nhóm)

| Nhóm | Vị trí | Đối tượng | Ngân sách khởi động |
|---|---|---|---|
| **A – Gần căn nhà** | "Người sống ở khu vực này", bán kính 15–20 km quanh căn | Tuổi 30–60 (nếu được chọn); **không** chọn sở thích (để Advantage+ tự tìm) | ~200 nghìn/ngày |
| **B – Thành phố lớn** | TP.HCM (hoặc tỉnh có khách), **loại trừ** bán kính của nhóm A | **1 ô** sở thích, 3–5 mục: Đầu tư bất động sản, Nhà ở, Làm vườn, Du lịch nghỉ dưỡng… Không dùng ô "Thu hẹp" khi mới chạy | ~200 nghìn/ngày |
| **C – Bám đuổi** | Như A + B | Tệp tuỳ chỉnh: xem ≥50% video 30 ngày, tương tác trang 90 ngày, đã nhắn tin | ~100 nghìn/ngày |

- Nhóm A và B **loại trừ tệp của nhóm C** để không giành cùng một người.
- Trang mới / ít tương tác: chạy A + B trước, bật C khi có khoảng 1.000 người xem video (ngày 5–7).
- Có từ ~100 người nhắn tin: thêm nhóm **Lookalike 1–3%** từ người đã nhắn tin.
- Vị trí hiển thị: **Advantage+ (tự động)** — video dọc chủ yếu chạy Reels + bảng tin.
- **Bộ sở thích nhóm B** (tất cả trong **1 ô** = "hoặc", thêm mục là mở rộng tệp; nhắm 8–12 mục, tổng tệp TP.HCM khoảng 2–10 triệu):
  - Bất động sản: Bất động sản (Real estate), Đầu tư bất động sản, Nhà ở (Home), Mua nhà / Nhà đất, trang Batdongsan.com.vn, Chợ Tốt Nhà (nếu Facebook gợi ý);
  - Hợp kiểu nhà (nhà vườn, nhà gỗ): Làm vườn, Kiến trúc, Thiết kế nội thất, Du lịch nghỉ dưỡng;
  - Khả năng tài chính: Đầu tư, Chủ doanh nghiệp nhỏ;
  - Sự kiện trong đời: Mới kết hôn (1 năm), Phụ huynh có con nhỏ.
  Hành vi ở Việt Nam ít mục hợp bất động sản: không cần chọn. Nói rõ với Giang: Facebook không có mục "đang tìm mua nhà" ở Việt Nam; sở thích chỉ là điểm xuất phát, lọc khách thật nằm ở video + giá trong chữ + nhóm bám đuổi + Lookalike.
- Ô thứ hai "Thu hẹp đối tượng": chỉ thử ở **một nhóm thử riêng** khi nhóm B nhiều tin nhắn mà khách không đủ tài chính; giữ quy mô trên khoảng 500 nghìn người.

## Bước 3 — Quảng cáo

**Có 1 video:** cả 3 nhóm dùng **"Sử dụng bài viết hiện có"** (cùng một bài fanpage).
**Có 2–4 video:** mỗi nhóm cùng một bộ 3 mẫu để so công bằng:
1. Mở bằng **giá + pháp lý**,
2. Mở bằng **vị trí** (flycam, bản đồ, khoảng cách),
3. Mở bằng **cảm xúc / nhóm khách** (kịch bản từ `kich-ban-video-bds`).
Hết video mới: cắt lại **3 giây đầu** của video đang có (mở bằng giá / bằng flycam) là thành mẫu mới.

**Chữ quảng cáo** (Claude soạn): dòng đầu = lợi ích chính; 3–4 gạch đầu dòng (diện tích, pháp lý, vị trí, giá); câu kêu gọi nhắn tin. Tạo trong Trình quản lý thì nhập **3–5 câu mở đầu + 3 tiêu đề** cho Facebook tự thử.

**Tin nhắn chào + 3 nút trả lời nhanh:**
"Chào anh/chị, Thùy gửi thông tin <tên căn> ạ. Anh/chị cần xem gì trước?"
→ `Xem vị trí & đường đi` · `Giá & pháp lý` · `Hẹn xem nhà`

## Bước 4 — Theo dõi và tối ưu

- **3 ngày đầu không sửa gì** (không đổi chữ, ngân sách, tắt bật: Facebook học lại từ đầu).
- Chỉ số: chi phí / cuộc trò chuyện → tỷ lệ để lại số điện thoại → **số lịch hẹn xem nhà** (quan trọng nhất).
- Sau 3–5 ngày: tắt mẫu / nhóm có chi phí tin nhắn **gấp đôi trung bình** hoặc tin nhắn không ai hỏi xem nhà; nhóm tốt tăng ngân sách **~20% mỗi 2–3 ngày**.
- Video chạy 1–2 tuần mà chi phí / tin nhắn tăng hơn ~30%: thay mẫu mới.
- Số liệu: Giang chụp màn hình Trình quản lý, hoặc kết nối tài khoản quảng cáo nhà đất vào Metricool (thương hiệu riêng, không dùng thương hiệu "Alpha Bot Gold V2" của EA) để Claude đọc bằng công cụ Metricool (`facebookAds` / `metaAds`).

## Lịch mẫu

| Ngày | Việc |
|---|---|
| 0 | Đăng video lên fanpage, bật thông báo tin nhắn |
| 1 | Bật chiến dịch: nhóm A, B (và C nếu trang có sẵn tương tác) |
| 1–3 | Chỉ trả lời tin nhắn, bình luận; không sửa quảng cáo |
| 4–5 | Đọc số liệu, tắt mẫu / nhóm kém, bật C nếu chưa bật |
| 6+ | Tăng 20% / 2–3 ngày cho nhóm tốt; chuẩn bị mẫu mới |

## Giao cho Giang (mỗi căn)

Một **phiếu chạy quảng cáo** gồm: tên chiến dịch; 3 nhóm (vị trí, bán kính, sở thích, ngân sách, loại trừ); nội dung bài đăng fanpage; 3–5 câu mở đầu + 3 tiêu đề; tin nhắn chào + 3 nút; lịch kiểm tra. Lưu ở `quang-cao/<ten-can>.md` và gửi toàn bộ nội dung trong câu trả lời để Giang dán.
