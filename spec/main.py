import argparse
import json
import spec

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--input.alloc', dest='alloc', action='store')
    parser.add_argument('--input.env', dest='env', action='store')
    parser.add_argument('--input.txs', dest='txs', action='store')

    args = parser.parse_args()

    with open(args.alloc) as f:
      alloc = json.load(f)
    with open(args.env) as f:
      env = json.load(f)
    with open(args.txs) as f:
      txs = json.load(f)

    state = {}
    for (addr, vals) in alloc.items():
        account = spec.Account(
            nonce=vals.get('nonce', 0),
            balance=vals.get('balance', 0),
            code=bytes.fromhex(vals.get('code', '')).decode('utf-8'),
            storage={} # TODO: support storage
        )
        state[addr] = account

    print(spec.apply_body(state, env['currentGasLimit'], [], []))

if __name__ == "__main__":
    main()
