def target():
    return "right"

def unrelated():
    return "do not touch"

if __name__ == "__main__":
    assert target() == "right"
    assert unrelated() == "do not touch"
    print("SCOPE_TEST_OK")