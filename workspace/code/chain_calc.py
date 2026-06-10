def net_score(base, bonus, penalty):
    return base + bonus - penalty

if __name__ == "__main__":
    assert net_score(10, 5, 3) == 12
    print("CHAIN_DOC_FS_PY_LEDGER_OK")
