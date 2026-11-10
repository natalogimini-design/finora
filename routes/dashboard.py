from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    request,
    flash,
    current_app
)

from db import get_db

from datetime import datetime, timedelta

import calendar
import math
import re


# ============================================================
# BLUEPRINT
# ============================================================

dashboard = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard"
)


# ============================================================
# KONSTANTA
# ============================================================

DEFAULT_LIMIT = 2000000
MAX_LIMIT = 1000000000000

# Jumlah transaksi yang dibaca untuk menghitung statistik.
MAX_TRANSACTIONS = 2000

# Jumlah transaksi yang ditampilkan di beranda.
RECENT_TRANSACTIONS = 10

MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
    "Jul", "Agu", "Sep", "Okt", "Nov", "Des"
]

# datetime.weekday(): Senin = 0
DAY_LABELS = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]

AMOUNT_KEYS = ["amount", "nominal", "jumlah", "total"]

TYPE_KEYS = [
    "type",
    "transaction_type",
    "tipe",
    "jenis",
    "jenis_transaksi"
]

DATE_KEYS = [
    "created_at",
    "transaction_date",
    "tanggal",
    "date",
    "created"
]

DESCRIPTION_KEYS = [
    "description",
    "deskripsi",
    "keterangan",
    "note",
    "notes",
    "title"
]

CATEGORY_KEYS = [
    "category",
    "kategori",
    "category_name",
    "nama_kategori"
]

# Nilai kolom "type" yang dianggap uang masuk / uang keluar.
# Spasi dan tanda "-" otomatis diubah menjadi "_" sebelum dicocokkan.
INCOME_TYPES = {
    "income", "pemasukan", "masuk", "credit", "kredit",
    "topup", "top_up", "deposit", "setoran",
    "transfer_in", "transfer_masuk", "terima", "received",
    "incoming"
}

EXPENSE_TYPES = {
    "expense", "pengeluaran", "keluar", "debit", "debet",
    "transfer", "transfer_out", "transfer_keluar",
    "payment", "pembayaran", "bayar", "purchase",
    "withdraw", "withdrawal", "tarik",
    "autopay", "outgoing"
}


# ============================================================
# HELPER
# ============================================================

def log_error(where, error):
    """
    Mencatat error ke log aplikasi.

    Sebelumnya error database ditelan oleh "except: pass",
    sehingga penyebab saldo kosong tidak pernah terlihat.
    """

    try:
        current_app.logger.warning(
            "DASHBOARD %s ERROR: %s",
            where,
            error
        )

    except Exception:
        print("DASHBOARD", where, "ERROR:", error)


def get_cursor(conn):
    """
    Cursor berbentuk dictionary (sama seperti auth.py).
    buffered=True mencegah error "Unread result found".
    """

    try:
        return conn.cursor(dictionary=True, buffered=True)

    except TypeError:
        return conn.cursor()


def row_to_dict(cursor, row):
    """
    Mengubah row (dict / tuple) menjadi dictionary.
    """

    if row is None:
        return None

    if isinstance(row, dict):
        return row

    try:
        columns = [column[0] for column in cursor.description]

        return dict(zip(columns, row))

    except Exception:
        return None


def get_column_value(data, possible_names, default=None):
    """
    Mengambil nilai berdasarkan beberapa kemungkinan
    nama kolom.
    """

    if not isinstance(data, dict):
        return default

    for name in possible_names:

        if name in data:
            return data[name]

    return default


def to_float(value):
    """
    Mengubah nilai (int, float, Decimal, str) menjadi float.
    """

    if value is None:
        return 0.0

    try:
        number = float(value)

    except (TypeError, ValueError):
        return 0.0

    if not math.isfinite(number):
        return 0.0

    return number


def parse_amount(raw):
    """
    Membaca nominal dari form.

    Contoh yang dikenali:
    2000000 | 2.000.000 | 2,000,000 | 2000000.5
    """

    text = re.sub(r"[^\d.,]", "", str(raw or "").strip())

    if not text:
        return None

    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", text):
        # pemisah ribuan
        text = re.sub(r"[.,]", "", text)

    else:
        text = text.replace(",", ".")

    try:
        value = float(text)

    except ValueError:
        return None

    if not math.isfinite(value):
        return None

    return round(value, 2)


def format_account_number(number):
    """
    Membuat nomor rekening lebih mudah dibaca.

    FIN123456789 -> FIN 123 456 789
    1234567890   -> 1234 5678 90
    """

    if not number:
        return "-"

    number = str(number).replace(" ", "").strip()

    if number in ("", "-"):
        return "-"

    match = re.fullmatch(r"([A-Za-z]+)(\d+)", number)

    if match:

        prefix, digits = match.groups()

        groups = [
            digits[i:i + 3]
            for i in range(0, len(digits), 3)
        ]

        return " ".join([prefix.upper()] + groups)

    # Jangan mengubah nomor yang terlalu pendek.
    if len(number) < 8:
        return number

    return " ".join(
        number[i:i + 4]
        for i in range(0, len(number), 4)
    )


def parse_date(value):
    """
    Mengubah datetime / date / string menjadi datetime.
    """

    if isinstance(value, datetime):
        return value

    if hasattr(value, "year") and hasattr(value, "month") \
            and hasattr(value, "day"):

        return datetime(value.year, value.month, value.day)

    text = str(value or "").strip()

    if not text:
        return None

    try:
        return datetime.fromisoformat(text)

    except ValueError:
        pass

    try:
        return datetime.strptime(text[:10], "%Y-%m-%d")

    except ValueError:
        return None


def format_date(date, raw):
    """
    Teks tanggal untuk daftar transaksi.
    """

    if date is None:
        return str(raw) if raw else "-"

    text = "{} {} {}".format(
        date.day,
        MONTH_LABELS[date.month - 1],
        date.year
    )

    if date.hour or date.minute:
        text += ", {:02d}:{:02d}".format(date.hour, date.minute)

    return text


def classify_type(value):
    """
    Mengembalikan "income", "expense", atau None.
    """

    key = re.sub(
        r"[\s\-]+",
        "_",
        str(value or "").strip().lower()
    )

    if key in INCOME_TYPES:
        return "income"

    if key in EXPENSE_TYPES:
        return "expense"

    return None


def normalize_transaction(raw):
    """
    Menyeragamkan satu baris transaksi dari database.
    """

    amount = abs(
        to_float(get_column_value(raw, AMOUNT_KEYS, 0))
    )

    type_raw = get_column_value(raw, TYPE_KEYS, "")

    kind = classify_type(type_raw)

    date_raw = get_column_value(raw, DATE_KEYS, None)

    date = parse_date(date_raw)

    description = get_column_value(
        raw,
        DESCRIPTION_KEYS,
        None
    ) or "Transaksi"

    category = get_column_value(
        raw,
        CATEGORY_KEYS,
        None
    ) or "Lainnya"

    type_label = ""

    if type_raw:
        type_label = str(type_raw).replace("_", " ").title()

    return {
        "amount": amount,
        "kind": kind,
        "is_income": kind == "income",
        "date": date,
        "date_text": format_date(date, date_raw),
        "description": str(description),
        "category": str(category),
        "type_label": type_label
    }


def bar_percent(value, peak):
    """
    Tinggi batang grafik (0 - 100).
    """

    if peak <= 0 or value <= 0:
        return 0

    return max(round(value / peak * 100, 1), 3)


# ============================================================
# STATISTIK
# ============================================================

def build_statistics(items, spending_limit, now=None):
    """
    Menghitung seluruh statistik dari transaksi yang sudah
    dinormalisasi.
    """

    now = now or datetime.now()

    days_in_month = calendar.monthrange(now.year, now.month)[1]

    day_of_month = now.day

    days_left = days_in_month - day_of_month + 1

    current_key = (now.year, now.month)

    # ---------------- 6 bulan terakhir ----------------

    month_keys = []

    year, month = now.year, now.month

    for _ in range(6):

        month_keys.append((year, month))

        month -= 1

        if month == 0:
            month = 12
            year -= 1

    month_keys.reverse()

    monthly = {
        key: {"income": 0.0, "expense": 0.0}
        for key in month_keys
    }

    # ---------------- 7 hari terakhir ----------------

    week_days = [
        (now - timedelta(days=offset)).date()
        for offset in range(6, -1, -1)
    ]

    daily = {day: 0.0 for day in week_days}

    # ---------------- Perulangan ----------------

    total_income = 0.0
    total_expense = 0.0

    income_count = 0
    expense_count = 0

    category_totals = {}

    largest_expense = None

    for item in items:

        kind = item["kind"]
        amount = item["amount"]
        date = item["date"]

        if kind == "income":
            total_income += amount
            income_count += 1

        elif kind == "expense":
            total_expense += amount
            expense_count += 1

        if kind is None or date is None:
            continue

        key = (date.year, date.month)

        if key in monthly:
            monthly[key][kind] += amount

        if kind != "expense":
            continue

        if date.date() in daily:
            daily[date.date()] += amount

        if key == current_key:

            category = item["category"]

            category_totals[category] = (
                category_totals.get(category, 0.0) + amount
            )

            if (
                largest_expense is None
                or amount > largest_expense["amount"]
            ):
                largest_expense = item

    current_income = monthly[current_key]["income"]
    current_expense = monthly[current_key]["expense"]

    previous_key = month_keys[-2]

    previous_expense = monthly[previous_key]["expense"]

    # ---------------- Kategori ----------------

    expense_by_category = []

    for category, amount in sorted(
        category_totals.items(),
        key=lambda pair: pair[1],
        reverse=True
    ):

        percentage = 0

        if current_expense > 0:
            percentage = amount / current_expense * 100

        expense_by_category.append({
            "category": category,
            "amount": amount,
            "percentage": round(percentage, 1)
        })

    # ---------------- Grafik tren ----------------

    peak = max(
        [
            value
            for data in monthly.values()
            for value in data.values()
        ] + [0]
    )

    trend = []

    for key in month_keys:

        data = monthly[key]

        trend.append({
            "label": MONTH_LABELS[key[1] - 1],
            "income": data["income"],
            "expense": data["expense"],
            "income_pct": bar_percent(data["income"], peak),
            "expense_pct": bar_percent(data["expense"], peak),
            "is_current": key == current_key
        })

    # ---------------- Grafik 7 hari ----------------

    week_peak = max(list(daily.values()) + [0])

    week = []

    for day in week_days:

        week.append({
            "label": DAY_LABELS[day.weekday()],
            "amount": daily[day],
            "pct": bar_percent(daily[day], week_peak),
            "is_today": day == now.date()
        })

    # ---------------- Wawasan ----------------

    net_cashflow = current_income - current_expense

    savings_rate = None

    if current_income > 0:
        savings_rate = round(net_cashflow / current_income * 100, 1)

    avg_daily_expense = current_expense / max(day_of_month, 1)

    projected_expense = avg_daily_expense * days_in_month

    mom_change = None

    if previous_expense > 0:
        mom_change = round(
            (current_expense - previous_expense)
            / previous_expense * 100,
            1
        )

    top_category = (
        expense_by_category[0] if expense_by_category else None
    )

    return {
        "current_month_income": current_income,
        "current_month_expense": current_expense,
        "total_income": total_income,
        "total_expense": total_expense,
        "income_count": income_count,
        "expense_count": expense_count,
        "expense_by_category": expense_by_category,
        "trend": trend,
        "trend_has_data": peak > 0,
        "week": week,
        "week_has_data": week_peak > 0,
        "week_total": sum(daily.values()),
        "net_cashflow": net_cashflow,
        "savings_rate": savings_rate,
        "avg_daily_expense": avg_daily_expense,
        "projected_expense": projected_expense,
        "projected_over": (
            spending_limit > 0
            and projected_expense > spending_limit
        ),
        "previous_month_expense": previous_expense,
        "mom_change": mom_change,
        "largest_expense": largest_expense,
        "top_category": top_category,
        "day_of_month": day_of_month,
        "days_in_month": days_in_month,
        "days_left": days_left
    }


# ============================================================
# DATABASE
# ============================================================

_tables_ready = False


def ensure_tables(conn, cursor):
    """
    Membuat tabel batas pengeluaran (sintaks MySQL)
    jika belum ada.
    """

    global _tables_ready

    if _tables_ready:
        return

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS spending_limits (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL UNIQUE,
            monthly_limit DECIMAL(15, 2) NOT NULL DEFAULT 2000000,
            updated_at DATETIME NULL
        )
        """
    )

    conn.commit()

    _tables_ready = True


def fetch_transactions(cursor, user_id, account_id):
    """
    Mengambil transaksi terbaru milik user.

    Jika tabel tidak punya kolom user_id, dicoba account_id.
    """

    queries = [
        (
            "SELECT * FROM transactions "
            "WHERE user_id = %s "
            "ORDER BY id DESC LIMIT %s",
            (user_id, MAX_TRANSACTIONS)
        )
    ]

    if account_id is not None:

        queries.append((
            "SELECT * FROM transactions "
            "WHERE account_id = %s "
            "ORDER BY id DESC LIMIT %s",
            (account_id, MAX_TRANSACTIONS)
        ))

    for sql, params in queries:

        try:
            cursor.execute(sql, params)

            return cursor.fetchall()

        except Exception as e:
            log_error("TRANSACTIONS", e)

    return []


# ============================================================
# DASHBOARD HOME
# ============================================================

@dashboard.route("/", methods=["GET", "POST"])
def home():

    # --------------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------------

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    session_name = session.get("user_name") or "Pengguna"

    conn = None
    cursor = None

    # --------------------------------------------------------
    # DEFAULT VALUES
    # --------------------------------------------------------

    account = {
        "balance": 0.0,
        "account_number": "-",
        "account_number_raw": "",
        "bank_name": "Rekening Utama",
        "account_name": session_name
    }

    user = None

    account_id = None

    raw_transactions = []

    savings = []

    spending_limit = DEFAULT_LIMIT

    dashboard_error = None

    # ========================================================
    # DATABASE
    # ========================================================

    try:

        conn = get_db()

        cursor = get_cursor(conn)

        # ----------------------------------------------------
        # TABEL BATAS PENGELUARAN
        # ----------------------------------------------------

        try:
            ensure_tables(conn, cursor)

        except Exception as e:
            log_error("CREATE TABLE", e)

        # ----------------------------------------------------
        # USER
        # ----------------------------------------------------

        try:

            cursor.execute(
                "SELECT * FROM users WHERE id = %s LIMIT 1",
                (user_id,)
            )

            user_data = row_to_dict(cursor, cursor.fetchone())

            if user_data:

                # Hash password / PIN tidak dikirim ke template.
                user = {
                    "id": user_data.get("id"),
                    "name": user_data.get("name"),
                    "email": user_data.get("email")
                }

        except Exception as e:
            log_error("USER", e)

        # ----------------------------------------------------
        # ACCOUNT  (saldo + nomor rekening)
        # ----------------------------------------------------

        try:

            cursor.execute(
                "SELECT * FROM accounts WHERE user_id = %s LIMIT 1",
                (user_id,)
            )

            account_data = row_to_dict(cursor, cursor.fetchone())

            if account_data:

                account_id = account_data.get("id")

                balance = get_column_value(
                    account_data,
                    ["balance", "saldo", "current_balance"],
                    0
                )

                account_number = get_column_value(
                    account_data,
                    [
                        "account_number",
                        "nomor_rekening",
                        "rekening",
                        "number"
                    ],
                    "-"
                )

                bank_name = get_column_value(
                    account_data,
                    ["bank_name", "nama_bank", "bank"],
                    None
                )

                account_name = get_column_value(
                    account_data,
                    [
                        "account_name",
                        "nama_rekening",
                        "owner_name",
                        "nama_pemilik"
                    ],
                    None
                )

                if not account_name or account_name == "-":

                    account_name = (
                        (user or {}).get("name") or session_name
                    )

                account = {
                    "balance": to_float(balance),
                    "account_number": format_account_number(
                        account_number
                    ),
                    "account_number_raw": (
                        str(account_number or "").replace(" ", "")
                        if account_number != "-" else ""
                    ),
                    "bank_name": bank_name or "Rekening Utama",
                    "account_name": account_name
                }

        except Exception as e:
            log_error("ACCOUNT", e)

        # ----------------------------------------------------
        # BATAS PENGELUARAN: baca
        # ----------------------------------------------------

        try:

            cursor.execute(
                "SELECT monthly_limit FROM spending_limits "
                "WHERE user_id = %s LIMIT 1",
                (user_id,)
            )

            row = row_to_dict(cursor, cursor.fetchone())

            if row and row.get("monthly_limit") is not None:

                value = to_float(row["monthly_limit"])

                if value > 0:
                    spending_limit = value

        except Exception as e:
            log_error("READ LIMIT", e)

        # ----------------------------------------------------
        # BATAS PENGELUARAN: simpan (POST)
        # ----------------------------------------------------

        if (
            request.method == "POST"
            and request.form.get("action") == "update_limit"
        ):

            new_limit = parse_amount(
                request.form.get("spending_limit")
            )

            if new_limit is None:

                flash(
                    "Nominal batas pengeluaran tidak valid.",
                    "danger"
                )

            elif new_limit <= 0:

                flash(
                    "Batas pengeluaran harus lebih dari Rp0.",
                    "danger"
                )

            elif new_limit > MAX_LIMIT:

                flash(
                    "Nominal batas pengeluaran terlalu besar.",
                    "danger"
                )

            else:

                try:

                    cursor.execute(
                        """
                        INSERT INTO spending_limits
                            (user_id, monthly_limit, updated_at)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            monthly_limit = VALUES(monthly_limit),
                            updated_at = VALUES(updated_at)
                        """,
                        (
                            user_id,
                            new_limit,
                            datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        )
                    )

                    conn.commit()

                    flash(
                        "Batas pengeluaran berhasil diperbarui.",
                        "success"
                    )

                except Exception as e:

                    try:
                        conn.rollback()

                    except Exception:
                        pass

                    log_error("SAVE LIMIT", e)

                    flash(
                        "Batas pengeluaran gagal disimpan. "
                        "Silakan coba lagi.",
                        "danger"
                    )

            # Post/Redirect/Get: mencegah submit ulang saat refresh.
            return redirect(url_for("dashboard.home"))

        # ----------------------------------------------------
        # TRANSAKSI
        # ----------------------------------------------------

        raw_transactions = [
            row_to_dict(cursor, row)
            for row in fetch_transactions(
                cursor,
                user_id,
                account_id
            )
        ]

        # ----------------------------------------------------
        # SAVINGS
        # ----------------------------------------------------

        try:

            cursor.execute(
                "SELECT * FROM savings WHERE user_id = %s "
                "ORDER BY id DESC LIMIT 10",
                (user_id,)
            )

            savings = [
                row_to_dict(cursor, row)
                for row in cursor.fetchall()
            ]

        except Exception as e:
            log_error("SAVINGS", e)

    # ========================================================
    # DATABASE ERROR
    # ========================================================

    except Exception as e:

        log_error("DATABASE", e)

        dashboard_error = (
            "Sebagian data gagal dimuat. "
            "Silakan muat ulang halaman."
        )

    finally:

        if cursor:

            try:
                cursor.close()

            except Exception:
                pass

        if conn:

            try:
                conn.close()

            except Exception:
                pass

    # ========================================================
    # STATISTIK
    # ========================================================

    items = [
        normalize_transaction(row)
        for row in raw_transactions
        if row
    ]

    stats = build_statistics(items, spending_limit)

    current_month_income = stats["current_month_income"]
    current_month_expense = stats["current_month_expense"]

    # ========================================================
    # BATAS PENGELUARAN
    # ========================================================

    remaining_limit = spending_limit - current_month_expense

    spending_percentage = 0

    if spending_limit > 0:

        spending_percentage = round(
            current_month_expense / spending_limit * 100,
            1
        )

    safe_daily_limit = 0

    if remaining_limit > 0 and stats["days_left"] > 0:
        safe_daily_limit = remaining_limit / stats["days_left"]

    # ========================================================
    # WARNING
    # ========================================================

    if current_month_expense > spending_limit:

        warning_level = "danger"

        warning_message = (
            "Pengeluaran bulan ini sudah "
            "melewati batas yang ditentukan."
        )

    elif spending_percentage >= 80:

        warning_level = "warning"

        warning_message = (
            "Pengeluaran sudah mendekati "
            "batas bulanan."
        )

    elif spending_percentage >= 60:

        warning_level = "notice"

        warning_message = (
            "Pengeluaran mulai meningkat. "
            "Tetap perhatikan penggunaan uang."
        )

    elif (
        stats["projected_over"]
        and stats["day_of_month"] >= 3
        and current_month_expense > 0
    ):

        warning_level = "notice"

        warning_message = (
            "Dengan laju saat ini, pengeluaran diproyeksikan "
            "melewati batas bulanan sebelum akhir bulan."
        )

    else:

        warning_level = "safe"

        warning_message = "Pengeluaran masih dalam batas aman."

    # ========================================================
    # RENDER DASHBOARD
    # ========================================================

    return render_template(
        "dashboard.html",

        user=user,

        account=account,

        transactions=items[:RECENT_TRANSACTIONS],

        savings=savings,

        # ringkasan bulan ini
        total_income=stats["total_income"],
        total_expense=stats["total_expense"],
        current_month_income=current_month_income,
        current_month_expense=current_month_expense,

        # batas pengeluaran
        spending_limit=spending_limit,
        remaining_limit=remaining_limit,
        spending_percentage=spending_percentage,
        safe_daily_limit=safe_daily_limit,

        # peringatan
        warning_level=warning_level,
        warning_message=warning_message,

        # statistik
        transaction_count=len(items),
        income_transaction_count=stats["income_count"],
        expense_transaction_count=stats["expense_count"],
        expense_by_category=stats["expense_by_category"],
        stats=stats,

        dashboard_error=dashboard_error
    )
