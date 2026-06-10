# Workflow: Debug Failed Test

## Goal

Debug test fail theo kiểu có bằng chứng, không sửa đại trà.

## Steps

1. Mở log:

```powershell
Get-Content test_runs\<timestamp>\<case>.log
```

2. Xác định failure:

- Missing expected?
- Forbidden found?
- Return code non-zero?
- Agent JSON invalid?
- Tool result `ok=false`?

3. Nếu tool fail, đọc `error`, `stdout`, `stderr`.

4. Nếu code fail:

- Dùng Code Index tìm symbol/reference.
- Dùng File Editor view file liên quan.
- Tạo/rerun probe nhỏ nếu nguyên nhân chưa rõ.
- Sửa nhỏ.
- Chạy validation hẹp.

5. Nếu dependency fail:

- Báo dependency failure.
- Không sửa code logic.

## Useful Commands

```powershell
python inspect_runs.py list
python inspect_runs.py events latest --limit 30
python run_all_cases.py --case <case> --fail-fast
```

## Anti-patterns

- Đổi path liên tục không đọc lỗi.
- Rerun cùng tool + args nhiều lần.
- Refactor rộng để sửa lỗi nhỏ.
- Final khi chưa validation pass.

