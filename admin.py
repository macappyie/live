from flask import Blueprint, render_template, redirect
from flask_login import login_required, current_user

from extensions import db
from models import User, Payment

admin = Blueprint("admin", __name__)


@admin.route("/admin")
@login_required
def admin_home():

    if not current_user.is_admin:
        return redirect("/dashboard")

    payments = Payment.query.order_by(Payment.created_at.desc()).all()

    return render_template(
        "admin/dashboard.html",
        payments=payments
    )


@admin.route("/admin/approve/<int:id>")
@login_required
def approve_payment(id):

    if not current_user.is_admin:
        return redirect("/dashboard")

    payment = Payment.query.get_or_404(id)

    payment.status = "Approved"

    user = User.query.get(payment.user_id)

    user.is_paid = True

    db.session.commit()

    return redirect("/admin")


@admin.route("/admin/reject/<int:id>")
@login_required
def reject_payment(id):

    if not current_user.is_admin:
        return redirect("/dashboard")

    payment = Payment.query.get_or_404(id)

    payment.status = "Rejected"

    db.session.commit()

    return redirect("/admin")
