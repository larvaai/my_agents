Use code_edit.

Yêu cầu chạy lần lượt:

1. Dùng filesystem.write_file tạo file code/skill_code_edit_existing.py với nội dung:

VALUE = "wrong"

def get_value():
    return VALUE

if __name__ == "__main__":
    assert get_value() == "right"
    print("CODE_EDIT_EXISTING_OK")

2. Dùng python.run_python chạy file để thấy test fail.
3. Trước khi sửa, phải dùng filesystem.read_file đọc file.
4. Sửa nhỏ nhất: đổi VALUE từ "wrong" thành "right".
5. Chạy lại python.run_python.
6. Final bằng tiếng Việt:
- đã đọc file trước khi sửa chưa
- sửa dòng nào
- test trước/sau thế nào
- stdout cuối là gì
- có sửa file ngoài yêu cầu không

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
