Use debug_traceback.

Đây là traceback giả lập:

Traceback (most recent call last):
  File "D:\Agent PRJ\my_agents\workspace\code\skill_debug_divide.py", line 5, in <module>
    print(divide(10, 0))
  File "D:\Agent PRJ\my_agents\workspace\code\skill_debug_divide.py", line 2, in divide
    return a / b
ZeroDivisionError: division by zero

Yêu cầu:
1. Tạo file code/skill_debug_divide.py đúng như traceback:

def divide(a, b):
    return a / b

if __name__ == "__main__":
    print(divide(10, 0))

2. Chạy python.run_python để tái hiện lỗi.
3. Đọc traceback từ dưới lên.
4. Đọc file.
5. Sửa nhỏ nhất: nếu b == 0 thì return None.
6. Chạy lại.
7. Final bằng tiếng Việt:
- exception type
- root cause
- file sửa
- fix applied
- test command run
- remaining failure nếu có

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
