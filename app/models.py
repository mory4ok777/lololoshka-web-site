from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True)
    password_hashd = db.Column(db.Text, nullable=False)

    # Relationships
    chats_as_friend1 = db.relationship('Chat', foreign_keys='Chat.sender_id', backref='user1', lazy=True)
    chats_as_friend2 = db.relationship('Chat', foreign_keys='Chat.receiver_id', backref='user2', lazy=True)

    def set_password(self, password):
        self.password_hashd = generate_password_hash(password)

    def cheque_password(self, password):
        return check_password_hash(self.password_hashd, password)

    @property
    def chats(self):
        return self.chats_as_friend1 + self.chats_as_friend2

class MSG(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    text = db.Column(db.String(500))  # Made nullable for media messages
    timestamp = db.Column(db.DateTime, default=datetime.now)
    

    message_type = db.Column(db.String(10), default='text') 
    media_url = db.Column(db.String(255))  
    mime_type = db.Column(db.String(50))  

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])
    messages = db.relationship('MSG', backref='chat', lazy='dynamic')

