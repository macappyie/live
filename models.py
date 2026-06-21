from datetime import datetime

from flask_login import UserMixin

from extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(150), nullable=False)

    email = db.Column(db.String(150), unique=True, nullable=False)

    mobile = db.Column(db.String(20))

    password = db.Column(db.String(255), nullable=False)

    is_admin = db.Column(db.Boolean, default=False)

    is_active = db.Column(db.Boolean, default=True)

    is_paid = db.Column(db.Boolean, default=False)

    subscription_end = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.email}>"
class Payment(db.Model):

    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    amount = db.Column(db.Integer, nullable=False)

    transaction_id = db.Column(db.String(100), unique=True, nullable=False)

    status = db.Column(db.String(20), default="Pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="payments")

