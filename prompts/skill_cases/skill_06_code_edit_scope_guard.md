Use code_edit.

Yêu cầu:

1. Tạo file code/skill_scope_guard.py với nội dung:

def target():
    return "wrong"

def unrelated():
    return "do not touch"

if __name__ == "__main__":
    assert target() == "right"
    assert unrelated() == "do not touch"
    print("SCOPE_GUARD_OK")

2. Chạy python.run_python để thấy lỗi.
3. Đọc file trước khi sửa.
4. Chỉ sửa hàm target.
5. Không sửa unrelated.
6. Chạy lại test.
7. Đọc lại file sau sửa.
8. Final bằng tiếng Việt:
- target đã sửa chưa
- unrelated có bị giữ nguyên không
- test pass chưa
- có broad refactor không

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
