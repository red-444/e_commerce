from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.form or request.json
    if not data.get('email') or not data.get('password') or not data.get('username'):
        return jsonify({'error':'missing fields'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error':'email exists'}), 400
    user = User(username=data['username'],
                fullname=data.get('fullname'),
                email=data['email'],
                phone=data.get('phone'),
                password=generate_password_hash(data['password']))
    db.session.add(user); db.session.commit()
    # login -> set session
    session['user_id'] = str(user.id)
    return redirect(url_for('product.list_page'))  # or JSON
