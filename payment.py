from flask import Blueprint, render_template, request, redirect, flash
from flask_login import login_required, current_user

from extensions import db
from models import Payment

payment = Blueprint("payment", __name__)


@payment.route("/payment", methods=["GET", "POST"])
@login_required
def payment_page():

    if request.method == "POST":

        txn = request.form.get("transaction_id", "").strip()

        if txn == "":
            flash("Please enter Transaction ID.", "danger")
            return redirect("/payment")

        existing = Payment.query.filter_by(transaction_id=txn).first()

        if existing:
            flash("Transaction ID already submitted.", "danger")
            return redirect("/payment")

        payment = Payment(
            user_id=current_user.id,
            amount=2000,
            transaction_id=txn,
            status="Pending"
        )

        db.session.add(payment)
        db.session.commit()

        flash(
            "Payment submitted successfully. Waiting for Admin Approval.",
            "success"
        )

        return redirect("/payment")

    return render_template(
        "payment.html",
        amount=2000,
        upi="9619692682@kotakbank"
    )
