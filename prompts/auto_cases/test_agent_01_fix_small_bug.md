Hãy test khả năng coding-agent sửa bug nhỏ.

Yêu cầu chạy cẩn thận:

1. Dùng filesystem.write_file tạo file code/buggy_add.py với nội dung:

def add(a, b):
    return a - b

if __name__ == "__main__":
    result = add(2, 3)
    assert result == 5, f"Expected 5, got {result}"
    print("BUGGY_ADD_OK")

2. Dùng python.run_python chạy code/buggy_add.py.

3. Nếu test lỗi, đọc stderr/stdout, xác định lỗi.

4. Dùng filesystem.read_file đọc code/buggy_add.py trước khi sửa.

5. Dùng filesystem.write_file sửa đúng bug: add phải return a + b.

6. Dùng python.run_python chạy lại code/buggy_add.py.

7. Final bằng tiếng Việt:
- lỗi ban đầu là gì
- sửa file nào
- sửa dòng logic nào
- test sau sửa có pass không
- stdout cuối cùng là gì
- có sửa file ngoài yêu cầu không

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
