from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from db import get_db

from datetime import datetime


# ============================================================
# BLUEPRINT
# ============================================================

budget = Blueprint(
    "budget",
    __name__
)


# ============================================================
# BUDGET PAGE
# ============================================================

@budget.route(
    "/budget",
    methods=["GET", "POST"]
)
def budget_page():

    # ========================================================
    # CEK LOGIN
    # ========================================================

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    user_id = session["user_id"]

    db = None
    cursor = None

    try:

        # ====================================================
        # DATABASE
        # ====================================================

        db = get_db()
        cursor = db.cursor()


        # ====================================================
        # AMBIL DATA REKENING USER
        # ====================================================

        account = None

        cursor.execute(
            """
            SELECT
                account_number,
                balance
            FROM accounts
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        account = cursor.fetchone()


        # ====================================================
        # PROSES SIMPAN BUDGET
        # ====================================================

        if request.method == "POST":

            budget_limit = request.form.get(
                "budget_limit",
                ""
            ).strip()

            budget_period = request.form.get(
                "budget_period",
                "monthly"
            ).strip()


            # ------------------------------------------------
            # VALIDASI
            # ------------------------------------------------

            if not budget_limit:

                flash(
                    "Batas pengeluaran harus diisi.",
                    "error"
                )

                return redirect(
                    url_for("budget.budget_page")
                )


            try:

                budget_limit = float(
                    budget_limit
                )

            except ValueError:

                flash(
                    "Batas pengeluaran tidak valid.",
                    "error"
                )

                return redirect(
                    url_for("budget.budget_page")
                )


            if budget_limit < 0:

                flash(
                    "Batas pengeluaran tidak boleh negatif.",
                    "error"
                )

                return redirect(
                    url_for("budget.budget_page")
                )


            # =================================================
            # CEK APAKAH TABEL BUDGET TERSEDIA
            # =================================================
            #
            # Bagian ini menggunakan tabel:
            # budgets
            #
            # Jika tabel budget kamu sudah berbeda,
            # pertahankan query budget lama kamu.
            #
            # =================================================

            try:

                cursor.execute(
                    """
                    SELECT id
                    FROM budgets
                    WHERE user_id = %s
                    LIMIT 1
                    """,
                    (user_id,)
                )

                existing_budget = cursor.fetchone()


                if existing_budget:

                    cursor.execute(
                        """
                        UPDATE budgets
                        SET
                            budget_limit = %s,
                            budget_period = %s
                        WHERE user_id = %s
                        """,
                        (
                            budget_limit,
                            budget_period,
                            user_id
                        )
                    )

                else:

                    cursor.execute(
                        """
                        INSERT INTO budgets
                        (
                            user_id,
                            budget_limit,
                            budget_period
                        )
                        VALUES
                        (
                            %s,
                            %s,
                            %s
                        )
                        """,
                        (
                            user_id,
                            budget_limit,
                            budget_period
                        )
                    )


                db.commit()


                flash(
                    "Budget berhasil disimpan.",
                    "success"
                )


            except Exception:

                db.rollback()

                flash(
                    "Data budget belum dapat disimpan. "
                    "Pastikan tabel budgets tersedia.",
                    "error"
                )


            return redirect(
                url_for("budget.budget_page")
            )


        # ====================================================
        # AMBIL DATA BUDGET
        # ====================================================

        budget_data = None

        try:

            cursor.execute(
                """
                SELECT
                    id,
                    budget_limit,
                    budget_period
                FROM budgets
                WHERE user_id = %s
                LIMIT 1
                """,
                (user_id,)
            )

            budget_data = cursor.fetchone()

        except Exception:

            budget_data = None


        # ====================================================
        # TAMPILKAN HALAMAN
        # ====================================================

        return render_template(
            "budget.html",
            account=account,
            budget=budget_data
        )


    except Exception as e:

        print(
            "BUDGET ERROR:",
            e
        )

        flash(
            "Terjadi kesalahan saat membuka Budget.",
            "error"
        )

        return render_template(
            "budget.html",
            account=None,
            budget=None
        )


    finally:

        if cursor:

            try:
                cursor.close()
            except Exception:
                pass