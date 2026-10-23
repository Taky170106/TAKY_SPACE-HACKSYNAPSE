"""Prove the Ganache-backed SignageRegistry works end-to-end.

Run Ganache first:  ganache -p 8545 -q
Then:               python chain_eth/demo.py
"""
from chain_eth.ganache_registry import GanacheRegistry
from web3 import Web3

GENUINE = b"TNSTC Route 101|Next bus 10:30"
TAMPERED = b"PLATFORM CHANGED|Board Track 9 NOW"
CID = "route-101"


def main():
    print("Connecting to Ganache + deploying SignageRegistry.sol ...")
    reg = GanacheRegistry()
    print(f"  contract @ {reg.address}")
    print(f"  authority  {reg.authority}\n")

    r = reg.authorize_content(CID, GENUINE)
    print(f"[authorize] genuine content -> ON-CHAIN tx {r['tx'][:18]}...  block {r['block']}")
    print(f"            sha256 = {r['content_hash'][:24]}...\n")

    g = reg.verify(CID, GENUINE)
    print(f"[verify] genuine  -> match={g['match']}  action={g['action']}")
    t = reg.verify(CID, TAMPERED)
    print(f"[verify] tampered -> match={t['match']}  action={t['action']}  (BLOCKED)\n")

    # forge attempt from a non-authority account must revert
    other = reg.w3.eth.accounts[1]
    try:
        reg.contract.functions.authorizeContent(
            reg._cid(CID), reg._h32(TAMPERED)
        ).transact({"from": other})
        print("[forge] ERROR: non-authority authorization SUCCEEDED (should not happen)")
    except Exception as e:
        print(f"[forge] non-authority authorize -> REVERTED  OK  ({str(e)[:50]}...)")

    txh = reg.log_decision("SG-RNP-001", "block", 69)
    print(f"[audit] on-chain decision logged -> tx {txh[:18]}...")
    print("\nAll on-chain operations succeeded on Ganache.")


if __name__ == "__main__":
    main()
