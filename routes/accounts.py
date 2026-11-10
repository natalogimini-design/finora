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

accounts_bp = Blueprint(
    "accounts",
    __name__,
    url_prefix="/accounts"
)


# ============================================================
# ACCOUNTS PAGE
# ============================================================

@accounts_bp.route("/")
def accounts_page():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    conn = None
    cursor = None

    try:

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM accounts
            WHERE user_id = ?
            LIMIT 1
            """,
            (user_id,)
        )

        account = cursor.fetchone()

        if account is None:

            account = {
                "balance": 0
            }

        return render_template(
            "accounts.html",
            account=account
        )

    except Exception as e:

        return render_template(
            "accounts.html",
            account={
                "balance": 0
            },
            error=str(e)
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