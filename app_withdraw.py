from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

from binace_api import Binance
import json
import math
import datetime
import random
import requests


def get_ip():
    try:
        response = requests.get("https://ipinfo.io", timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["ip"]
    except requests.exceptions.RequestException:
        return None


def truncate(number, decimals=2):
    factor = 10.0**decimals
    return math.floor(number * factor) / factor


def get_random_amount(
    upper_bound: float = 0.03, lower_bound: float = 0.02, num_decimals: int = 3
):
    return truncate(random.uniform(lower_bound, upper_bound), num_decimals)


def current_time():

    now = datetime.datetime.now()

    # 分别获取年、月、日、时、分、秒
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    minute = now.minute
    second = now.second

    # 输出结果
    return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"


def parse_wallet_addresses(file):
    wallet_addresses = []
    for line in file:
        wallet_address = line.strip().decode()
        if not wallet_address:
            continue
        wallet_addresses.append(wallet_address)
    return wallet_addresses


app = Flask(__name__)
socketio = SocketIO(app)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["wallet_file"]
        network = request.form["network"].strip().upper()
        wallet_addresses = parse_wallet_addresses(file)
        valid_addrs = wallet_addresses
        valid_addrs = list(set(valid_addrs))
        print(valid_addrs)
        return render_template(
            "wallet.html",
            messages=valid_addrs,
            valid_addrs=valid_addrs,
            network=network,
        )
    ip = get_ip()
    return render_template("index.html", ip=ip)


@socketio.on("submit_form")
def withdraw(form_data):
    api_key = form_data["api_key"].strip()
    api_secret = form_data["api_secret"].strip()
    coin = form_data["coin"].strip().upper()
    network = form_data["network"].strip().upper()
    withdraw_interval1 = float(form_data["withdraw_interval1"].strip())
    withdraw_interval2 = float(form_data["withdraw_interval2"].strip())
    withdraw_amount1 = float(form_data["withdraw_amount1"].strip())
    withdraw_amount2 = float(form_data["withdraw_amount2"].strip())
    wallet_addresses = form_data["wallet_addresses"].strip().split(",")
    num_decimals = int(form_data["num_decimals"].strip())
    # print form_data
    bn = Binance(api_key, api_secret)
    total = len(wallet_addresses)
    idx = 1
    for addr in wallet_addresses:
        emit("withdraw_log", f"{idx}/{total}")
        idx += 1
        withdraw_interval = get_random_amount(withdraw_interval1, withdraw_interval2, 0)
        withdraw_amount = get_random_amount(
            withdraw_amount1, withdraw_amount2, num_decimals
        )
        emit("withdraw_log", current_time())
        try:
            result = "mock"
            result = bn.withdraw(coin, addr, withdraw_amount, network)
            emit(
                "withdraw_log",
                json.dumps(result),
            )
            emit("withdraw_log", f"Withdrawing {withdraw_amount} to {addr}.")
        except Exception as e:
            emit("withdraw_log", f"Error: {e}.")
            break
        emit("withdraw_log", f"sleeping for {withdraw_interval} seconds.")
        socketio.sleep(withdraw_interval)
    emit("withdraw_log", "Done!")


if __name__ == "__main__":
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5005
    socketio.run(app, debug=True, host="0.0.0.0", port=port)
