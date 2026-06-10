Use debug_traceback, then git_review.

Yêu cầu:
1. Tạo file code/skill_chain_debug_git.py với nội dung:

def value():
    return 1 / 0

if __name__ == "__main__":
    print(value())

2. Chạy python.run_python để lấy traceback.
3. Dùng debug_traceback sửa nhỏ nhất: value() return None thay vì chia 0.
4. Chạy lại.
5. Sau khi pass, dùng git_review:
   - git.git_status
   - git.git_diff_unstaged
   - không commit
6. Final bằng tiếng Việt:
- root cause
- file sửa
- stdout sau sửa
- git status summary
- suggested commit message

Chỉ trả JSON tool call hoặc JSON final.
