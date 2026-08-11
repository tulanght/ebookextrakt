---
name: start-electron
description: Khởi tạo và chạy phiên làm việc cho nhánh UI bằng Electron.
---

# Start Electron Workspace

Khi người dùng chạy `/start-electron`, hãy thực hiện các bước sau:

1. Đọc nội dung file `docs/ai/implementation/electron-handover.md` để nắm các Guardrails và Rule.
2. Đảm bảo nhánh hiện tại là `feature/electron-ui`.
3. Kiểm tra xem môi trường ảo Python đã được kích hoạt chưa (`venv`).
4. Hướng dẫn người dùng cách chạy đồng thời Backend và Frontend:
   - Backend: `.\venv\Scripts\python.exe -m uvicorn src.extract_app.api.main:app --reload`
   - Frontend: Mở terminal mới, `cd electron` và `npm run dev`
5. Phân tích các lỗi mới nhất (nếu có) hoặc hỏi người dùng muốn thực hiện chức năng tiếp theo là gì.

