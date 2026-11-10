from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app
)

from decimal import Decimal, InvalidOperation

from db import get_db


# ============================================================
# BLUEPRINT
# ============================================================

topup = Blueprint(
    "topup",
    __name__,
    url_prefix="/topup"
)


# ============================================================
# KONSTANTA
# ============================================================

# Sama dengan batas di topup.html (max="100000000").
MAX_TOPUP = 100000000

ALLOWED_METHODS = {
    "Simulasi",
    "Transfer Bank",
    "Virtual Account",
    "E-Wallet"
}


# ============================================================
# HELPER
# ============================================================

def log_error(where, error):
    """
    Mencatat error ke log aplikasi.
    """

    try:
        current_app.logger.warning(
            "TOPUP %s ERROR: %s",
            where,
            error
        )

    except Exception:
        print("TOPUP", where, "ERROR:", error)


def get_cursor(conn):
    """
    Cursor berbentuk dictionary (sama seperti auth.py dan
    savings.py). buffered=True mencegah "Unread result found".
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


def insert_transaction(cursor, user_id, description, amount):
    """
    Menyimpan riwayat top up.

    Dicoba beberapa bentuk kolom karena struktur tabel
    transactions belum diketahui. Kolom jenis diisi "income"
    agar dashboard dan statistik menghitungnya sebagai
    pemasukan. Jika semuanya gagal, saldo tetap diproses.
    """

    for column in ("type", "transaction_type", None):

        try:

            if column:

                cursor.execute(
                    "INSERT INTO transactions "
                    "(user_id, " + column + ", description, amount) "
                    "VALUES (%s, %s, %s, %s)",
                    (user_id, "income", description, amount)
                )

            else:

                cursor.execute(
                    "INSERT INTO transactions "
                    "(user_id, description, amount) "
                    "VALUES (%s, %s, %s)",
                    (user_id, description, amount)
                )

            return True

        except Exception as e:

            log_error("INSERT TRANSACTION (%s)" % column, e)

    return False


# ============================================================
# TOP UP PAGE
# ============================================================

@topup.route("/", methods=["GET", "POST"])
def topup_page():

    # --------------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------------

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    conn = None
    cursor = None

    # --------------------------------------------------------
    # DEFAULT ACCOUNT
    # --------------------------------------------------------

    account = {
        "balance": 0,
        "account_number": "-"
    }

    def show_error(message):

        flash(message, "error")

        return render_template(
            "topup.html",
            account=account
        )

    try:

        # ====================================================
        # DATABASE
        # ====================================================

        conn = get_db()

        cursor = get_cursor(conn)


        # ====================================================
        # GET ACCOUNT
        # ====================================================

        account_row = None

        try:

            cursor.execute(
                """
                SELECT *
                FROM accounts
                WHERE user_id = %s
                LIMIT 1
                """,
                (user_id,)
            )

            account_row = row_to_dict(
                cursor,
                cursor.fetchone()
            )

            if account_row:

                account = account_row

        except Exception as e:

            log_error("GET ACCOUNT", e)


        # ====================================================
        # PROCESS TOP UP
        # ====================================================

        if request.method == "POST":

            # ------------------------------------------------
            # GET FORM DATA
            # ------------------------------------------------

            amount_raw = request.form.get(
                "amount",
                ""
            ).strip()

            method = request.form.get(
                "method",
                "Simulasi"
            ).strip()

            if method not in ALLOWED_METHODS:
                method = "Simulasi"


            # ------------------------------------------------
            # VALIDATION
            # ------------------------------------------------

            if not amount_raw:

                return show_error(
                    "Masukkan nominal top up."
                )


            # ------------------------------------------------
            # NORMALIZE NUMBER
            # ------------------------------------------------

            amount_clean = (
                amount_raw
                .replace("Rp", "")
                .replace("rp", "")
                .replace(" ", "")
                .replace(".", "")
                .replace(",", ".")
            )


            # ------------------------------------------------
            # CONVERT DECIMAL
            # ------------------------------------------------

            try:

                amount = Decimal(
                    amount_clean
                )

            except InvalidOperation:

                return show_error(
                    "Nominal top up tidak valid."
                )

            if not amount.is_finite():

                return show_error(
                    "Nominal top up tidak valid."
                )


            # ------------------------------------------------
            # AMOUNT CHECK
            # ------------------------------------------------

            if amount <= 0:

                return show_error(
                    "Nominal top up harus lebih dari Rp0."
                )


            # ------------------------------------------------
            # INTEGER CHECK
            # ------------------------------------------------
            # FINORA menggunakan saldo rupiah tanpa pecahan.

            if amount != amount.to_integral_value():

                return show_error(
                    "Nominal top up harus berupa angka bulat."
                )


            amount_value = int(amount)


            # ------------------------------------------------
            # MAKSIMAL TOP UP (sebelumnya hanya dicek di HTML)
            # ------------------------------------------------

            if amount_value > MAX_TOPUP:

                return show_error(
                    "Maksimal top up adalah Rp100.000.000."
                )


            # =================================================
            # UPDATE / CREATE ACCOUNT
            # =================================================
            #
            # Saldo ditambah langsung di database (atomik),
            # bukan dibaca lalu ditulis ulang, sehingga aman
            # jika ada dua permintaan bersamaan.

            if account_row:

                cursor.execute(
                    """
                    UPDATE accounts
                    SET balance = COALESCE(balance, 0) + %s
                    WHERE user_id = %s
                    """,
                    (
                        amount_value,
                        user_id
                    )
                )

            else:

                # ------------------------------------------------
                # Generate simple account number
                # ------------------------------------------------

                account_number = (
                    "FIN"
                    + str(user_id).zfill(8)
                )

                cursor.execute(
                    """
                    INSERT INTO accounts
                    (
                        user_id,
                        account_number,
                        balance
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (
                        user_id,
                        account_number,
                        amount_value
                    )
                )


            # =================================================
            # TRANSACTION HISTORY
            # =================================================

            insert_transaction(
                cursor,
                user_id,
                "Top Up via " + method,
                amount_value
            )


            # =================================================
            # COMMIT
            # =================================================

            conn.commit()


            # =================================================
            # SUCCESS
            # =================================================

            flash(
                f"Top up sebesar Rp{amount_value:,.0f} berhasil."
                .replace(",", "."),
                "success"
            )

            return redirect(
                url_for("topup.topup_page")
            )


        # ====================================================
        # GET REQUEST
        # ====================================================

        return render_template(
            "topup.html",
            account=account
        )


    except Exception as e:

        # ----------------------------------------------------
        # ROLLBACK
        # ----------------------------------------------------

        if conn:

            try:
                conn.rollback()
            except Exception:
                pass


        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------
        #
        # Detail error hanya masuk ke log, tidak ditampilkan
        # ke pengguna.

        log_error("PROCESS", e)

        flash(
            "Terjadi kesalahan saat memproses top up. "
            "Silakan coba lagi.",
            "error"
        )

        return render_template(
            "topup.html",
            account=account
        )


    finally:

        # ----------------------------------------------------
        # CLOSE CURSOR
        # ----------------------------------------------------

        if cursor:

            try:
                cursor.close()
            except Exception:
                pass


        # ----------------------------------------------------
        # CLOSE CONNECTION
        # ----------------------------------------------------

        if conn:

            try:
                conn.close()
            except Exception:
                pass
