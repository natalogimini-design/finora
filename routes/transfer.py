
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import mysql.connector
from decimal import Decimal, InvalidOperation
from config import DB_CONFIG

transfer = Blueprint("transfer", __name__)


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


@transfer.route("/transfer", methods=["GET", "POST"])
def transfer_page():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Ambil rekening milik pengguna yang sedang login
        cursor.execute(
            """
            SELECT id, account_number, balance
            FROM accounts
            WHERE user_id = %s
            LIMIT 1
            """,
            (session["user_id"],)
        )
        account = cursor.fetchone()

        if not account:
            flash("Rekening FINORA kamu belum tersedia.", "error")
            return redirect(url_for("dashboard.home"))

        if request.method == "POST":
            receiver_number = request.form.get(
                "account_number", ""
            ).strip()

            amount_text = request.form.get("amount", "").strip()
            note = request.form.get("note", "").strip()

            # Validasi nominal
            try:
                amount = Decimal(amount_text)
                if not amount.is_finite() or amount <= 0:
                    raise InvalidOperation
                amount = amount.quantize(Decimal("0.01"))
                if amount > Decimal("999999999999.99"):
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                flash("Nominal transfer tidak valid.", "error")
                return redirect(url_for("transfer.transfer_page"))

            if not receiver_number:
                flash("Nomor rekening tujuan wajib diisi.", "error")
                return redirect(url_for("transfer.transfer_page"))

            if len(note) > 255:
                flash("Catatan maksimal 255 karakter.", "error")
                return redirect(url_for("transfer.transfer_page"))

            if receiver_number == account["account_number"]:
                flash("Tidak bisa transfer ke rekening sendiri.", "error")
                return redirect(url_for("transfer.transfer_page"))

            # Cari rekening tujuan
            cursor.execute(
                """
                SELECT id, account_number
                FROM accounts
                WHERE account_number = %s
                """,
                (receiver_number,)
            )
            receiver = cursor.fetchone()

            if not receiver:
                flash("Nomor rekening tujuan tidak ditemukan.", "error")
                return redirect(url_for("transfer.transfer_page"))

            # Kunci kedua rekening selama proses transfer
            account_ids = sorted([account["id"], receiver["id"]])
            placeholders = ", ".join(["%s"] * len(account_ids))

            cursor.execute(
                f"""
                SELECT id, user_id, account_number, balance
                FROM accounts
                WHERE id IN ({placeholders})
                ORDER BY id
                FOR UPDATE
                """,
                tuple(account_ids)
            )
            locked_accounts = {
                row["id"]: row for row in cursor.fetchall()
            }

            sender = locked_accounts.get(account["id"])
            receiver_locked = locked_accounts.get(receiver["id"])

            if not sender or not receiver_locked:
                db.rollback()
                flash("Rekening tidak dapat diproses.", "error")
                return redirect(url_for("transfer.transfer_page"))

            if Decimal(str(sender["balance"] or 0)) < amount:
                db.rollback()
                flash("Saldo tidak mencukupi untuk transfer.", "error")
                return redirect(url_for("transfer.transfer_page"))

            # Kurangi saldo pengirim
            cursor.execute(
                """
                UPDATE accounts
                SET balance = balance - %s
                WHERE id = %s
                """,
                (amount, sender["id"])
            )

            # Tambahkan saldo penerima
            cursor.execute(
                """
                UPDATE accounts
                SET balance = balance + %s
                WHERE id = %s
                """,
                (amount, receiver_locked["id"])
            )

            # Simpan catatan transfer
            cursor.execute(
                """
                INSERT INTO transfers
                (sender_account_id, receiver_account_id,
                 amount, note, status)
                VALUES (%s, %s, %s, %s, 'success')
                """,
                (
                    sender["id"],
                    receiver_locked["id"],
                    amount,
                    note or None
                )
            )

            db.commit()

            flash("Transfer berhasil dilakukan!", "success")
            return redirect(url_for("transfer.transfer_page"))

        # Ambil saldo terbaru
        cursor.execute(
            """
            SELECT id, account_number, balance
            FROM accounts
            WHERE user_id = %s
            LIMIT 1
            """,
            (session["user_id"],)
        )
        account = cursor.fetchone()

        # Riwayat transfer masuk dan keluar
        cursor.execute(
            """
            SELECT
                t.id,
                t.amount,
                t.note,
                t.created_at,
                t.status,
                sender.account_number AS sender_number,
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
            LIMIT 10
            """,
            (
                session["user_id"],
                session["user_id"],
                session["user_id"]
            )
        )
        transfer_history = cursor.fetchall()

        return render_template(
            "transfer.html",
            account=account,
            transfer_history=transfer_history
        )

    except Exception:
        db.rollback()
        raise

    finally:
        cursor.close()
        db.close()
