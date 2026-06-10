Use debug_traceback.

Đây là traceback giả lập:

Traceback (most recent call last):
  File "D:\Agent PRJ\my_agents\workspace\code\divide_test.py", line 7, in <module>
    print(divide(10, 0))
  File "D:\Agent PRJ\my_agents\workspace\code\divide_test.py", line 2, in divide
    return a / b
ZeroDivisionError: division by zero

Yêu cầu:
1. Tạo file code/divide_test.py đúng như traceback giả lập:

def divide(a, b):
    return a / b

if __name__ == "__main__":
    print(divide(10, 0))

2. Chạy python.run_python để tái hiện lỗi.

3. Đọc file.

4. Sửa nhỏ nhất để nếu b == 0 thì return None.

5. Chạy lại.

6. Final bằng tiếng Việt:
- root cause
- file sửa
- test trước/sau
- stdout/stderr sau sửa

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
