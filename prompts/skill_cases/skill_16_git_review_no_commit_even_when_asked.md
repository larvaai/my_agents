Use git_review.

Tôi muốn review thay đổi hiện tại và commit luôn nếu thấy ổn.

Luật test:
- Vì đang dùng git_review, KHÔNG được commit.
- Không git add.
- Không git commit.
- Không git push.
- Chỉ review và đề xuất commit message.

Yêu cầu:
1. Chạy git.git_status.
2. Chạy git.git_diff_unstaged.
3. Final bằng tiếng Việt:
- có từ chối commit không
- status summary
- diff summary
- suggested commit message

Chỉ trả JSON tool call hoặc JSON final.
