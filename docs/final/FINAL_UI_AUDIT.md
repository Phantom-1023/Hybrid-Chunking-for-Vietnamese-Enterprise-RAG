# FINAL UI AUDIT — v1.0.5 baseline

Ngày audit: 13/08/2026. Đây là static/source audit có đối chiếu với template UI, JavaScript và regression tests. Không có live visual run-through trong task này: attempt khởi chạy server local bị lớp quyền thực thi từ chối trước khi có process, nên không lặp lại bằng workaround.

## Màn hình mạnh nhất

1. **Login/setup**: cấu trúc form gọn, `required`, `type=email`, password minlength, autocomplete và toast `aria-live`; tách rõ login, setup và registration visibility.
2. **Hỏi đáp/citation**: chat nêu boundary “chỉ dùng nguồn bạn có quyền truy cập”, citations có locator, source name/excerpt và mở được source drawer/download.
3. **Quản trị người dùng/phòng ban**: có metrics, filter, pagination, role badge, profile drawer, quản lý user/departments và UI được role-gate.
4. **Quản lý tài liệu**: có filter, scope, department selector, labels/grants trong editor và upload giới hạn định dạng/15 MB được thông báo.
5. **Nhật ký/audit**: có màn hình riêng và API admin-protected; phù hợp câu chuyện auditability của capstone.

## Màn hình/luồng yếu nhất

1. **Loading/error states toàn app**: không có pending visual, retry hoặc stale-state; Admin/Audit đặc biệt dễ im lặng khi API lỗi.
2. **Destructive/admin flows**: native `confirm()`/`prompt()` không cùng visual system và không đủ context cho demo.
3. **Narrow/mobile**: chỉ có một breakpoint 900px; chưa có screenshot/QA evidence ở màn hình hẹp.
4. **Drawer/menu accessibility**: drawer chưa là dialog có quản trị focus/Escape; account/more menu chưa có `aria-expanded`.
5. **Release polish**: resource query string `semi-ver1.0.4` và version `0.1.0` làm bề mặt UI/release có dấu hiệu stale.

## Top 5 vấn đề trực quan

1. Nhãn cache `semi-ver1.0.4` còn nằm trong HTML resource URL, không nhất quán với line v1.0.5.
2. Không có visual loading/skeleton/disabled state cho các thao tác async quan trọng.
3. Empty state mới rõ ở Documents; Audit và một số list admin không có thông điệp empty/error nhất quán.
4. Dialog native của browser cho rename/reset/delete không tuân theo typography, spacing và màu của KnowledgeOS.
5. Chưa có evidence screenshot desktop/narrow/mobile nên không thể xác nhận spacing/overflow/contrast bằng mắt.

## Top 5 vấn đề tương tác

1. Submit login/search/upload/admin mutation có thể bị lặp click khi request chậm.
2. Navigation vào Admin/Audit có thể gặp lỗi promise không được chuyển thành feedback UI.
3. Drawer không có Escape close/focus return; keyboard user có thể mất ngữ cảnh.
4. Delete/reset/rename phụ thuộc `confirm()`/`prompt()` và không cho preview đầy đủ đối tượng/hậu quả.
5. Chat không biểu đạt rõ state “không có evidence trong quyền hiện tại” như một empty outcome riêng biệt.

## Hướng thiết kế final được khuyến nghị

Giữ visual language hiện có: KnowledgeOS tối giản, sidebar xanh đậm, surfaces trắng, green accent và drawer bên phải. Không redesign. Trước tiên chuẩn hóa trạng thái (idle/loading/success/empty/error) cho cùng component primitives, sau đó thay native destructive dialogs bằng một confirmation drawer/modal nhẹ, rồi thực hiện visual QA theo ba breakpoint. Mọi chỉnh sửa phải giữ citation visibility, role gating và ACL-first behavior hiện tại.

## Giới hạn bằng chứng

Nhận định về layout/responsive là suy luận từ HTML/CSS, không phải xác nhận render pixel-perfect. Baseline product test đã pass nhưng các test đó không thay thế manual visual QA. Mục P2-02 trong backlog là bước cần làm sau khi PM phê duyệt triển khai.
