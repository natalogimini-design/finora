from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import random

from db import get_db


# =========================================================
# BLUEPRINT AUTH
# =========================================================

auth = Blueprint(
    "auth",
    __name__
)


# =========================================================
# REGISTER
# =========================================================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        pin = request.form.get("pin", "").strip()

        # -------------------------------------------------
        # VALIDASI INPUT
        # -------------------------------------------------

        if not name or not email or not password or not pin:
            flash("Semua data wajib diisi.")
            return redirect(url_for("auth.register"))

        if len(pin) != 6 or not pin.isdigit():
            flash("PIN harus terdiri dari 6 angka.")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("Password minimal 6 karakter.")
            return redirect(url_for("auth.register"))

        # -------------------------------------------------
        # DATABASE
        # -------------------------------------------------

        db = get_db()
        cursor = db.cursor()

        try:

            # Cek email
            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            if cursor.fetchone():
                flash("Email sudah terdaftar.")
                return redirect(url_for("auth.register"))

            # -------------------------------------------------
            # HASH PASSWORD DAN PIN
            # -------------------------------------------------

            password_hash = generate_password_hash(password)
            pin_hash = generate_password_hash(pin)

            # -------------------------------------------------
            # INSERT USER
            # -------------------------------------------------

            cursor.execute(
                """
                INSERT INTO users
                (name, email, password_hash, pin_hash)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    name,
                    email,
                    password_hash,
                    pin_hash
                )
            )

            user_id = cursor.lastrowid

            # -------------------------------------------------
            # BUAT NOMOR REKENING
            # -------------------------------------------------

            account_number = None

            for _ in range(10):

                candidate = "FIN" + str(
                    random.randint(100000000, 999999999)
                )

                cursor.execute(
                    """
                    SELECT id
                    FROM accounts
                    WHERE account_number = %s
                    """,
                    (candidate,)
                )

                if not cursor.fetchone():
                    account_number = candidate
                    break

            if account_number is None:
                db.rollback()
                flash("Gagal membuat nomor rekening. Silakan coba lagi.")
                return redirect(url_for("auth.register"))

            # -------------------------------------------------
            # BUAT ACCOUNT
            # -------------------------------------------------

            cursor.execute(
                """
                INSERT INTO accounts
                (user_id, account_number, balance)
                VALUES (%s, %s, %s)
                """,
                (
                    user_id,
                    account_number,
                    0
                )
            )

            # -------------------------------------------------
            # SIMPAN SEMUA
            # -------------------------------------------------

            db.commit()

            flash(
                "Registrasi berhasil. Silakan login."
            )

            return redirect(
                url_for("auth.login")
            )

        except Exception as e:

            db.rollback()

            print("REGISTER ERROR:", e)

            flash(
                "Registrasi gagal. Silakan coba lagi."
            )

            return redirect(
                url_for("auth.register")
            )

        finally:

            cursor.close()
            db.close()

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        # -------------------------------------------------
        # VALIDASI
        # -------------------------------------------------

        if not email or not password:

            flash(
                "Email dan password wajib diisi."
            )

            return redirect(
                url_for("auth.login")
            )

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email,)
            )

            user = cursor.fetchone()

            # -------------------------------------------------
            # CEK PASSWORD
            # -------------------------------------------------

            if user and check_password_hash(
                user["password_hash"],
                password
            ):

                session.clear()

                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["user_email"] = user["email"]

                return redirect(
                    url_for("dashboard.home")
                )

            flash(
                "Email atau password salah."
            )

        except Exception as e:

            print("LOGIN ERROR:", e)

            flash(
                "Terjadi kesalahan saat login."
            )

        finally:

            cursor.close()
            db.close()

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@auth.route("/logout")
def logout():

    session.clear()

    flash(
        "Anda telah logout."
    )

    return redirect(
        url_for("auth.login")
    )
