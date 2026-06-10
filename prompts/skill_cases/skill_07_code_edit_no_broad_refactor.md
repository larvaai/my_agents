Use code_edit.

Yêu cầu:

1. Tạo file code/skill_no_refactor.py với nội dung:

def calculate_price(base):
    tax = 0.1
    return base + tax

def helper_one():
    return "keep"

def helper_two():
    return "keep"

if __name__ == "__main__":
    assert calculate_price(100) == 110
    assert helper_one() == "keep"
    assert helper_two() == "keep"
    print("NO_REFACTOR_OK")

2. Chạy file để thấy lỗi.
3. Đọc file.
4. Sửa nhỏ nhất để calculate_price(100) == 110.
5. Không đổi tên hàm.
6. Không sắp xếp lại file.
7. Không sửa helper_one/helper_two.
8. Chạy lại test.
9. Final bằng tiếng Việt:
- sửa nhỏ nhất là gì
- có tránh refactor không
- test pass chưa

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
