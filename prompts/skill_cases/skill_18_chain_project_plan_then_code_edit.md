Use project_plan first, then use code_edit.

Mục tiêu:
Tạo file code/skill_chain_plan_edit.py in ra "CHAIN_PLAN_EDIT_OK".

Quy trình bắt buộc:
1. Giai đoạn project_plan:
   - Chỉ lập kế hoạch.
   - Không write file trong giai đoạn này.
   - Final tạm không được trả, phải chuyển sang bước code_edit sau khi đã nêu plan.
2. Giai đoạn code_edit:
   - Tạo file code/skill_chain_plan_edit.py.
   - Chạy python.run_python.
3. Final bằng tiếng Việt:
   - plan đã nêu gì
   - file đã tạo
   - test đã chạy
   - stdout
   - có sửa ngoài phạm vi không

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
