---
format: 1080x1920
duration: 170s
message: "Robot EA là công cụ tự động; AI giúp nó thông minh hơn nhưng không phải máy in tiền, hiểu rủi ro và test demo trước khi dùng vốn thật"
arc: Hook → Bối cảnh AI → EA là gì → Cơ chế → Ví dụ → Lợi ích → Phân loại → AI thay đổi → Sự thật DCA → Thuật ngữ → Tiêu chí → Chính bạn → Lộ trình → CTA
audience: người mới chưa biết Robot EA, quan tâm AI và đầu tư vàng
mode: autonomous
music: none
language: vi
---

## Video direction

- **palette system** (từ frame.md BlockFrame): nền cream #FFFDF5 làm nền chính; accent hồng #FE90E8, xanh #C0F7FE, xanh lá #99E885, vàng #F7CB46; mọi khối có viền đen 4px + bóng đổ cứng 8px; frame cảnh báo (9) dùng nền ink tối để tạo đối lập; đỏ chỉ dùng cho cảnh báo/rủi ro.
- **type**: Inter 800-900 chữ HOA cho tiêu đề, Space Grotesk cho nhãn nhỏ. Mọi chữ tiếng Việt CÓ DẤU đầy đủ — kiểm tra dấu không bị cắt (line-height ≥ 1.1 cho chữ hoa có dấu). Hero chữ gần full-bleed 1080 rộng, tối đa 4-5 từ mỗi dòng.
- **motion grammar**: power3 mặc định; mỗi mảnh nội dung chỉ xuất hiện khi VO nói tới (VO-paced), không dump đầu frame; cho phép jitter rất nhẹ khi hold, không breathing/pan lười.
- **rhythm**: frame 1 và 9 nhịp mạnh nhất; frame 4, 10, 13 là nhịp thở (giữ tĩnh sau khi lộ nội dung); frame 14 giữ tĩnh ~1.2s cuối.
- **portrait**: nội dung chính trong 83% trên (caption pill chiếm ~17% dưới); hero anchor y ≈ 0.42×1920; xếp dọc, không split-screen ngang.
- **negative list**: không số điện thoại; không số dư/lịch sử lệnh/kết quả lãi giả; không % lợi nhuận; biểu đồ luôn gắn nhãn MINH HOẠ; không gradient tím-xanh kiểu AI; không bokeh; không kiểu slideshow (front-load rồi đứng) và không kiểu screensaver (mọi thứ trôi riêng).
- **disclaimer**: frame 9 và frame 14 phải có dòng 'GIAO DỊCH VÀNG CÓ RỦI RO' nhìn thấy.

## Frame 1 — Hook - Cỗ máy không ngủ

- scene: Chữ khổng lồ đổi từ NGỦ sang ROBOT EA, kèm nhãn AI
- voiceover: "Trong lúc bạn đang ngủ, có những cỗ máy vẫn đang giao dịch vàng. Không mệt, không sợ hãi, không tham lam. Chúng được gọi là Robot EA. Và AI đang khiến chúng thông minh hơn mỗi ngày."
- duration: 9.251s
- transition_in: cut
- status: outline
- src: compositions/frames/01-hook.html
- type: hook
- persuasion: Curiosity gap + contrast (con người vs máy)
- beat: hook
- blueprint: kinetic-type-beats (Adapt)
- focal: từ khoá khổng lồ NGỦ → ROBOT EA
- roles: NGỦ/ROBOT EA = foreground subject · lưới chấm nền = background (dim 40%) · chip KHÔNG MỆT/KHÔNG SỢ/KHÔNG THAM = supporting · sticker AI = supporting
- sfx: none

narrativeRole: Mở bằng nghịch lý: máy làm việc lúc bạn ngủ
keyMessage: Robot EA = cỗ máy giao dịch không mệt, AI làm nó thông minh hơn

Scene 1 (0–2.8s): Nền cream lưới chấm; chữ NGỦ (nghiêng nhẹ, viền đen dày, bóng đổ cứng) pop vào giữa khung, centered ~55% khung, per-word reveal lúc VO nói 'đang ngủ'
Scene 2 (2.8–6.1s): Cụm 'giao dịch vàng' — một đồng vàng/thỏi vàng vẽ bằng hình khối rơi xuống dưới chữ NGỦ; ba chip KHÔNG MỆT · KHÔNG SỢ · KHÔNG THAM lần lượt swap tại chỗ (hard cut) đúng nhịp từng cụm VO
Scene 3 (6.1–8.4s): Khi VO nói 'Robot EA': NGỦ bị đẩy ra, chữ ROBOT EA slam vào full-bleed với starburst vàng; layered-depth 3 lớp
Scene 4 (8.4–9.9s): Sticker +AI (chip xanh) spring-pop góc phải trên, hold tĩnh đến hết câu

## Frame 2 — AI bùng nổ

- scene: Bốn thẻ nghề AI xếp chồng, thẻ ĐẦU TƯ sáng lên
- voiceover: "AI đang bùng nổ ở mọi nơi: viết bài, vẽ tranh, lập trình. Đầu tư cũng không ngoại lệ. Các quỹ lớn dùng thuật toán từ lâu rồi. Điều mới là, người bình thường như bạn cũng đã tiếp cận được công cụ tương tự."
- duration: 10.739s
- transition_in: crossfade
- status: outline
- src: compositions/frames/02-ai-bung-no.html
- type: context
- persuasion: Relatability + progressive disclosure
- beat: setup
- blueprint: grid-card-assemble (Adapt)
- focal: chồng thẻ VIẾT BÀI / VẼ TRANH / LẬP TRÌNH / ĐẦU TƯ
- roles: các thẻ = foreground · nền xanh nhạt = background · thẻ ĐẦU TƯ = hero accent vàng · nhãn QUỸ LỚN → BẠN = supporting
- sfx: none

narrativeRole: Đặt bối cảnh: AI ở mọi nơi, đầu tư cũng vậy
keyMessage: AI đã vào đầu tư; công cụ không còn chỉ dành cho quỹ lớn

Scene 1 (0–3.4s): Nền xanh nhạt (blue); thẻ VIẾT BÀI, VẼ TRANH, LẬP TRÌNH lần lượt rơi xếp dọc (stagger cascade) đúng khi VO nói từng việc; vertical list ~60% khung
Scene 2 (3.4–6.2s): Thẻ ĐẦU TƯ xuất hiện cuối cùng, to hơn, nền vàng, các thẻ khác dim 50%; hold nhẹ
Scene 3 (6.2–9s): VO 'quỹ lớn dùng thuật toán': nhãn QUỸ LỚN + biểu tượng chart nhỏ hiện bên trái thẻ ĐẦU TƯ, mũi tên vẽ nét (draw-on) sang phải
Scene 4 (9–11.3s): Mũi tên chạm nhãn BẠN (chip hồng) — 'người bình thường cũng tiếp cận được'; hold tĩnh

## Frame 3 — Robot EA là gì

- scene: Phương trình EA = Expert Advisor = cố vấn tự động, kèm cửa sổ MT5 tối giản
- voiceover: "Vậy Robot EA là gì? EA là viết tắt của Expert Advisor, nghĩa là cố vấn tự động, một phần mềm chạy trên MT5. Bạn đặt luật một lần, nó tự đọc giá, tự vào lệnh, tự đặt cắt lỗ."
- duration: 10.874s
- transition_in: blur-crossfade
- status: outline
- src: compositions/frames/03-ea-la-gi.html
- type: definition
- persuasion: Definition + equation build
- beat: comprehension
- blueprint: kinetic-type-beats (Adapt)
- focal: dòng phương trình EA = cố vấn tự động
- roles: phương trình chữ lớn = foreground · khung cửa sổ MT5 vẽ tối giản (nến + nút) = supporting · nền cream = background
- sfx: none

narrativeRole: Định nghĩa EA bằng ngôn ngữ đời thường
keyMessage: EA là phần mềm tự làm việc theo luật bạn đặt

Scene 1 (0–2.5s): Chữ 'ROBOT EA là gì?' xuất hiện lớn ở trên (top third), per-word reveal
Scene 2 (2.5–5.8s): VO 'viết tắt của Expert Advisor': chữ EA tách thành EXPERT · ADVISOR, hai chip xanh/hồng lắp vào nhau thành phương trình; dịch 'cố vấn tự động' hiện nghiêng bên dưới
Scene 3 (5.8–8.6s): VO 'phần mềm chạy trên MT5': khung cửa sổ MT5 vẽ tối giản (thanh tiêu đề, vài nến) trượt lên chiếm nửa dưới, 60/40 stacked
Scene 4 (8.6–11.5s): VO 'đặt luật một lần, tự vào lệnh, tự đặt cắt lỗ': ba chip ĐẶT LUẬT → VÀO LỆNH → CẮT LỖ nối bằng mũi tên, hiện đúng nhịp; hold

## Frame 4 — Ba bước làm việc

- scene: Ba thẻ dọc 1-2-3 với vòng lặp nối
- voiceover: "Cách làm việc chỉ có ba bước. Một, quan sát giá liên tục. Hai, so với luật bạn đã cài. Ba, gửi lệnh trong vài phần giây. Lặp lại suốt giờ thị trường mở cửa."
- duration: 8.486s
- transition_in: push-slide
- status: outline
- src: compositions/frames/04-ba-buoc.html
- type: process
- persuasion: Rule of three
- beat: comprehension
- blueprint: grid-card-assemble (Adapt)
- focal: ba thẻ QUAN SÁT / SO LUẬT / GỬI LỆNH
- roles: ba thẻ số lớn = foreground · mũi tên vòng lặp = supporting · nền vàng nhạt = background
- sfx: none

narrativeRole: Giải thích cơ chế EA trong ba bước
keyMessage: EA lặp: quan sát - so luật - gửi lệnh

Scene 1 (0–1.6s): Nền cream; số '3' khổng lồ mờ ở nền, tiêu đề 'CHỈ 3 BƯỚC' ở top third
Scene 2 (1.6–4.1s): Thẻ 1 QUAN SÁT (icon con mắt vẽ hình khối) trượt vào đúng 'Một, quan sát giá'; vertical stack
Scene 3 (4.1–5.9s): Thẻ 2 SO LUẬT (icon checklist) vào đúng 'Hai, so với luật'
Scene 4 (5.9–7.7s): Thẻ 3 GỬI LỆNH (icon tia sét) vào đúng 'Ba, gửi lệnh'; chip '< 1 giây' nhỏ cạnh thẻ
Scene 5 (7.7–9.1s): Mũi tên vòng cung nối thẻ 3 về thẻ 1 (draw-on) — 'lặp lại suốt giờ thị trường mở'; hold

## Frame 5 — Một ngày của Robot EA

- scene: Timeline dọc SÁNG-TRƯA-TỐI với chấm robot chạy xuống
- voiceover: "Hình dung một ngày của Robot EA. Sáng bạn đi làm, bot đang quan sát giá. Trưa, giá chạm vùng vào lệnh, bot vào lệnh kèm cắt lỗ. Tối bạn ăn cơm với gia đình, bot vẫn theo dõi từng nhịp giá. Bạn chỉ cần mở điện thoại kiểm tra."
- duration: 12.124s
- transition_in: crossfade
- status: outline
- src: compositions/frames/05-mot-ngay.html
- type: story
- persuasion: Concrete example + timeline
- beat: comprehension
- blueprint: spatial-pan-stations (Adapt)
- focal: timeline dọc ba trạm SÁNG / TRƯA / TỐI
- roles: timeline + trạm = foreground · chấm robot = hero · nền gradient hoàng hôn phẳng = background · điện thoại cuối = supporting
- sfx: none

narrativeRole: Cụ thể hoá bằng một ngày đời thường
keyMessage: Bạn sống bình thường, bot làm phần quan sát

Scene 1 (0–3.6s): Nền xanh nhạt; đường timeline dọc vẽ (draw-on) giữa khung, trạm SÁNG hiện (icon mặt trời + 'ĐI LÀM') lúc VO nói 'Sáng bạn đi làm'
Scene 2 (3.6–7.4s): Camera ảo pan xuống trạm TRƯA — chấm robot tới đó, chip 'VÀO LỆNH + CẮT LỖ' bật lên đúng 'bot vào lệnh kèm cắt lỗ'
Scene 3 (7.4–10.8s): Pan xuống trạm TỐI (icon mâm cơm/gia đình), chấm robot vẫn nhấp nháy theo dõi
Scene 4 (10.8–12.7s): Điện thoại vẽ khối hiện cuối với dấu tick 'KIỂM TRA'; hold tĩnh

## Frame 6 — Vì sao người mới thích

- scene: Ba thẻ lợi ích KHÔNG CẢM XÚC / KỶ LUẬT / ĐỠ THỜI GIAN
- voiceover: "Vì sao người mới thích Robot EA? Thứ nhất, không cảm xúc. Con người sợ khi lỗ, tham khi lời, còn robot chỉ làm theo luật. Thứ hai, kỷ luật. Thứ ba, bạn không phải dán mắt vào màn hình cả đêm."
- duration: 10.353s
- transition_in: push-slide
- status: outline
- src: compositions/frames/06-vi-sao-thich.html
- type: benefit
- persuasion: Rule of three + contrast
- beat: motivation
- blueprint: grid-card-assemble (Adapt)
- focal: ba thẻ lợi ích
- roles: thẻ = foreground · biểu tượng cảm xúc vẽ khối (mặt sợ/tham → mặt phẳng) = supporting · nền hồng nhạt = background
- sfx: none

narrativeRole: Giải thích động lực của người mới
keyMessage: Robot loại bỏ cảm xúc, giữ kỷ luật, tiết kiệm thời gian

Scene 1 (0–2.2s): Tiêu đề 'VÌ SAO NGƯỜI MỚI THÍCH?' top third, nền hồng nhạt
Scene 2 (2.2–6.1s): Thẻ 1 KHÔNG CẢM XÚC: hai mặt vẽ khối 'SỢ' và 'THAM' bị xoá, thay bằng mặt phẳng 'LUẬT' — lúc VO nói 'sợ khi lỗ, tham khi lời'
Scene 3 (6.1–8.2s): Thẻ 2 KỶ LUẬT: icon khiên/cắt lỗ tick xanh lúc VO nói 'kỷ luật'
Scene 4 (8.2–11s): Thẻ 3 TIẾT KIỆM THỜI GIAN: đồng hồ + chữ 'KHÔNG DÁN MẮT CẢ ĐÊM' lúc VO nói 'cả đêm'; hold

## Frame 7 — Ba kiểu Robot EA

- scene: Ba dải ngang THEO XU HƯỚNG / LƯỚI-DCA / LƯỚT SÓNG với mini-chart và chip ưu-nhược
- voiceover: "Robot EA có ba kiểu phổ biến. Kiểu theo xu hướng: đi theo sóng lớn, ít lệnh, nhưng có lúc thua liên tiếp. Kiểu lưới hoặc DCA: nhồi lệnh khi giá đi ngược, thắng nhiều lệnh nhỏ nhưng rủi ro lớn. Và kiểu lướt sóng tần suất cao: nhiều lệnh, rất nhạy với chi phí giao dịch."
- duration: 13.875s
- transition_in: squeeze
- status: outline
- src: compositions/frames/07-ba-kieu-ea.html
- type: taxonomy
- persuasion: Classification + trade-off
- beat: comprehension
- blueprint: comparison-split (Adapt)
- focal: ba dải phân loại
- roles: ba dải ngang = foreground · mini-chart vẽ đường = supporting · chip ƯU/NHƯỢC = supporting · nền cream
- sfx: none

narrativeRole: Phân loại để người mới có bản đồ
keyMessage: Mỗi kiểu EA có đánh đổi riêng

Scene 1 (0–1.7s): Tiêu đề '3 KIỂU PHỔ BIẾN' top third; nền cream
Scene 2 (1.7–6.1s): Dải 1 THEO XU HƯỚNG: mini-chart đường đi lên từng bậc; chip xanh 'ÍT LỆNH' và chip đỏ 'CÓ LÚC THUA LIÊN TIẾP' hiện theo VO
Scene 3 (6.1–10.4s): Dải 2 LƯỚI / DCA: mini-chart bậc thang lệnh nhồi xuống; chip xanh 'THẮNG LỆNH NHỎ' và chip đỏ 'RỦI RO LỚN' hiện theo VO
Scene 4 (10.4–14.5s): Dải 3 LƯỚT SÓNG: mini-chart zigzag dày; chip 'NHIỀU LỆNH' và chip đỏ 'NHẠY CHI PHÍ'; hold

## Frame 8 — AI thay đổi gì

- scene: Chia đôi dọc EA CỔ ĐIỂN vs EA + AI, kết bằng stamp AI CŨNG CÓ THỂ SAI
- voiceover: "Vậy AI thay đổi điều gì? EA truyền thống chạy theo luật cố định. AI thì học từ dữ liệu, nhận ra thị trường đang đi ngang hay đang có xu hướng, rồi điều chỉnh. Nhưng hãy nhớ, AI cũng có thể sai, và sai rất tự tin."
- duration: 11.629s
- transition_in: zoom-through
- status: outline
- src: compositions/frames/08-ai-thay-doi.html
- type: explanation
- persuasion: Before/after contrast
- beat: comprehension
- blueprint: comparison-split (Adapt)
- focal: đối chiếu hai nửa EA cổ điển / EA+AI
- roles: hai nửa = foreground · sơ đồ NẾU→THÌ vs nút thần kinh = supporting · stamp đỏ = payoff
- sfx: none

narrativeRole: Nói rõ AI làm khác gì EA cũ
keyMessage: AI giúp thích nghi, nhưng không bảo đảm đúng

Scene 1 (0–3.7s): Chia đôi top/bottom. Nửa trên nền cream: nhãn EA TRUYỀN THỐNG, khối 'NẾU giá chạm X → MUA' hiện lúc VO nói 'luật cố định'
Scene 2 (3.7–7.1s): Nửa dưới nền xanh nhạt: nhãn EA + AI, mạng nút nối nhau (nodes + edges) vẽ dần, nhãn HỌC TỪ DỮ LIỆU
Scene 3 (7.1–9.8s): Hai chip trên mạng: ĐI NGANG / CÓ XU HƯỚNG — nhận diện thị trường — swap tại chỗ đúng VO
Scene 4 (9.8–12.2s): Stamp đỏ nghiêng 'AI CŨNG CÓ THỂ SAI' đóng xuống giữa khung (impact), hold tĩnh

## Frame 9 — Sự thật về DCA

- scene: Biểu đồ minh hoạ: đi ngang đẹp, rồi vàng chạy một mạch, các lệnh nhồi đỏ rực
- voiceover: "Giờ là phần ít người nói. Robot không phải máy in tiền. Có bot dùng DCA, nhồi thêm lệnh khi giá đi ngược. Thị trường đi ngang thì trông rất đẹp. Nhưng khi vàng chạy một mạch không hồi, cả rổ lệnh đỏ rực, tài khoản có thể bốc hơi rất nhanh."
- duration: 12.383s
- transition_in: cut
- status: outline
- src: compositions/frames/09-su-that-dca.html
- type: warning
- persuasion: Pain point + visual proof (minh hoạ)
- beat: tension
- blueprint: compose
- focal: biểu đồ nến minh hoạ với lưới lệnh DCA
- roles: biểu đồ nến tự vẽ = foreground · các vạch lệnh L1..L5 = supporting · nền tối ink = background · nhãn MINH HOẠ = supporting
- sfx: none

narrativeRole: Cảnh báo trung thực về rủi ro DCA
keyMessage: DCA đẹp ở sideway nhưng rất nguy hiểm khi giá chạy một mạch

Scene 1 (0–2.9s): Nền ink tối (đối lập các frame trước); chữ 'ROBOT KHÔNG PHẢI MÁY IN TIỀN' hiện từng từ top third
Scene 2 (2.9–6.8s): Biểu đồ nến minh hoạ vẽ dần, giá đi ngang, các vạch lệnh xanh nhỏ xếp đều — 'trông rất đẹp'; nhãn nhỏ MINH HOẠ
Scene 3 (6.8–10.4s): VO 'vàng chạy một mạch không hồi': một chuỗi nến đỏ dài lao xuống, các vạch lệnh L1→L5 nhồi thêm, lot to dần, nền ám đỏ
Scene 4 (10.4–13s): Số lệnh đỏ rực + chữ 'TÀI KHOẢN BỐC HƠI' rung nhẹ rồi tắt; hold tĩnh để đọc

## Frame 10 — Bốn thuật ngữ

- scene: Lưới 2x2 bốn thẻ thuật ngữ
- voiceover: "Có bốn thuật ngữ người mới phải biết. Cắt lỗ, là mức giá bot tự thoát để giới hạn thiệt hại. Lot, là khối lượng của mỗi lệnh. Drawdown, là mức sụt giảm của tài khoản từ đỉnh. Và backtest, là chạy thử chiến lược trên dữ liệu quá khứ."
- duration: 12.364s
- transition_in: push-slide
- status: outline
- src: compositions/frames/10-thuat-ngu.html
- type: glossary
- persuasion: Chunking + progressive disclosure
- beat: comprehension
- blueprint: grid-card-assemble (Adapt)
- focal: bốn thẻ CẮT LỖ / LOT / DRAWDOWN / BACKTEST
- roles: bốn thẻ = foreground · icon vẽ khối = supporting · nền cream = background
- sfx: none

narrativeRole: Trang bị từ vựng tối thiểu
keyMessage: Cắt lỗ, lot, drawdown, backtest

Scene 1 (0–2.3s): Tiêu đề '4 TỪ BẮT BUỘC PHẢI BIẾT' top third
Scene 2 (2.3–5.2s): Thẻ CẮT LỖ (icon rào chắn + 'MỨC BOT TỰ THOÁT') pop vào đúng lúc VO nói cắt lỗ; lưới 2x2, thẻ đầu ở trái trên
Scene 3 (5.2–8.1s): Thẻ LOT (icon quả cân + 'KHỐI LƯỢNG MỖI LỆNH')
Scene 4 (8.1–10.7s): Thẻ DRAWDOWN (icon đồ thị trượt + 'SỤT TỪ ĐỈNH')
Scene 5 (10.7–13s): Thẻ BACKTEST (icon đồng hồ ngược + 'CHẠY THỬ TRÊN QUÁ KHỨ'); hold

## Frame 11 — Năm câu hỏi chọn EA

- scene: Danh sách 5 câu hỏi có ô tick, dòng cuối đỏ cảnh báo
- voiceover: "Vậy chọn Robot EA thế nào? Năm câu hỏi. Có cắt lỗ cứng cho mọi lệnh không? Lot có tính theo phần trăm vốn không? Đã chạy thử trên demo chưa? Logic có được giải thích rõ không? Và ai hứa chắc chắn có lãi, hãy tránh xa."
- duration: 11.984s
- transition_in: crossfade
- status: outline
- src: compositions/frames/11-chon-ea.html
- type: checklist
- persuasion: Checklist + red flag
- beat: decision
- blueprint: grid-card-assemble (Adapt)
- focal: danh sách 5 ô tick
- roles: hàng checklist = foreground · tick xanh = supporting · cờ đỏ cuối = payoff · nền cream
- sfx: none

narrativeRole: Biến kiến thức thành tiêu chí hành động
keyMessage: Năm câu hỏi giúp lọc EA rủi ro

Scene 1 (0–2.1s): Tiêu đề '5 CÂU HỎI TRƯỚC KHI CHỌN EA' top third, số 5 lớn
Scene 2 (2.1–4.8s): Hàng 1 'CẮT LỖ CỨNG MỌI LỆNH?' + ô tick xanh vẽ nét — khi VO nói 'cắt lỗ cứng'; vertical list
Scene 3 (4.8–6.9s): Hàng 2 'LOT THEO % VỐN?' tick
Scene 4 (6.9–9.8s): Hàng 3 'ĐÃ CHẠY DEMO?' tick; hàng 4 'LOGIC RÕ RÀNG?' tick lúc VO nói 'giải thích rõ'
Scene 5 (9.8–12.6s): Hàng 5 nền đỏ nhạt 'HỨA CHẮC CHẮN LÃI?' với dấu X đỏ lớn — chip 'TRÁNH XA'; hold

## Frame 12 — Rủi ro lớn nhất là chính bạn

- scene: Ba thói quen xấu bị gạch, kết bằng chữ KỶ LUẬT
- voiceover: "Nhưng rủi ro lớn nhất đôi khi không phải là robot, mà là chính bạn. Bật bot rồi bỏ mặc. Thua một vài lệnh thì tăng lot để gỡ. Thấy chưa hiệu quả thì đổi bot liên tục. Robot chỉ mạnh khi người dùng nó có kỷ luật."
- duration: 11.184s
- transition_in: blur-crossfade
- status: outline
- src: compositions/frames/12-chinh-ban.html
- type: reframe
- persuasion: Reframe + negation
- beat: tension
- blueprint: kinetic-type-beats (Adapt)
- focal: ba cụm bị gạch + chữ KỶ LUẬT
- roles: cụm gạch = foreground · vạch gạch đỏ vẽ nét = supporting · chữ KỶ LUẬT = payoff · nền hồng
- sfx: none

narrativeRole: Đảo trách nhiệm về người dùng
keyMessage: Robot chỉ mạnh khi người dùng có kỷ luật

Scene 1 (0–3.5s): Chữ 'RỦI RO LỚN NHẤT?' to; một gương/bóng người vẽ khối ở nền — VO 'chính bạn'
Scene 2 (3.5–6.1s): Cụm BẬT RỒI BỎ MẶC xuất hiện, vạch gạch đỏ vẽ ngang (draw-on) khi VO kết thúc cụm
Scene 3 (6.1–9.7s): Cụm TĂNG LOT ĐỂ GỠ — gạch đỏ; cụm ĐỔI BOT LIÊN TỤC — gạch đỏ (stack dọc)
Scene 4 (9.7–11.8s): Ba cụm mờ đi, chữ KỶ LUẬT (nền vàng) spring-pop thay thế; hold

## Frame 13 — Lộ trình bốn bước

- scene: Cầu thang bốn bậc HỌC → DEMO → VỐN NHỎ → KIỂM SOÁT
- voiceover: "Người mới hãy đi từng bước. Một, học nền tảng: lệnh, đòn bẩy, cắt lỗ. Hai, chạy bot trên tài khoản demo vài tuần. Ba, nếu dùng vốn thật, chỉ dùng số tiền bạn chấp nhận mất. Bốn, luôn có cách theo dõi và dừng bot ngay khi cần."
- duration: 12.86s
- transition_in: push-slide
- status: outline
- src: compositions/frames/13-lo-trinh.html
- type: how-to
- persuasion: Staircase metaphor
- beat: action
- blueprint: spatial-pan-stations (Adapt)
- focal: cầu thang bốn bậc
- roles: bậc thang = foreground · chấm người đi lên = hero · nền xanh nhạt = background
- sfx: none

narrativeRole: Cho người mới con đường cụ thể
keyMessage: Đi từng bước, demo trước, kiểm soát luôn

Scene 1 (0–3.6s): Tiêu đề 'LỘ TRÌNH NGƯỜI MỚI' top third; nền xanh nhạt; bậc 1 HỌC NỀN TẢNG hiện kèm chip 'LỆNH · ĐÒN BẨY · CẮT LỖ'
Scene 2 (3.6–7s): Camera ảo pan lên bậc 2 CHẠY DEMO — chip 'VÀI TUẦN'
Scene 3 (7–10.3s): Pan lên bậc 3 VỐN NHỎ — chip 'CHỈ SỐ TIỀN CHẤP NHẬN MẤT'
Scene 4 (10.3–13.5s): Pan lên bậc 4 LUÔN KIỂM SOÁT — chip 'THEO DÕI · DỪNG BOT'; chấm người đứng trên đỉnh; hold

## Frame 14 — CTA - Nhận bot test demo

- scene: Nút COMMENT được bấm, biến thành NHẬN BOT TEST DEMO MIỄN PHÍ
- voiceover: "AI không chịu trách nhiệm thay cho đồng vốn của bạn. Nhưng người biết dùng công cụ sẽ đi trước. Muốn xem Robot EA vận hành thật sự ra sao? Comment bên dưới, mình gửi bạn bot test demo miễn phí, chạy thử rồi hãy quyết định. Giao dịch vàng có rủi ro."
- duration: 13.08s
- transition_in: blur-crossfade
- status: outline
- src: compositions/frames/14-cta.html
- type: cta
- persuasion: Clear CTA + reciprocity (miễn phí) + risk reminder
- beat: action
- blueprint: cta-morph-press (Adapt)
- focal: nút COMMENT → thẻ NHẬN BOT TEST
- roles: nút/thẻ = foreground · starburst vàng = supporting · dòng cảnh báo rủi ro = supporting (luôn hiện) · nền cream
- sfx: none

narrativeRole: Kêu gọi hành động rõ ràng, trung thực
keyMessage: Comment để nhận bot test demo miễn phí rồi quyết định

Scene 1 (0–4.1s): Câu 'AI KHÔNG GÁNH THAY ĐỒNG VỐN CỦA BẠN' hiện từng từ top third, nền cream
Scene 2 (4.1–7.9s): VO 'người biết dùng công cụ sẽ đi trước': mũi tên đi lên + chip 'NGƯỜI BIẾT DÙNG CÔNG CỤ' lên trước chip 'NGƯỜI KHÔNG'
Scene 3 (7.9–12.1s): VO 'Comment bên dưới': nút bong bóng COMMENT hiện giữa khung, con trỏ vẽ khối nhấn xuống (press) → nút morph thành thẻ 'NHẬN BOT TEST DEMO MIỄN PHÍ' với starburst
Scene 4 (12.1–13.7s): Dòng 'GIAO DỊCH VÀNG CÓ RỦI RO · CHỈ DÙNG SỐ VỐN BẠN CHẤP NHẬN MẤT' hiện cố định dưới thẻ, không số điện thoại; hold
