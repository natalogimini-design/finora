from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)

from db import get_db


# ============================================================
# BLUEPRINT
# ============================================================

savings = Blueprint(
    "savings",
    __name__,
    url_prefix="/savings"
)


# ============================================================
# SAVINGS / TABUNGAN
# ============================================================

@savings.route("/")
def index():

    # --------------------------------------------------------
    # CEK LOGIN
    # --------------------------------------------------------

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = None
    cursor = None

    try:

        user_id = session["user_id"]

        # ----------------------------------------------------
        # KONEKSI DATABASE
        # ----------------------------------------------------

        db = get_db()

        cursor = db.cursor(dictionary=True)

        # ----------------------------------------------------
        # AMBIL DATA ACCOUNT
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                account_number,
                balance
            FROM accounts
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        account = cursor.fetchone()

        # ----------------------------------------------------
        # TAMPILKAN HALAMAN
        # ----------------------------------------------------

        return render_template(
            "savings.html",
            account=account
        )

    except Exception as e:

        print("Savings Error:", e)

        return (
            f"Terjadi kesalahan pada halaman tabungan: {e}",
            500
        )

    finally:

        if cursor is not None:
            cursor.close()

        if db is not None:
            db.close()