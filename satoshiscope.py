"""
SatoshiScope: отслеживание цепочки перемещений конкретного UTXO.
"""

import requests
import argparse

def get_utxo_chain(txid, vout_index):
    visited = set()
    chain = []

    current_txid = txid
    current_vout = vout_index

    while True:
        key = f"{current_txid}:{current_vout}"
        if key in visited:
            break
        visited.add(key)

        # Получаем tx
        url = f"https://api.blockchair.com/bitcoin/raw/transaction/{current_txid}"
        r = requests.get(url)
        if r.status_code != 200:
            print(f"❌ Ошибка получения транзакции: {current_txid}")
            break

        tx = r.json()["data"][current_txid]["decoded_raw_transaction"]
        outputs = tx["vout"]
        if current_vout >= len(outputs):
            print("⚠️ Некорректный индекс выхода.")
            break

        output = outputs[current_vout]
        value = output["value"]
        addresses = output.get("script_pub_key", {}).get("addresses", ["N/A"])
        chain.append({
            "txid": current_txid,
            "vout": current_vout,
            "value": value,
            "address": addresses[0],
        })

        # Теперь ищем, был ли этот UTXO использован
        url2 = f"https://api.blockchair.com/bitcoin/dashboards/output/{current_txid}:{current_vout}"
        r2 = requests.get(url2)
        if r2.status_code != 200:
            print("✅ UTXO не был потрачен (находится в обороте).")
            break
        spent_info = r2.json()["data"].get(f"{current_txid}:{current_vout}", {}).get("spent_by", None)
        if not spent_info:
            print("✅ UTXO не потрачен.")
            break

        current_txid = spent_info["transaction_hash"]
        current_vout = spent_info["index"]

    return chain

def print_chain(chain):
    print("🔎 Цепочка UTXO:")
    for i, link in enumerate(chain):
        print(f"{i+1}. TXID: {link['txid']} (vout {link['vout']}) — {link['value']} BTC → {link['address']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SatoshiScope — отслеживание UTXO.")
    parser.add_argument("txid", help="TXID")
    parser.add_argument("vout", type=int, help="VOUT index")
    args = parser.parse_args()
    chain = get_utxo_chain(args.txid, args.vout)
    print_chain(chain)
