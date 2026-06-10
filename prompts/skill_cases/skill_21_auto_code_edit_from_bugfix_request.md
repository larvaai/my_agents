Tôi có một bug nhỏ cần sửa, nhưng không nói alias skill.

Yêu cầu:
1. Tạo file code/skill_auto_bugfix.py với nội dung:

def is_ready():
    return False

if __name__ == "__main__":
    assert is_ready() is True
    print("AUTO_CODE_EDIT_OK")

2. Chạy file để thấy lỗi.
3. Tự dùng đúng logic của code_edit/debug nếu cần.
4. Đọc file trước khi sửa.
5. Sửa nhỏ nhất: is_ready return True.
6. Chạy lại.
7. Final bằng tiếng Việt:
- agent có hiểu đây là bugfix/code_edit không
- file đọc/sửa
- test trước/sau
- stdout cuối

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
