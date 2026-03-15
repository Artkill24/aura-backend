"""
AURA — Blockchain Notarization (Polygon Amoy)
Salva ogni report on-chain: hash SHA256 + verdict + score.
"""
import os, json
from pathlib import Path
from typing import Dict, Any

CONTRACT_ADDRESS = "0x772f9b66C2884664bf6b18D2a263CfcaCa494849"
AMOY_RPC        = "https://rpc-amoy.polygon.technology/"
CHAIN_ID        = 80002
ABI_PATH        = Path(__file__).parent.parent.parent / "contracts" / "AURANotary_abi.json"

def notarize_report(job_id: str, sha256_hash: str, verdict: str, score: float) -> Dict[str, Any]:
    result = {"tx_hash": None, "block": None, "contract": CONTRACT_ADDRESS, "network": "polygon-amoy", "error": None}

    private_key = os.environ.get("PRIVATE_KEY", "")
    if not private_key:
        result["error"] = "PRIVATE_KEY not set"
        return result

    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(AMOY_RPC))
        if not w3.is_connected():
            result["error"] = "RPC not reachable"
            return result

        with open(ABI_PATH) as f:
            abi = json.load(f)

        account  = w3.eth.account.from_key(private_key)
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

        # sha256 hex → bytes32
        hash_bytes = bytes.fromhex(sha256_hash[:64])

        # score → uint256 (moltiplicato x10000)
        score_int = int(round(score * 10000))

        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.notarize(
            job_id, hash_bytes, verdict, score_int
        ).build_transaction({
            "from":     account.address,
            "nonce":    nonce,
            "gas":      200000,
            "gasPrice": w3.to_wei("30", "gwei"),
            "chainId":  CHAIN_ID,
        })

        signed  = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

        result["tx_hash"] = tx_hash.hex()
        result["block"]   = receipt.blockNumber

    except Exception as e:
        result["error"] = str(e)

    return result


def verify_on_chain(job_id: str) -> Dict[str, Any]:
    result = {"found": False, "error": None}
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(AMOY_RPC))
        with open(ABI_PATH) as f:
            abi = json.load(f)
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
        found, sha256_bytes, verdict, score, timestamp, notarizer = contract.functions.verify(job_id).call()
        result = {
            "found":     found,
            "sha256":    sha256_bytes.hex() if found else None,
            "verdict":   verdict,
            "score":     score / 10000 if found else None,
            "timestamp": timestamp,
            "notarizer": notarizer,
            "contract":  CONTRACT_ADDRESS,
            "network":   "polygon-amoy",
            "explorer":  f"https://amoy.polygonscan.com/address/{CONTRACT_ADDRESS}",
            "error":     None,
        }
    except Exception as e:
        result["error"] = str(e)
    return result
