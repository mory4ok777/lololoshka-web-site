from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify
from flask_login import login_required, logout_user, fresh_login_required, current_user
from .models import User, MSG, Chat,db
from flask_login import login_user
from flask_socketio import send,join_room,leave_room
from . import socketio
from flask import send_from_directory
import os
from datetime import datetime
main = Blueprint('main', __name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTOS_DIR = os.path.join(BASE_DIR,'photos')
AUDIO_DIR = os.path.join(BASE_DIR,'audio_messages')


@main.route('/audio_messages/<filename>')
def send_audio(filename):
    try:
        return send_from_directory(AUDIO_DIR, filename)
    except FileNotFoundError:
        return "Audio not found", 404

@main.route('/photos/<filename>')
def send_photo(filename):
    try:
        return send_from_directory(PHOTOS_DIR, filename)
    except FileNotFoundError:
        return "Photo not found", 404
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
        ((Chat.receiver_id == friend.id) and (Chat.sender_id == current_user.id) or (Chat.receiver_id == current_user.id)
         and (Chat.sender_id == friend.id))
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






import base64

@socketio.on('audio_message')
def handle_audio_message(data):
    try:
        chat_id = data['chat_id']
        user_id = data['user_id']
        audio_data = data['audio']
        mime_type = data.get('mime_type', 'audio/webm')
        
  
        os.makedirs(AUDIO_DIR, exist_ok=True)
        

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"audio_{timestamp}_{user_id}.webm"
        filepath = os.path.join(AUDIO_DIR, filename)
        

        with open(filepath, 'wb') as f:
            if isinstance(audio_data, str):

                audio_data = base64.b64decode(audio_data.split(',')[1] if ',' in audio_data else audio_data)
            f.write(audio_data)
        

        message = MSG(
            sender_id=user_id,
            chat_id=chat_id,
            message_type='audio',
            media_url=f'/audio_messages/{filename}',
            mime_type=mime_type,
            timestamp=datetime.now()
        )
        
        db.session.add(message)
        db.session.commit()
        

        socketio.emit('audio_message', {
            'message_id': message.id,
            'chat_id': chat_id,
            'audio_url': f'/audio_messages/{filename}',
            'sender_id': user_id,
            'mime_type': mime_type,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, room=str(chat_id))
        
    except Exception as e:
        print(f"Error processing audio: {str(e)}")                     
        





@socketio.on('photo_message')
def handle_photo_message(data):
    try:
        chat_id = data['chat_id']
        user_id = data['user_id']
        image_data = data['image']
        mime_type = data.get('mime_type','image/jpeg')
        filename = data.get('file_name','photo.jpg')

        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]   
            
        image_bytes = base64.b64decode(image_data)
        os.makedirs(PHOTOS_DIR, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_ext = os.path.splitext(filename)[1] or '.jpg'    
        new_filename = f"photo_{timestamp}_{user_id}{file_ext}"
        filepath = os.path.join(PHOTOS_DIR,new_filename)
        with open(filepath, 'wb') as f:
            f.write(image_bytes)

        message = MSG(
            sender_id = user_id,
            chat_id = chat_id,
            message_type = 'photo',
            media_url = f'/photos/{new_filename}',
            mime_type = mime_type,
            timestamp = datetime.now()
        )
        db.session.add(message)
        db.session.commit()

        print(f"Saved photo: {new_filename}")

        socketio.emit('photo_message', {
            'message_id': message.id,
            'chat_id': chat_id,
            'sender_id': user_id,
            'image_url': f'/photos/{new_filename}?t={int(datetime.now().timestamp())}',
            'mime_type': mime_type,
            'timestamp': timestamp,
        }, room=str(chat_id))
    except Exception as e:
        print(f"Photo message error: {str(e)}")
                                                                                                                                                                                                          