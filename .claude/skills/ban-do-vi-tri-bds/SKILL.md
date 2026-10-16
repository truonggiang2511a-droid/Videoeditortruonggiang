---
name: ban-do-vi-tri-bds
description: Dựng video bản đồ vị trí bất động sản kiểu "vẽ đường từ căn nhà" (9:16, ảnh vệ tinh 3D nghiêng, line sáng chạy từ từ, chữ 3D in dẹt tên tuyến đường, ghim icon tiện ích, thẻ khoảng cách + phút ô tô, SFX). Tự quét và in chữ 3D cho mọi cao tốc, vành đai, quốc lộ, tỉnh lộ quanh nhà, không cần Giang nêu tên đường. Dùng khi Giang gửi link Google Maps / toạ độ căn nhà và nhờ "vẽ đường ra QL1A, chợ, trường…", "video vị trí", "bản đồ tiện ích", "khoảng cách bao nhiêu mét, mấy phút".
---

# Video bản đồ vị trí BĐS (kiểu Phước Lý v3)

Mẫu chuẩn: `videos/vi-tri-phuoc-ly-v3/`, config `vi-du/phuoc-ly.json`. Bộ công cụ ở `kit/`:

| File | Việc |
|---|---|
| `kit/fetch.py config.json DỰ_ÁN` | Lấy dữ liệu thật: **tự quét hạ tầng giao thông chính quanh nhà** (cao tốc, vành đai, quốc lộ, tỉnh lộ và các đường lộ trình đi qua), lộ trình ô tô và mét/giây (OSRM), ảnh vệ tinh Esri ở 3 mức zoom. Có cache, chạy lại không tốn mạng |
| `kit/build.py config.json DỰ_ÁN` | Tự căn khung, tự đặt chữ 3D, tự chọn hướng thẻ, tạo `index.html`, SFX và nhạc nền, rồi in **báo cáo chồng chữ** |
| `kit/template.tpl` | Toàn bộ phong cách: CSS, camera 3D, line, comet, chữ 3D, ghim, HUD, bảng tóm tắt |
| `kit/sfx.py [giây_bgm]` | Tổng hợp SFX (whoosh, pop, chime, draw, boom, riser) và nhạc nền êm vào `assets/` |

## Quy trình

1. **Toạ độ nhà**: mở link Maps rút gọn (theo redirect), lấy `@lat,lon` hoặc `!3d…!4d…`. Hỏi lại nếu link không ra toạ độ.
2. **Viết config** (chép `vi-du/phuoc-ly.json`):
   - `title`: kicker, line1 (trắng), line2 (vàng), sub.
   - `tag`: tên căn nhà, chỉ ghi đặc điểm. **Không có số điện thoại** trên hình.
   - **Chữ 3D tên đường: mặc định để tự động, không cần Giang nêu tên đường.**
     - `fetch.py` quét trong khoảng `road_km` (4 km) quanh nhà, cộng thêm các đường mà lộ trình đi qua: cao tốc, vành đai (trắng), quốc lộ (cam, QL1 ghi "QUỐC LỘ 1A"), tỉnh lộ / ĐT (cyan, ghi "TL…").
     - Lấy tối đa `max_roads` tuyến (mặc định 5), ưu tiên cao tốc > quốc lộ > tỉnh lộ, rồi đến gần nhà. Bỏ tuyến trùng làn với tuyến đã chọn.
     - Tên cao tốc dài được tách 2 dòng: "CAO TỐC" to, tên tuyến nhỏ ở dưới.
     - Mỗi chữ hiện ở cảnh đầu tiên có lộ trình chạy trên tuyến đó. Cảnh đó chật thì tự chuyển sang cảnh khác còn chỗ trống.
     - Kết quả nằm trong `map/roads_auto.json`. Bỏ bớt: `"roads_skip": ["key"]`. Đổi chữ: `"road_labels": {"key": "CHỮ"}`.
     - Muốn tự chọn tay toàn bộ thì khai báo `roads`, gồm `key`, `queries`, `label`, `style` (`q` cam, `t` cyan, `w` trắng), `size` và `reveal_with`.
   - `stops` theo thứ tự kể chuyện, gần trước xa sau. Mỗi điểm có `label`, `chip` (chữ ngắn trên thẻ) và `icon` (road, cross, market, school, gov, hospital, city, park, shop, bridge). Toạ độ cho bằng `at` (đã tra), `query` hoặc `nearest_road` (điểm gần nhất ra tuyến đường, dùng khoá trong `roads_auto.json`, ví dụ `tl835b`, `quoclo1a`).
     - `hud: false` cho điểm phụ, chỉ hiện thẻ nhỏ.
     - `far: true` cho điểm rất xa như trung tâm TP.HCM.
   - `summary`: các dòng cho bảng cuối.
3. `python3 kit/fetch.py config.json videos/<ten-du-an>`. Mạng phải mở cho nominatim.openstreetmap.org, router.project-osrm.org và server.arcgisonline.com. In ra mét, phút ô tô và khoảng cách chim bay.
4. **So số với tin đăng.** OSRM ra quãng đường thật theo đường ô tô, tin đăng thường ghi chim bay hoặc làm tròn. Hai nguồn lệch nhau thì **hỏi Giang dùng số nào**. Muốn dùng số tin đăng thì đặt `show_m` / `show_s` cho điểm đó. Không tự bịa số.
5. Tạo dự án HyperFrames: chép `package.json`, `hyperframes.json`, `meta.json`, `CLAUDE.md` từ `videos/vi-tri-phuoc-ly-v3/` và đổi tên.
6. `python3 kit/build.py config.json videos/<ten-du-an>`. Đọc báo cáo:
   - Phải ra `Kiem tra chong chu: OK`. Còn dòng `!` thì sửa config rồi build lại (xem mục Sửa lỗi).
   - Dòng `(ghi chú)` là icon chạm icon (ghim sát nhà), chấp nhận được.
7. `npx hyperframes lint` (0 error), rồi `npx hyperframes snapshot --at <các giây build in ra>`. **Mở ảnh xem tận mắt từng khung:**
   - Thẻ và HUD của từng điểm hiện đủ chữ, không bị cắt mép.
   - Chữ 3D tên đường không bị ghim, thẻ hay HUD đè lên.
   - Không lộ nền đen.
   - Tiêu đề không lỗi font.
8. Render bản master `npx hyperframes render --quality high`, rồi xuất bản đăng HEVC theo `CLAUDE.md`. Gửi Giang kèm thông số.

## Phong cách (đừng đổi nếu Giang không yêu cầu)

- **Mở đầu (0–5s)**:
  - Toàn cảnh nghiêng 26°, riser lên rồi boom.
  - Pill vàng cho kicker. Tiêu đề Be Vietnam Pro Black 118px, dòng 2 màu vàng.
  - Dòng phụ trên nền tối.
- **Vào nhà (5–9.6s)**:
  - Zoom tới khoảng 3, lớp ảnh z18 sắc nét mờ dần vào.
  - Ghim đỏ hình giọt nước rơi xuống kiểu bounce, vòng vàng lan ra.
  - Bảng tên đỏ "CĂN NHÀ" kèm dòng phụ.
- **Mỗi điểm dừng**:
  - Camera trượt (whoosh), rồi line vẽ từ từ với comet sáng chạy ở đầu line (SFX draw).
  - Line gồm 4 lớp: bóng đen, glow vàng, lõi kem, dòng chảy chấm trắng.
  - Tới nơi thì ghim icon màu bật lên (pop), thẻ tên kèm "x km · ~y phút".
  - Điểm chính có thêm HUD to ở dưới (chime): "TỪ CĂN NHÀ ĐẾN", tên, số mét vàng 70px.
- **Chữ 3D in dẹt**: chữ nằm phẳng trên mặt đất theo hướng con đường. Mặt chữ trắng bóng gradient, khối đùn 7 lớp xám, glow theo màu tuyến. Đường được tô sáng (cam, cyan hoặc trắng) trước, chữ bật lên sau 1 giây.
- **Điểm xa** (TP.HCM): zoom ra khoảng 0,13, nghiêng 10°, lớp z16 mờ đi chỉ còn ảnh z14.
- **Kết**: quay về toàn cảnh, bảng "Từ căn nhà đi" liệt kê khoảng cách và phút.
- **Chú thích nguồn** ở đáy: "Quãng đường theo bản đồ OpenStreetMap · thời gian ô tô ước tính", "Ảnh vệ tinh: Esri, Maxar · Dữ liệu đường: © OpenStreetMap".

## Luật bố cục (build.py tự làm, lúc xem snapshot vẫn phải soát lại)

1. **Không cắt chữ**:
   - Camera mỗi điểm được tính để toàn bộ route, nhà, ghim, **thẻ tên** và chữ 3D vừa hiện nằm trong vùng an toàn: x 70–1010, y 300 tới đỉnh HUD (1176), hoặc tới 1500 nếu không có HUD.
   - Phép tính có tính cả độ nghiêng 3D.
   - Lỗi ở v2 (Chợ Long Thượng, TT TP.HCM mất chữ) là do camera đặt tay. Từ nay không đặt tay nữa.
2. **Chữ không đè chữ**: tên đường không chồng tên đường khác. Ở cảnh sau, tên đường nào sẽ bị ghim, thẻ, HUD hay tên đường khác che thì mờ đi trong cảnh đó rồi hiện lại. Báo cáo cũng báo lỗi nếu có tên đường không hiện trọn trong cảnh nào.
3. **Ghim không che chữ 3D**:
   - Chữ tên đường được đặt ở vị trí dọc con đường mà ở mọi khung hình không đè ghim, thẻ, HUD hay chữ khác, và không bị cắt nửa ở mép.
   - Ở cảnh xa, ghim nào rơi lên chữ thì tạm ẩn.
4. **Thẻ không đè gì**:
   - Hướng thẻ (trên, dưới, trái, phải) được chọn tự động để né chữ 3D, ghim khác, HUD và mép khung.
   - Ghim cũ nằm dưới thẻ, HUD hay bảng tóm tắt thì mờ đi trong cảnh đó.
5. Chữ trên thẻ và HUD theo vùng an toàn TikTok/Reels: tránh 15% trên và 20% dưới.
6. Hai điểm quá sát nhau (dưới khoảng 80m, ví dụ trường và UBND cạnh nhau) thì cân nhắc gộp hoặc để `hud: false`.

## Sửa lỗi theo báo cáo

| Báo | Sửa |
|---|---|
| `thẻ … ra ngoài vùng an toàn` | giảm `zmax` của điểm đó, hoặc ép `"side": "d"` / `"l"` / `"r"` |
| `… đè chữ <tên đường>` | đổi `reveal_with` sang điểm khác, giảm `size`, hoặc thêm `lines` để chữ có đoạn đường khác mà đứng |
| `lộ nền đen` | tăng `far_km` hoặc lề ảnh z14 trong `fetch.py` (`fp`), rồi fetch lại |
| route đi vòng lạ | đặt `at` chính xác hơn (cổng chợ, đầu hẻm) |

## Nhớ

- Số điện thoại chỉ ở caption, không lên hình.
- Không ghi "rẻ nhất" hay hứa tăng giá. Khoảng cách và thời gian lấy từ OSRM hoặc tin đăng, ghi "~" và "ô tô ước tính".
- Ảnh vệ tinh, cache, renders, fonts, sfx và bgm không commit (xem `.gitignore`). Commit config, `map/*.json`, `index.html`.
