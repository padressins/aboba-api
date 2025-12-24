from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Файлы для хранения данных
RATES_FILE = "rates.json"
REFERRALS_FILE = "referrals.json"

# === РАБОТА С КУРСОМ ===

def get_btc_rate():
    if os.path.exists(RATES_FILE):
        with open(RATES_FILE) as f:
            data = json.load(f)
            return data.get("BTC", 7000000)
    return 7000000

def save_btc_rate(rate):
    with open(RATES_FILE, "w") as f:
        json.dump({"BTC": rate}, f)

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        amount = float(data['amount'])
        wallet = data.get('wallet', 'N/A')
        rate = get_btc_rate()
        sum_moment = amount * rate * 1.2
        sum_delay = amount * rate * 1.1
        return jsonify({
            "sum_moment": round(sum_moment),
            "sum_delay": round(sum_delay),
            "rate": rate
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/set_rate', methods=['GET'])
def set_rate():
    try:
        new_rate = float(request.args.get('rate'))
        save_btc_rate(new_rate)
        return jsonify({"status": "ok", "rate": new_rate})
    except Exception as e:
        return jsonify({"error": str(e), "status": "fail"}), 400

# === РАБОТА С РЕФЕРАЛАМИ ===

def load_referrals():
    if os.path.exists(REFERRALS_FILE):
        with open(REFERRALS_FILE) as f:
            return json.load(f)
    return {}

def save_referrals(refs):
    with open(REFERRALS_FILE, "w") as f:
        json.dump(refs, f, indent=2)

@app.route('/api/user_joined', methods=['POST'])
def user_joined():
    data = request.json
    user_id = str(data['user_id'])
    ref = data.get('ref', None)
    username = data.get('username', 'unknown')

    refs = load_referrals()

    # Если пришёл по рефке
    if ref:
        ref = str(ref)
        if ref not in refs:
            refs[ref] = {"username": "unknown", "referrals": []}

        # Проверяем, не дубль ли
        if not any(r["user_id"] == user_id for r in refs[ref]["referrals"]):
            refs[ref]["referrals"].append({
                "user_id": user_id,
                "username": username,
                "joined_at": datetime.now().isoformat(),
                "status": "active"
            })

    # Если это партнёр — обновим его username
    if user_id not in refs:
        refs[user_id] = {"username": username, "referrals": []}
    else:
        refs[user_id]["username"] = username

    save_referrals(refs)
    return jsonify({"status": "ok"})

@app.route('/api/partner/<partner_id>', methods=['GET'])
def get_partner_info(partner_id):
    refs = load_referrals()
    partner = refs.get(str(partner_id), {"username": "unknown", "referrals": []})

    # Собираем юзернеймы
    referral_usernames = [ref["username"] for ref in partner["referrals"]]
    referral_usernames_str = ", ".join(referral_usernames) if referral_usernames else "нет"

    return jsonify({
        "username": partner["username"],
        "total_referrals": len(partner["referrals"]),
        "referral_usernames": referral_usernames_str,
        "referrals": partner["referrals"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
