import argparse
import json

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

    print(alloc)
    print(env)
    print(txs)

if __name__ == "__main__":
    main()
