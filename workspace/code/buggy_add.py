def add(a, b):
    return a + b

if __name__ == "__main__":
    result = add(2, 3)
    assert result == 5, f"Expected 5, got {result}"
    print("BUGGY_ADD_OK")