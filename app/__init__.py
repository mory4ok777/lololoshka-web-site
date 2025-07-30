from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins='*')
def create_app():
    app = Flask(__name__)

    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat993.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app)
    from app.routes import main
    app.register_blueprint(main)
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):

        return User.query.get(int(user_id))
    

    return app

