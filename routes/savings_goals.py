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


savings = Blueprint(
    "savings",
    __name__
)


# =========================================================
# TARGET TABUNGAN
# =========================================================

@savings.route("/savings", methods=["GET", "POST"])
def savings_page():

    # User wajib login
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    user_id = session["user_id"]

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:

        # =================================================
        # BUAT TARGET BARU
        # =================================================

        if request.method == "POST":

            name = request.form.get(
                "name",
                ""
            ).strip()

            target_amount = request.form.get(
                "target_amount",
                "0"
            )

            deadline = request.form.get(
                "deadline",
                ""
            ).strip()

            try:
                target_amount = float(
                    target_amount
                )
            except ValueError:
                target_amount = 0

            if not name:

                flash(
                    "Nama target wajib diisi.",
                    "error"
                )

                return redirect(
                    url_for("savings.savings_page")
                )

            if target_amount <= 0:

                flash(
                    "Nominal target harus lebih dari 0.",
                    "error"
                )

                return redirect(
                    url_for("savings.savings_page")
                )

            cursor.execute(
                """
                INSERT INTO savings_goals
                (
                    user_id,
                    name,
                    target_amount,
                    saved_amount,
                    deadline
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    name,
                    target_amount,
                    0,
                    deadline if deadline else None
                )
            )

            db.commit()

            flash(
                "Target tabungan berhasil dibuat.",
                "success"
            )

            return redirect(
                url_for("savings.savings_page")
            )

        # =================================================
        # AMBIL TARGET USER
        # =================================================

        cursor.execute(
            """
            SELECT *
            FROM savings_goals
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )

        goals = cursor.fetchall()

        # Hitung progress
        for goal in goals:

            target = float(
                goal["target_amount"] or 0
            )

            saved = float(
                goal["saved_amount"] or 0
            )

            if target > 0:

                progress = (
                    saved / target
                ) * 100

            else:

                progress = 0

            progress = min(
                progress,
                100
            )

            goal["progress"] = round(
                progress,
                1
            )

            goal["remaining"] = max(
                target - saved,
                0
            )

        return render_template(
            "savings.html",
            goals=goals
        )

    except Exception as e:

        db.rollback()

        print(
            "Savings Error:",
            e
        )

        flash(
            "Terjadi kesalahan pada target tabungan.",
            "error"
        )

        return redirect(
            url_for("dashboard.home")
        )

    finally:

        cursor.close()
        db.close()


# =========================================================
# TAMBAH DANA
# =========================================================

@savings.route(
    "/savings/add/<int:goal_id>",
    methods=["POST"]
)
def add_savings(goal_id):

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    user_id = session["user_id"]

    amount = request.form.get(
        "amount",
        "0"
    )

    try:
        amount = float(amount)
    except ValueError:
        amount = 0

    if amount <= 0:

        flash(
            "Nominal dana tidak valid.",
            "error"
        )

        return redirect(
            url_for("savings.savings_page")
        )

    db = get_db()
    cursor = db.cursor()

    try:

        # Pastikan target milik user
        cursor.execute(
            """
            SELECT id
            FROM savings_goals
            WHERE id = %s
            AND user_id = %s
            """,
            (
                goal_id,
                user_id
            )
        )

        goal = cursor.fetchone()

        if not goal:

            flash(
                "Target tidak ditemukan.",
                "error"
            )

            return redirect(
                url_for("savings.savings_page")
            )

        cursor.execute(
            """
            UPDATE savings_goals
            SET saved_amount = saved_amount + %s
            WHERE id = %s
            AND user_id = %s
            """,
            (
                amount,
                goal_id,
                user_id
            )
        )

        db.commit()

        flash(
            "Dana berhasil ditambahkan.",
            "success"
        )

        return redirect(
            url_for("savings.savings_page")
        )

    except Exception as e:

        db.rollback()

        print(
            "Add Savings Error:",
            e
        )

        flash(
            "Gagal menambahkan dana.",
            "error"
        )

        return redirect(
            url_for("savings.savings_page")
        )

    finally:

        cursor.close()
        db.close()


# =========================================================
# HAPUS TARGET
# =========================================================

@savings.route(
    "/savings/delete/<int:goal_id>",
    methods=["POST"]
)
def delete_goal(goal_id):

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    user_id = session["user_id"]

    db = get_db()
    cursor = db.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM savings_goals
            WHERE id = %s
            AND user_id = %s
            """,
            (
                goal_id,
                user_id
            )
        )

        db.commit()

        flash(
            "Target berhasil dihapus.",
            "success"
        )

    except Exception as e:

        db.rollback()

        print(
            "Delete Goal Error:",
            e
        )

    finally:

        cursor.close()
        db.close()

    return redirect(
        url_for("savings.savings_page")
    )
