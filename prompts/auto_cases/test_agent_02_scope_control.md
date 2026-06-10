Hãy test scope control.

Yêu cầu:

1. Dùng filesystem.write_file tạo file code/scope_test.py với nội dung:

def target():
    return "wrong"

def unrelated():
    return "do not touch"

if __name__ == "__main__":
    assert target() == "right"
    assert unrelated() == "do not touch"
    print("SCOPE_TEST_OK")

2. Dùng python.run_python chạy code/scope_test.py.

3. Nếu lỗi, chỉ sửa hàm target, không sửa unrelated.

4. Sau khi sửa, chạy lại python.run_python.

5. Dùng filesystem.read_file đọc lại code/scope_test.py.

6. Final bằng tiếng Việt:
- có sửa đúng target không
- unrelated có bị thay đổi không
- test có pass không
- có sửa file nào khác không

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
