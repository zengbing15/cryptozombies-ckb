#/usr/bin/env python3
#coding: utf-8

import json
import sys
import os
import subprocess
import time

SENDER1 = "0xbd201ecf986127c0cb166601aff05558ae5ce89f"
SENDER1_PRIVKEY = "273f4620c7de18839970183916a5d1b8fa4bdfa2c3afdd2ff72f4fdfb44d56fe013e71994d66d9192e754b2b2c837ebc34288d7e6265bbbd3d7678bde2e6ba66"
eoa_accounts = {}

def send_jsonrpc(url, method, params=[]):
    payload = {
        "id": 0,
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
    }
    cmd = "curl -s -H 'content-type: application/json' -d '{}' {}".format(json.dumps(payload), url)
    output = subprocess.check_output(cmd, shell=True).strip().decode("utf-8")
    resp = json.loads(output)
    if "error" in resp:
        raise ValueError("JSONRPC ERROR: {}".format(resp["error"]))
    return resp["result"]

def create_contract(url, binary, constructor_args="", sender=SENDER1, account_index=0, value=0):
    eoa_account = eoa_accounts[sender][account_index]
    print("[create contract]:")
    print("  sender = {}".format(sender))
    print("  account = {}".format(eoa_account))
    print("  binary = 0x{}".format(binary))
    print("    args = 0x{}".format(constructor_args))
    result = send_jsonrpc(url, "create", [eoa_account, "0x{}{}".format(binary, constructor_args), value])
    print("  >> created address = {}".format(result["entrance_contract"]))
    return result

def call_contract(url, contract_address, args, is_static=False, sender=SENDER1, account_index=0, value=0):
    eoa_account = eoa_accounts[sender][account_index]
    method = "static_call" if is_static else "call"
    print("[{} contract]:".format(method))
    print("   sender = {}".format(sender))
    print("  account = {}".format(eoa_account))
    print("  address = {}".format(contract_address))
    print("     args = {}".format(args))
    return send_jsonrpc(url, method, [eoa_account, contract_address, args, value])

def mine_blocks(ckb_bin_path, ckb_dir, n=4):
    run_cmd("{} miner -C {} -l {}".format(ckb_bin_path, ckb_dir, n))
    time.sleep(1)

def run_cmd(cmd, print_output=True):
    print("[RUN]: {}".format(cmd))
    output = subprocess.check_output(cmd, shell=True, env=os.environ).strip().decode("utf-8")
    if print_output:
        print("[Output]: {}".format(output))
    return output

def commit_tx(target_dir, ckb_bin_path, ckb_dir, ckb_rpc_url, privkey_path, result, polyjuice_rpc_url, action_name):
    result_path = os.path.join(target_dir, "{}.json".format(action_name))
    with open(result_path, "w") as f:
        json.dump(result, f, indent=4)
    tx_path = os.path.join(target_dir, "{}-tx.json".format(action_name))
    tx_raw_path = os.path.join(target_dir, "{}-raw-tx.json".format(action_name))
    # tx_moack_path = os.path.join(target_dir, "{}-mock-tx.json".format(action_name))
    run_cmd("polyjuice sign-tx --url {} -k {} -t {} -o {}".format(ckb_rpc_url, privkey_path, result_path, tx_path))
    run_cmd("cat {} | jq .transaction > {}".format(tx_path, tx_raw_path))
    # run_cmd("ckb-cli mock-tx dump --tx-file {} --output-file {}".format(tx_raw_path, tx_moack_path))
    for retry in range(3):
        os.environ["API_URL"] = ckb_rpc_url
        tx_hash = run_cmd("ckb-cli tx send --tx-file {} --skip-check".format(tx_path)).strip()
        mine_blocks(ckb_bin_path, ckb_dir)
        tx_content = run_cmd("ckb-cli rpc get_transaction --hash {}".format(tx_hash), print_output=False)
        if tx_content.find(tx_hash) > -1:
            print("Transaction sent: {}".format(tx_hash))
            break;
        print("Retry send transaction: {}".format(retry))

    contract_address = result["entrance_contract"]
    tx_hash = result["tx_hash"]
    for retry in range(10):
        current_tx_hash = None
        try:
            change = send_jsonrpc(polyjuice_rpc_url, "get_change", [contract_address, None])
            current_tx_hash = change["tx_hash"]
        except ValueError:
            pass
        if current_tx_hash != tx_hash:
            time.sleep(0.5)
            print("Waiting for polyjuice to index transaction: {}, retry: {} ...".format(tx_hash, retry))
        else:
            print("Transaction indexed: {}".format(tx_hash))
            break

def get_code(path):
    with open(path) as f:
        data = json.load(f)
        return data['bytecode'][2:]

def addr_to_arg(addr):
    return "000000000000000000000000{}".format(addr[2:])

def gen_node(name):
    return hexlify(namehash(name)).decode('utf-8')

def gen_label(name):
    return hexlify(sha3(name)).decode('utf-8')


def call(target_dir, ckb_bin_path, ckb_rpc_url, polyjuice_rpc_url, ckb_dir, privkey_path,
         addr, fn_name, args, name):
    args = ''.join(['0x', fn_name, *args])
    result = call_contract(polyjuice_rpc_url, addr, args)
    commit_tx(
        target_dir, ckb_bin_path, ckb_dir, ckb_rpc_url, privkey_path,
        result,
        polyjuice_rpc_url,
        'call-{}-{}'.format(name, args)[:45],
    )
    return result

def main(target_dir, ckb_bin_path, ckb_rpc_url, polyjuice_rpc_url, ckb_dir, privkey1_path):
    def local_commit_tx(result, action_name):
        commit_tx(
            target_dir, ckb_bin_path, ckb_dir, ckb_rpc_url, privkey1_path,
            result,
            polyjuice_rpc_url,
            action_name,
        )

    def local_call(addr, fn_name, args, name):
        return call(
            target_dir, ckb_bin_path, ckb_rpc_url, polyjuice_rpc_url, ckb_dir, privkey1_path,
            addr, fn_name, args, name,
        )

def gen_eoa_accounts(ckb_bin_path, ckb_dir, ckb_rpc_url, sender, privkey_path):
    balance = "1000.0"
    output = run_cmd("polyjuice new-eoa-account --url {} -k {} --balance {}".format(
        ckb_rpc_url, privkey_path, balance,
    ))
    eoa_address = output.strip().splitlines()[-1]
    mine_blocks(ckb_bin_path, ckb_dir)
    if sender not in eoa_accounts:
        eoa_accounts[sender] = []
    eoa_accounts[sender].append(eoa_address)


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('USAGE:\n  python3 deploy.py <tmp-dir> <ckb-binary-path> <ckb-rpc-url> <polyjuice-rpc-url>')
        exit(-1)
    target_dir = sys.argv[1]
    ckb_bin_path = sys.argv[2]
    ckb_rpc_url = sys.argv[3]
    polyjuice_rpc_url = sys.argv[4] if len(sys.argv) == 5 else "http://localhost:8214"

    ckb_dir = os.path.dirname(os.path.abspath(ckb_bin_path))
    privkey1_path = os.path.join(target_dir, "{}.privkey".format(SENDER1))

    if not os.path.exists(privkey1_path):
        with open(privkey1_path, 'w') as f:
            f.write(SENDER1_PRIVKEY)
    main(
        target_dir,
        ckb_bin_path,
        ckb_rpc_url,
        polyjuice_rpc_url,
        ckb_dir,
        privkey1_path,
    )
