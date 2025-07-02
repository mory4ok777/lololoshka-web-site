from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify
from flask_login import login_required, logout_user, fresh_login_required, current_user
from .models import User, MSG, Chat,db
from flask_login import login_user
from flask_socketio import send,join_room,leave_room
from . import socketio

main = Blueprint('main', __name__)
@main.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.cheque_password(password):
            login_user(user)
            return redirect(url_for("main.home"))
    return render_template("login.html")

@main.route('/register', methods=["GET","POST"])
def register():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            user = User.query.filter_by(username=username).first()
            if user:
                flash('This username is taken, please choose another one')
            else:
                new_user = User(username = username)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect(url_for('main.home'))
        return render_template('register.html')
@main.route('/')
@login_required
def home():
    messages = MSG.query.all()
    users = User.query.all()
    return render_template("chat.html", messages=messages, users=users)
@main.route('/chat/<int:chat_id>',methods = ['GET'])
@login_required
def chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if current_user.id not in [chat.receiver_id,chat.sender_id]:
        flash("You're not a part of this conversation, try and make one")
    messages = MSG.query.filter_by(chat_id = chat.id).order_by(MSG.timestamp.asc()).all()
    return render_template('chat.html',messages=messages, chat = chat)





@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))

@main.route("/search_users", methods=['GET'])
@login_required
def search_users():
    query = request.args.get('query')
    if query:
        users = User.query.filter(User.username.contains(query)).all()
        users_data = [{"id": user.id, "username": user.username} for user in users]
        return jsonify(users_data)
    return jsonify([])
@main.route("/start_chat/<int:user_id>", methods = ['GET','POST'])
@login_required
def start_chat(user_id):
    friend = User.query.get_or_404(user_id)
    chat = Chat.query.filter(
        ((Chat.receiver_id == friend.id) and (Chat.sender_id == current_user.id) or (Chat.receiver_id == current_user.id) and (Chat.sender_id == friend.id))
    ).first()
    print(current_user.id, friend.id)
    if not chat:
        chat = Chat(sender_id = friend.id,receiver_id = current_user.id)
        db.session.add(chat)
        db.session.commit()
    return redirect(url_for('main.chat',chat_id=chat.id))




@socketio.on('message')
def handle_message(data):
    chat_id = data['chat_id']
    text = data['text']
    user_id = data['user_id']
    
    
    message = MSG(sender_id=user_id, chat_id=chat_id, text=text)
    db.session.add(message)
    db.session.commit()
    
    send({
        "chat_id": chat_id,
        "text": text,
        "sender_id": user_id,
        "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    }, room=str(chat_id))


@socketio.on('join')
def on_join(data):
    chat_id = data['chat_id']
    join_room(str(chat_id))

@socketio.on('leave')
def on_join(data):
    chat_id = data['chat_id']
    leave_room(str(chat_id))
                                                                                                                                                                                                                                    