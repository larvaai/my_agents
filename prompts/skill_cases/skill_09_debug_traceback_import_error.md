Use debug_traceback.

Yêu cầu:

1. Tạo file code/skill_debug_import.py với nội dung:

import module_that_does_not_exist

print("IMPORT_OK")

2. Chạy python.run_python để lấy traceback thật.
3. Dựa trên traceback, xác định root cause.
4. Đọc file.
5. Sửa nhỏ nhất để file chạy được bằng cách bỏ import sai.
6. Chạy lại.
7. Final bằng tiếng Việt:
- traceback nói lỗi gì
- root cause
- file sửa
- test sau sửa pass chưa
- stdout cuối là gì

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
