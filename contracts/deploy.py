import os, json
from web3 import Web3
from solcx import compile_source, install_solc

install_solc("0.8.20")

AMOY_RPC = "https://rpc-amoy.polygon.technology/"
PRIVATE_KEY = os.environ["PRIVATE_KEY"]

w3 = Web3(Web3.HTTPProvider(AMOY_RPC))
assert w3.is_connected(), "RPC non raggiungibile"

account = w3.eth.account.from_key(PRIVATE_KEY)
print(f"Deploying from: {account.address}")
print(f"Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} MATIC")

with open("contracts/AURANotary.sol") as f:
    source = f.read()

compiled = compile_source(source, output_values=["abi", "bin"], solc_version="0.8.20")
contract_id = "<stdin>:AURANotary"
abi = compiled[contract_id]["abi"]
bytecode = compiled[contract_id]["bin"]

Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.get_transaction_count(account.address)

tx = Contract.constructor().build_transaction({
    "from": account.address,
    "nonce": nonce,
    "gas": 800000,
    "gasPrice": w3.to_wei("30", "gwei"),
    "chainId": 80002,  # Polygon Amoy
})

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"TX hash: {tx_hash.hex()}")
print("Waiting for confirmation...")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
print(f"✅ Contract deployed: {receipt.contractAddress}")

# Salva ABI e address
with open("contracts/AURANotary_abi.json", "w") as f:
    json.dump(abi, f, indent=2)
with open("contracts/deployed.json", "w") as f:
    json.dump({"address": receipt.contractAddress, "network": "polygon-amoy", "chain_id": 80002}, f, indent=2)

print("ABI e address salvati in contracts/")
