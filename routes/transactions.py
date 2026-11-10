from flask import Blueprint, render_template, session, redirect, url_for
import mysql.connector
from config import DB_CONFIG

transactions = Blueprint("transactions", __name__)


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


@transactions.route("/transactions")
def history():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Riwayat transfer masuk & keluar milik pengguna
        cursor.execute(
            """
            SELECT
                t.id,
                t.amount,
                t.note,
                t.status,
                t.created_at,
                sender.account_number   AS sender_number,
                receiver.account_number AS receiver_number,
                CASE
                    WHEN sender.user_id = %s THEN 'Keluar'
                    ELSE 'Masuk'
                END AS transfer_type
            FROM transfers t
            JOIN accounts sender
                ON t.sender_account_id = sender.id
            JOIN accounts receiver
                ON t.receiver_account_id = receiver.id
            WHERE sender.user_id = %s
               OR receiver.user_id = %s
            ORDER BY t.created_at DESC, t.id DESC
            LIMIT 100
            """,
            (session["user_id"],) * 3
        )
        data = cursor.fetchall()

    finally:
        cursor.close()
        db.close()

    total_in = sum(r["amount"] for r in data if r["transfer_type"] == "Masuk")
    total_out = sum(r["amount"] for r in data if r["transfer_type"] == "Keluar")

    return render_template(
        "transactions.html",
        transactions=data,
        total_in=total_in,
        total_out=total_out
    )
