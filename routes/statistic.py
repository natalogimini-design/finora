from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)

from db import get_db

from datetime import datetime


statistics = Blueprint(
    "statistics",
    __name__
)


@statistics.route("/statistics")
def statistics_page():

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    user_id = session["user_id"]

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:

        # =================================================
        # TOTAL TRANSAKSI
        # =================================================

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(amount), 0)
                AS total
            FROM transactions
            WHERE user_id = %s
            """,
            (user_id,)
        )

        total_result = cursor.fetchone()

        total_transactions = float(
            total_result["total"] or 0
        )

        # =================================================
        # JUMLAH TRANSAKSI
        # =================================================

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM transactions
            WHERE user_id = %s
            """,
            (user_id,)
        )

        count_result = cursor.fetchone()

        transaction_count = count_result["total"]

        # =================================================
        # TRANSAKSI BULANAN
        # =================================================

        cursor.execute(
            """
            SELECT
                YEAR(created_at) AS year,
                MONTH(created_at) AS month,
                COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE user_id = %s
            GROUP BY
                YEAR(created_at),
                MONTH(created_at)
            ORDER BY
                YEAR(created_at) DESC,
                MONTH(created_at) DESC
            LIMIT 6
            """,
            (user_id,)
        )

        monthly = cursor.fetchall()

        # =================================================
        # TARGET TABUNGAN
        # =================================================

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_goals,
                COALESCE(
                    SUM(target_amount),
                    0
                ) AS total_target,
                COALESCE(
                    SUM(saved_amount),
                    0
                ) AS total_saved
            FROM savings_goals
            WHERE user_id = %s
            """,
            (user_id,)
        )

        savings = cursor.fetchone()

        total_target = float(
            savings["total_target"] or 0
        )

        total_saved = float(
            savings["total_saved"] or 0
        )

        if total_target > 0:

            savings_progress = (
                total_saved /
                total_target
            ) * 100

        else:

            savings_progress = 0

        savings_progress = min(
            savings_progress,
            100
        )

        # =================================================
        # BATAS PENGELUARAN BULAN INI
        # =================================================

        now = datetime.now()

        cursor.execute(
            """
            SELECT limit_amount
            FROM spending_limits
            WHERE user_id = %s
            AND month = %s
            AND year = %s
            LIMIT 1
            """,
            (
                user_id,
                now.month,
                now.year
            )
        )

        budget = cursor.fetchone()

        budget_limit = float(
            budget["limit_amount"]
            if budget
            else 0
        )

        return render_template(
            "statistics.html",
            total_transactions=total_transactions,
            transaction_count=transaction_count,
            monthly=monthly,
            total_target=total_target,
            total_saved=total_saved,
            savings_progress=round(
                savings_progress,
                1
            ),
            budget_limit=budget_limit
        )

    except Exception as e:

        print(
            "Statistics Error:",
            e
        )

        return (
            "Terjadi kesalahan saat "
            "mengambil statistik.",
            500
        )

    finally:

        cursor.close()
        db.close()