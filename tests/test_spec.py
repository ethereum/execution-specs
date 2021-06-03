from eth1spec.spec import Account, State, get_account


def test_get_account():
    account = Account(
        nonce=0,
        balance=1,
        code_hash=b"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    )

    state = State()
    state[b"aaaaaaaaaaaaaaaaaaaa"] = account

    actual = get_account(state, b"aaaaaaaaaaaaaaaaaaaa")

    assert actual.nonce == 0
    assert actual.balance == 1
    assert actual.code_hash == b"yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
