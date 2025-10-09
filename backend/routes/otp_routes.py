# backend/routes/otp_routes.py
import hashlib
import hmac
import random
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from backend.models import Cart, OTPVerification, OrderItem, Product, User, Order
from backend.extensions import db

import os
from dotenv import load_dotenv

# smtp imports
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

# ===== Razorpay config =====


otp_bp = Blueprint("otp", __name__)

# ===== OTP Utilities =====
def generate_otp():
    return str(random.randint(100000, 999999)).zfill(6)

def send_email_smtp(to_email, otp_code):
    """
    Send OTP using Gmail SMTP. Uses MAIL_USERNAME and MAIL_PASSWORD from env.
    Returns True on success, False on failure (so caller can fallback to debug).
    """
    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")

    if not sender_email or not sender_password:
        print("❌ MAIL_USERNAME or MAIL_PASSWORD not set in environment; skipping SMTP send.")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = "Your OTP Code"

    body = f"Your OTP code is: {otp_code}. It will expire in 5 minutes."
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=20)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ OTP email sent to {to_email}")
        return True
    except Exception as e:
        # Print full exception for debugging (will show reason in console)
        print(f"❌ Failed to send OTP email: {e}")
        return False

# ===== Routes =====
@otp_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    try:
        user_id = session.get("user_id")
        data = request.get_json() or {}
        order_id = data.get("order_id")
        email = data.get("email")

        if not user_id and not email:
            return jsonify({"status": "error", "message": "Missing email"}), 401

        user = None
        if user_id:
            user = User.query.get(user_id)

        otp_code = generate_otp()
        expiry_time = datetime.utcnow() + timedelta(minutes=5)

        if user_id:
            otp_entry = OTPVerification(
                user_id=user_id,
                order_id=order_id,
                otp_code=otp_code,
                is_verified=False,
                created_at=datetime.utcnow(),
                expires_at=expiry_time
            )
            db.session.add(otp_entry)
            db.session.commit()

        final_email = email or (user.email if user else None)
        if not final_email:
            return jsonify({"status": "error", "message": "Final email not found"}), 400

        # Use SMTP send. If it fails, fallback to debug-printing OTP
        email_status = send_email_smtp(final_email, otp_code)

        if not email_status:
             print(f"DEBUG OTP for {final_email}: {otp_code}")
        return jsonify({
        "status": "error",
        "message": "Failed to send OTP email. Please try again later."
    }), 500


        return jsonify({
            "status": "success",
            "message": "OTP sent successfully",
            "expires_at": expiry_time.isoformat() + "Z"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@otp_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    try:
        user_id = session.get("user_id")
        data = request.get_json() or {}
        entered_otp = data.get("otp")
        order_id = data.get("order_id")
        email = data.get("email")

        if not entered_otp:
            return jsonify({"status": "error", "message": "OTP is required"}), 400

        if user_id:
            otp_record = OTPVerification.query.filter_by(
                user_id=user_id,
                order_id=order_id,
                is_verified=False
            ).order_by(OTPVerification.created_at.desc()).first()

            if not otp_record:
                return jsonify({"status": "error", "message": "No OTP found"}), 404

            if datetime.utcnow() > otp_record.expires_at:
                return jsonify({"status": "error", "message": "OTP expired"}), 400

            if otp_record.otp_code != entered_otp:
                return jsonify({"status": "error", "message": "Invalid OTP"}), 400

            otp_record.is_verified = True
            db.session.commit()

            order = Order.query.get(order_id)
            if order:
                order.order_status = "confirmed"
                db.session.commit()

            return jsonify({"status": "success", "message": "OTP verified"})
        else:
            # debug mode (email verification flow without a stored user)
            print(f"DEBUG verify OTP for email={email}: {entered_otp}")
            return jsonify({"status": "success", "message": "OTP verified (debug mode)"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500