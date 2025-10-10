# backend/routes/otp_routes.py
import os
import random
import requests
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from backend.models import Cart, OTPVerification, OrderItem, Product, User, Order
from backend.extensions import db
from dotenv import load_dotenv

load_dotenv()

otp_bp = Blueprint("otp", __name__)

# ====== Utility Functions ======
def generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999)).zfill(6)


# ====== Resend API Email Sender ======
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

def send_otp_email(to_email, otp):
    """Send OTP email using Resend API."""
    if not RESEND_API_KEY:
        print("❌ RESEND_API_KEY not found in environment variables.")
        return False

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "from": "Resend <onboarding@resend.dev>",
        "to": [to_email],
        "subject": "Your OTP Code",
        "html": f"<h2>Your OTP is {otp}</h2><p>This code will expire in 5 minutes.</p>",
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"✅ OTP email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send OTP via Resend API: {e}")
        return False


# ====== Routes ======
@otp_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    """Resend OTP to user email using Resend API."""
    try:
        user_id = session.get("user_id")
        data = request.get_json() or {}
        order_id = data.get("order_id")
        email = data.get("email")

        if not user_id and not email:
            return jsonify({"status": "error", "message": "Missing email"}), 401

        user = User.query.get(user_id) if user_id else None
        final_email = email or (user.email if user else None)

        if not final_email:
            return jsonify({"status": "error", "message": "Email not found"}), 400

        otp_code = generate_otp()
        expiry_time = datetime.utcnow() + timedelta(minutes=5)

        # Store OTP in DB
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

        # Send OTP via Resend API
        if not send_otp_email(final_email, otp_code):
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
    """Verify OTP entered by user."""
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
            # Fallback mode (debug)
            print(f"DEBUG verify OTP for email={email}: {entered_otp}")
            return jsonify({"status": "success", "message": "OTP verified (debug mode)"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
