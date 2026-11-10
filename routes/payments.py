from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import mysql.connector
from config import DB_CONFIG

payments = Blueprint("payments", __name__)


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


@payments.route("/payments", methods=["GET", "POST"])
def payment():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        category = request.form["category"]
        customer_number = request.form["customer_number"]
        amount = float(request.form["amount"])

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM accounts
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        account = cursor.fetchone()

        if account["balance"] < amount:

            cursor.close()
            db.close()

            flash("Saldo tidak mencukupi.")
            return redirect(url_for("payments.payment"))

        new_balance = account["balance"] - amount

        cursor.execute(
            """
            UPDATE accounts
            SET balance = %s
            WHERE user_id = %s
            """,
            (new_balance, session["user_id"])
        )

        cursor.execute(
            """
            INSERT INTO payments
            (user_id, category, customer_number, amount, status)
            VALUES (%s, %s, %s, %s, 'success')
            """,
            (
                session["user_id"],
                category,
                customer_number,
                amount
            )
        )

        cursor.execute(
            """
            INSERT INTO transactions
            (user_id, type, amount, description)
            VALUES (%s, 'payment', %s, %s)
            """,
            (
                session["user_id"],
                amount,
                f"Pembayaran {category}"
            )
        )

        db.commit()

        cursor.close()
        db.close()

        flash("Pembayaran berhasil.")

        return redirect(url_for("payments.payment"))

    return render_template("payments.html")