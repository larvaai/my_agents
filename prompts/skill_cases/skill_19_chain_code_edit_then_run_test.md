Use code_edit, then use run_test.

Yêu cầu:
1. Dùng code_edit tạo file code/skill_chain_edit_test.py với nội dung:

def value():
    return "CHAIN_EDIT_TEST_OK"

if __name__ == "__main__":
    print(value())

2. Dùng run_test để validate file bằng python.run_python.
3. Final bằng tiếng Việt:
- code_edit đã tạo file nào
- run_test đã chạy command/tool nào
- result class
- stdout
- có sửa ngoài phạm vi không

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
