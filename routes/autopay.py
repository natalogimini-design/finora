from flask import Blueprint, render_template, request, redirect, url_for, session
import mysql.connector
from config import DB_CONFIG

autopay = Blueprint("autopay", __name__)


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


@autopay.route("/autopay", methods=["GET", "POST"])
def index():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":

        name = request.form["name"]
        category = request.form["category"]
        amount = request.form["amount"]
        payment_date = request.form["payment_date"]

        cursor.execute(
            """
            INSERT INTO autopay
            (user_id, name, category, amount, payment_date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                name,
                category,
                amount,
                payment_date
            )
        )

        db.commit()

    cursor.execute(
        """
        SELECT *
        FROM autopay
        WHERE user_id = %s
        ORDER BY payment_date ASC
        """,
        (session["user_id"],)
    )

    schedules = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "autopay.html",
        schedules=schedules
    )