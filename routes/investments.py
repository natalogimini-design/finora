import math
import random
import threading
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash
)
import mysql.connector
from config import DB_CONFIG

investments = Blueprint("investments", __name__)


# =========================================================
# PENGATURAN SIMULASI PASAR
# =========================================================
# Semua angka di bawah adalah ASUMSI untuk simulasi,
# bukan data pasar sungguhan.
#
#   mu        : ekspektasi return per tahun (0.08 = 8%)
#   sigma     : volatilitas per tahun       (0.18 = 18%)
#   buy_fee   : biaya beli  (dipotong dari nominal)
#   sell_fee  : biaya jual  (dipotong dari nilai saat dicairkan)
#   tax       : pajak atas KEUNTUNGAN saat dicairkan
#   min       : pembelian minimum (Rp)

ASSETS = {
    "deposito": {
        "name": "Deposito",
        "risk": "Rendah", "risk_level": 1,
        "mu": 0.045, "sigma": 0.0,
        "buy_fee": 0.0, "sell_fee": 0.0, "tax": 0.20,
        "min": 1000000,
        "desc": "Bunga relatif tetap. Pajak final 20% atas bunga."
    },
    "sbn": {
        "name": "SBN Ritel",
        "risk": "Rendah", "risk_level": 1,
        "mu": 0.063, "sigma": 0.018,
        "buy_fee": 0.0, "sell_fee": 0.001, "tax": 0.10,
        "min": 1000000,
        "desc": "Surat utang negara. Pajak final 10% atas kupon."
    },
    "rdpu": {
        "name": "Reksa Dana Pasar Uang",
        "risk": "Rendah", "risk_level": 1,
        "mu": 0.048, "sigma": 0.004,
        "buy_fee": 0.0, "sell_fee": 0.0, "tax": 0.0,
        "min": 10000,
        "desc": "Fluktuasi sangat kecil, cocok untuk dana darurat."
    },
    "rdcampuran": {
        "name": "Reksa Dana Campuran",
        "risk": "Sedang", "risk_level": 2,
        "mu": 0.080, "sigma": 0.080,
        "buy_fee": 0.0025, "sell_fee": 0.0025, "tax": 0.0,
        "min": 100000,
        "desc": "Gabungan saham dan obligasi, risiko menengah."
    },
    "emas": {
        "name": "Emas",
        "risk": "Sedang", "risk_level": 2,
        "mu": 0.070, "sigma": 0.150,
        "buy_fee": 0.005, "sell_fee": 0.005, "tax": 0.0,
        "min": 50000,
        "desc": "Lindung nilai inflasi, ada selisih harga beli dan jual."
    },
    "saham": {
        "name": "Saham / Indeks",
        "risk": "Tinggi", "risk_level": 3,
        "mu": 0.100, "sigma": 0.200,
        "buy_fee": 0.0015, "sell_fee": 0.0025, "tax": 0.0,
        "min": 100000,
        "desc": "Potensi tinggi, naik turun besar dalam jangka pendek."
    },
    "kripto": {
        "name": "Kripto",
        "risk": "Sangat tinggi", "risk_level": 4,
        "mu": 0.150, "sigma": 0.650,
        "buy_fee": 0.003, "sell_fee": 0.003, "tax": 0.0,
        "min": 50000,
        "desc": "Sangat fluktuatif, bisa turun tajam dalam waktu singkat."
    },
}

FALLBACK_ASSET = "rdpu"

# Waktu pasar dipercepat: 5 menit nyata = 1 hari simulasi
SIM_SECONDS_PER_DAY = 300
SIM_EPOCH = datetime(2026, 11, 1)
DT = 1.0 / 365.0

# Batas panjang riwayat harga yang disimpan di memori.
# Lewat batas ini, harga bergerak mengikuti drift saja.
MAX_TICKS = 600000

MAX_BUY = Decimal("1000000000")
MAX_DB_VALUE = 9999999999.99


# =========================================================
# DATABASE
# =========================================================

def get_db():
    return mysql.connector.connect(**DB_CONFIG)


# =========================================================
# HELPER UMUM
# =========================================================

def to_float(value):
    try:
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return 0.0
        return number
    except (TypeError, ValueError):
        return 0.0


def to_decimal(value):
    try:
        return Decimal(str(value if value is not None else 0))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def money(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fmt_rp(value):
    rounded = int(round(to_float(value)))
    text = "{:,}".format(abs(rounded)).replace(",", ".")
    return ("-Rp " if rounded < 0 else "Rp ") + text


def fmt_signed_rp(value):
    rounded = int(round(to_float(value)))
    if rounded == 0:
        return "Rp 0"
    sign = "+" if rounded > 0 else "-"
    return sign + "Rp " + "{:,}".format(abs(rounded)).replace(",", ".")


def fmt_pct(value):
    return "{:+.2f}%".format(to_float(value) * 100).replace(".", ",")


def as_datetime(value):
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    return None


def normalize_type(raw):
    key = str(raw or "").strip().lower()
    if key in ASSETS:
        return key
    for asset_key, asset in ASSETS.items():
        if key == asset["name"].lower():
            return asset_key
    return FALLBACK_ASSET


def tick_of(moment):
    moment = as_datetime(moment)
    if moment is None:
        return 0
    seconds = (moment - SIM_EPOCH).total_seconds()
    return max(0, int(seconds // SIM_SECONDS_PER_DAY))


def public_assets():
    """Data aset yang aman dikirim ke browser."""
    return {
        key: {
            "name": a["name"],
            "risk": a["risk"],
            "risk_level": a["risk_level"],
            "mu": a["mu"],
            "sigma": a["sigma"],
            "buy_fee": a["buy_fee"],
            "sell_fee": a["sell_fee"],
            "tax": a["tax"],
            "min": a["min"],
            "desc": a["desc"],
        }
        for key, a in ASSETS.items()
    }


# =========================================================
# MESIN HARGA PASAR (deterministik)
# =========================================================
# Setiap aset punya deret harga yang sama untuk semua pengguna
# (seed tetap), sehingga hasilnya konsisten dan bisa dihitung
# ulang kapan saja tanpa menyimpan status di database.

_market_lock = threading.Lock()
_market = {}


def _extend_series(key, upto):
    asset = ASSETS[key]
    state = _market.get(key)
    if state is None:
        state = {"series": [0.0], "rng": random.Random("finora-market-" + key)}
        _market[key] = state

    series = state["series"]
    rng = state["rng"]

    mu = asset["mu"]
    sigma = asset["sigma"]
    drift = (math.log(1.0 + mu) - 0.5 * sigma * sigma) * DT
    vol = sigma * math.sqrt(DT)

    last = series[-1]
    while len(series) <= upto:
        if sigma > 0:
            last = last + drift + vol * rng.gauss(0.0, 1.0)
        else:
            last = last + drift
        series.append(last)


def log_price(key, tick):
    """Logaritma harga relatif aset pada tick tertentu."""
    tick = max(0, int(tick))
    capped = min(tick, MAX_TICKS)

    with _market_lock:
        series = _market.get(key, {}).get("series")
        if series is None or len(series) <= capped:
            _extend_series(key, capped)
        series = _market[key]["series"]
        value = series[capped]

    if tick > capped:
        asset = ASSETS[key]
        sigma = asset["sigma"]
        drift = (math.log(1.0 + asset["mu"]) - 0.5 * sigma * sigma) * DT
        value += drift * (tick - capped)

    return value


def spark_points(values, width=100.0, height=32.0, pad=3.0):
    """Ubah daftar nilai menjadi atribut points untuk polyline SVG."""
    if not values:
        values = [0.0, 0.0]
    if len(values) == 1:
        values = [values[0], values[0]]

    low = min(values)
    high = max(values)
    span = high - low
    flat = span <= abs(high) * 1e-9 or span <= 1e-12

    points = []
    last_index = len(values) - 1
    for i, value in enumerate(values):
        x = width * i / last_index
        if flat:
            y = height / 2.0
        else:
            y = height - pad - (value - low) / span * (height - 2 * pad)
        points.append("{:.1f},{:.1f}".format(x, y))
    return " ".join(points)


def sample_ticks(start, end, count=24):
    if end <= start:
        return [start, start]
    if end - start <= count:
        return list(range(start, end + 1))
    return [
        start + int(round((end - start) * i / (count - 1)))
        for i in range(count)
    ]


def position_value(key, capital, created_at, now_tick):
    """Nilai posisi saat ini + titik sparkline."""
    asset = ASSETS[key]

    start_tick = tick_of(created_at) if created_at else now_tick
    start_tick = min(start_tick, now_tick)

    net = capital * (1.0 - asset["buy_fee"])
    base = log_price(key, start_tick)

    ticks = sample_ticks(start_tick, now_tick)
    values = [net * math.exp(log_price(key, t) - base) for t in ticks]

    value = net * math.exp(log_price(key, now_tick) - base)
    return value, values, now_tick - start_tick


def sale_breakdown(key, capital, value):
    """Hitung dana bersih yang diterima jika posisi dicairkan."""
    asset = ASSETS[key]

    gross = money(Decimal(str(round(value, 2))))
    sell_fee = money(gross * Decimal(str(asset["sell_fee"])))
    after_fee = gross - sell_fee

    profit = after_fee - to_decimal(capital)
    tax = Decimal("0")
    if profit > 0:
        tax = money(profit * Decimal(str(asset["tax"])))

    net = money(after_fee - tax)
    if net < 0:
        net = Decimal("0.00")

    return gross, sell_fee, tax, net


# =========================================================
# QUERY BANTU
# =========================================================

def fetch_account(cursor, lock=False):
    sql = """
        SELECT id, account_number, balance
        FROM accounts
        WHERE user_id = %s
        LIMIT 1
    """
    if lock:
        sql += " FOR UPDATE"
    cursor.execute(sql, (session["user_id"],))
    return cursor.fetchone()


def fetch_now(cursor):
    cursor.execute("SELECT NOW() AS now_value")
    row = cursor.fetchone()
    moment = as_datetime(row["now_value"]) if row else None
    return moment or datetime.now()


# =========================================================
# HALAMAN UTAMA
# =========================================================

@investments.route("/investments", methods=["GET"])
def index():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        account = fetch_account(cursor)
        now = fetch_now(cursor)
        now_tick = tick_of(now)

        cursor.execute(
            """
            SELECT *
            FROM investments
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (session["user_id"],)
        )
        rows = cursor.fetchall()

        holdings = []
        updates = []
        total_value = 0.0
        total_capital = 0.0

        for row in rows:
            key = normalize_type(row.get("type"))
            asset = ASSETS[key]

            capital = to_float(row.get("capital"))
            value, values, days = position_value(
                key, capital, row.get("created_at"), now_tick
            )

            pnl = value - capital
            pnl_pct = (pnl / capital) if capital > 0 else 0.0
            _, _, _, net = sale_breakdown(key, capital, value)

            total_value += value
            total_capital += capital

            created = as_datetime(row.get("created_at"))

            holdings.append({
                "id": row.get("id"),
                "key": key,
                "name": asset["name"],
                "risk": asset["risk"],
                "risk_level": asset["risk_level"],
                "capital": fmt_rp(capital),
                "value": fmt_rp(value),
                "pnl": fmt_signed_rp(pnl),
                "pnl_pct": fmt_pct(pnl_pct),
                "is_up": pnl >= 0,
                "spark": spark_points(values),
                "days": days,
                "date": created.strftime("%d %b %Y, %H:%M") if created else "-",
                "proceeds": fmt_rp(float(net)),
            })

            if row.get("id") is not None:
                updates.append((
                    round(min(value, MAX_DB_VALUE), 2),
                    row.get("id"),
                    session["user_id"],
                ))

        # Sinkronkan kolom current_value (aman bila gagal)
        if updates:
            try:
                for item in updates:
                    cursor.execute(
                        """
                        UPDATE investments
                        SET current_value = %s
                        WHERE id = %s AND user_id = %s
                        """,
                        item
                    )
                db.commit()
            except Exception:
                db.rollback()

        total_pnl = total_value - total_capital
        total_pct = (total_pnl / total_capital) if total_capital > 0 else 0.0

        summary = {
            "value": fmt_rp(total_value),
            "capital": fmt_rp(total_capital),
            "pnl": fmt_signed_rp(total_pnl),
            "pnl_pct": fmt_pct(total_pct),
            "is_up": total_pnl >= 0,
            "count": len(holdings),
        }

        market = []
        for key, asset in ASSETS.items():
            price = log_price(key, now_tick)
            p30 = log_price(key, max(0, now_tick - 30))
            p365 = log_price(key, max(0, now_tick - 365))

            ch30 = math.exp(price - p30) - 1.0
            ch365 = math.exp(price - p365) - 1.0

            history_ticks = sample_ticks(max(0, now_tick - 60), now_tick, 30)
            history = [math.exp(log_price(key, t)) for t in history_ticks]

            market.append({
                "key": key,
                "name": asset["name"],
                "risk": asset["risk"],
                "risk_level": asset["risk_level"],
                "index": "{:,.2f}".format(100.0 * math.exp(price))
                         .replace(",", "X").replace(".", ",").replace("X", "."),
                "ch30": fmt_pct(ch30),
                "ch30_up": ch30 >= 0,
                "ch365": fmt_pct(ch365),
                "ch365_up": ch365 >= 0,
                "spark": spark_points(history),
            })

        balance = to_float(account["balance"]) if account else 0.0

        return render_template(
            "investments.html",
            account=account,
            balance=balance,
            balance_fmt=fmt_rp(balance),
            holdings=holdings,
            summary=summary,
            market=market,
            assets=public_assets(),
            max_buy=int(MAX_BUY),
            seconds_per_day=SIM_SECONDS_PER_DAY,
        )

    except Exception:
        db.rollback()
        raise

    finally:
        cursor.close()
        db.close()


# =========================================================
# BELI
# =========================================================

@investments.route("/investments/buy", methods=["POST"])
def buy():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    asset_key = request.form.get("asset", "").strip()
    amount_text = request.form.get("amount", "").strip()

    if asset_key not in ASSETS:
        flash("Jenis investasi tidak valid.", "error")
        return redirect(url_for("investments.index"))

    asset = ASSETS[asset_key]

    try:
        amount = Decimal(amount_text)
        if not amount.is_finite() or amount <= 0:
            raise InvalidOperation
        amount = money(amount)
    except (InvalidOperation, ValueError):
        flash("Nominal investasi tidak valid.", "error")
        return redirect(url_for("investments.index"))

    if amount < Decimal(asset["min"]):
        flash(
            "Minimum pembelian {} adalah {}.".format(
                asset["name"], fmt_rp(asset["min"])
            ),
            "error"
        )
        return redirect(url_for("investments.index"))

    if amount > MAX_BUY:
        flash(
            "Maksimum pembelian per transaksi adalah {}.".format(
                fmt_rp(float(MAX_BUY))
            ),
            "error"
        )
        return redirect(url_for("investments.index"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        account = fetch_account(cursor, lock=True)

        if not account:
            db.rollback()
            flash("Rekening FINORA kamu belum tersedia.", "error")
            return redirect(url_for("investments.index"))

        if to_decimal(account["balance"]) < amount:
            db.rollback()
            flash("Saldo tidak mencukupi untuk investasi ini.", "error")
            return redirect(url_for("investments.index"))

        fee = money(amount * Decimal(str(asset["buy_fee"])))
        invested = amount - fee

        cursor.execute(
            """
            UPDATE accounts
            SET balance = balance - %s
            WHERE id = %s
            """,
            (amount, account["id"])
        )

        cursor.execute(
            """
            INSERT INTO investments
            (user_id, type, capital, current_value)
            VALUES (%s, %s, %s, %s)
            """,
            (session["user_id"], asset_key, amount, invested)
        )

        db.commit()

        flash(
            "Pembelian {} sebesar {} berhasil.".format(
                asset["name"], fmt_rp(float(amount))
            ),
            "success"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        cursor.close()
        db.close()

    return redirect(url_for("investments.index"))


# =========================================================
# JUAL / CAIRKAN
# =========================================================

@investments.route("/investments/sell/<int:investment_id>", methods=["POST"])
def sell(investment_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        account = fetch_account(cursor, lock=True)

        if not account:
            db.rollback()
            flash("Rekening FINORA kamu belum tersedia.", "error")
            return redirect(url_for("investments.index"))

        cursor.execute(
            """
            SELECT *
            FROM investments
            WHERE id = %s AND user_id = %s
            FOR UPDATE
            """,
            (investment_id, session["user_id"])
        )
        row = cursor.fetchone()

        if not row:
            db.rollback()
            flash("Investasi tidak ditemukan.", "error")
            return redirect(url_for("investments.index"))

        now = fetch_now(cursor)
        key = normalize_type(row.get("type"))
        capital = to_float(row.get("capital"))

        value, _, _ = position_value(
            key, capital, row.get("created_at"), tick_of(now)
        )
        _, _, _, net = sale_breakdown(key, capital, value)

        cursor.execute(
            """
            UPDATE accounts
            SET balance = balance + %s
            WHERE id = %s
            """,
            (net, account["id"])
        )

        cursor.execute(
            """
            DELETE FROM investments
            WHERE id = %s AND user_id = %s
            """,
            (investment_id, session["user_id"])
        )

        db.commit()

        result = float(net) - capital
        flash(
            "{} dicairkan. Dana diterima {} ({}).".format(
                ASSETS[key]["name"],
                fmt_rp(float(net)),
                ("untung " if result >= 0 else "rugi ") + fmt_rp(abs(result))
            ),
            "success"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        cursor.close()
        db.close()

    return redirect(url_for("investments.index"))
