Use debug_traceback.

Yêu cầu:

1. Tạo file code/skill_debug_syntax.py với nội dung lỗi syntax:

def broken_func()
    return "ok"

if __name__ == "__main__":
    print(broken_func())

2. Chạy python.run_python để lấy SyntaxError.
3. Đọc stderr từ dưới lên.
4. Đọc file.
5. Sửa nhỏ nhất để code hợp lệ.
6. Chạy lại.
7. Final bằng tiếng Việt:
- exception type
- dòng lỗi
- fix applied
- stdout cuối
- có sửa ngoài file này không

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
