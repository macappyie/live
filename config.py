import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:

    SECRET_KEY = "74de1cc8c68d6f70b092fbcaa6ef638ab4fef1f41487c4b508ca717649935b07"

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "database", "moneyassure.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    RAZORPAY_KEY_ID = ""

    RAZORPAY_KEY_SECRET = ""

    SUBSCRIPTION_PRICE = 2000

    COMPANY_NAME = "MoneyAssure"

    COMPANY_EMAIL = "optionstradingstarted@gmail.com"

    COMPANY_PHONE = ""

    COMPANY_ADDRESS = "Navi Mumbai"

    SESSION_PERMANENT = False
