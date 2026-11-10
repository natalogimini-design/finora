
import os

from flask import Flask, redirect, url_for, session

# ============================================================
# IMPORT BLUEPRINT
# ============================================================

from routes.auth import auth
from routes.dashboard import dashboard
from routes.transactions import transactions
from routes.payments import payments
from routes.savings import savings
from routes.investments import investments
from routes.autopay import autopay
from routes.transfer import transfer
from routes.topup import topup
from routes.accounts import accounts_bp
from routes.budget import budget

# ============================================================
# CREATE APP
# ============================================================

app = Flask(__name__)

# ============================================================
# SECRET KEY
# ============================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "finora-local-development-key"
)

# ============================================================
# REGISTER BLUEPRINT
# ============================================================

app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(transactions)
app.register_blueprint(payments)
app.register_blueprint(savings)
app.register_blueprint(investments)
app.register_blueprint(autopay)
app.register_blueprint(transfer)
app.register_blueprint(topup)
app.register_blueprint(accounts_bp)
app.register_blueprint(budget)

# ============================================================
# ROOT
# ============================================================

@app.route("/")
def index():

    if "user_id" in session:
        return redirect(url_for("dashboard.home"))

    return redirect(url_for("auth.login"))

# ============================================================
# 404 ERROR
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>404 - FINORA</title>

        <style>
            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #080b14;
                color: #ffffff;
                font-family: Arial, sans-serif;
                padding: 20px;
            }

            .error-box {
                width: 100%;
                max-width: 480px;
                padding: 40px 30px;
                text-align: center;
                background: #101522;
                border: 1px solid #202a3d;
                border-radius: 20px;
            }

            .code {
                font-size: 72px;
                font-weight: 800;
            }

            h1 {
                margin: 10px 0;
            }

            p {
                color: #9ca8bd;
                line-height: 1.6;
            }

            a {
                display: inline-block;
                margin-top: 15px;
                padding: 12px 22px;
                border-radius: 12px;
                background: #5865f2;
                color: white;
                text-decoration: none;
            }
        </style>
    </head>

    <body>
        <div class="error-box">
            <div class="code">404</div>
            <h1>Halaman Tidak Ditemukan</h1>
            <p>Halaman yang kamu cari tidak tersedia.</p>
            <a href="/">Kembali ke FINORA</a>
        </div>
    </body>
    </html>
    """, 404

# ============================================================
# 500 ERROR
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>500 - FINORA</title>

        <style>
            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #080b14;
                color: white;
                font-family: Arial, sans-serif;
                padding: 20px;
            }

            .error-box {
                width: 100%;
                max-width: 480px;
                padding: 40px 30px;
                text-align: center;
                background: #101522;
                border: 1px solid #202a3d;
                border-radius: 20px;
            }

            .code {
                font-size: 72px;
                font-weight: 800;
            }

            h1 {
                margin: 10px 0;
            }

            p {
                color: #9ca8bd;
                line-height: 1.6;
            }

            a {
                display: inline-block;
                margin-top: 15px;
                padding: 12px 22px;
                border-radius: 12px;
                background: #5865f2;
                color: white;
                text-decoration: none;
            }
        </style>
    </head>

    <body>
        <div class="error-box">
            <div class="code">500</div>
            <h1>Terjadi Kesalahan</h1>
            <p>FINORA mengalami kesalahan saat memproses halaman.</p>
            <a href="/">Kembali ke FINORA</a>
        </div>
    </body>
    </html>
    """, 500

# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    )