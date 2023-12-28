from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .extensions import db,bcrypt,login_manager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_uploads import UploadSet, configure_uploads, ALL
import os


def create_app():

    app=Flask(__name__)
    CORS(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost:5432/flask_db'
    app.config['SECRET_KEY']='sgdfg'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Bu satır SQLAlchemy uyarılarını engeller
    #add_file_to_event
    app.config['UPLOADED_FILES_DEST']= r'C:\Users\burak\OneDrive\Masaüstü\Flask-main\uploads'
    #add_file_to_event
    files=UploadSet('files', ALL) 
    configure_uploads(app, files)
    uploads_folder = 'uploads'
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)
    from .routes import main as main_routes
    app.register_blueprint(main_routes)

    migrate=Migrate(app,db)
    
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app,db)

    
    
    login_manager.login_view = "login_page"  # URL fonksiyon ismi
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User  # User modelini yerel olarak import et
        return User.query.get(int(user_id))

    # Uygulama rotalarınızı burada tanımlayın veya import edin
    from .routes import (home_page, register_page, login_page, logout_page)

    # Uygulama rotalarını ekleyin
    app.add_url_rule('/', 'home_page', home_page)
    app.add_url_rule('/home', 'home_page', home_page)
    app.add_url_rule('/register', 'register_page', register_page, methods=['GET', 'POST'])
    app.add_url_rule('/login', 'login_page', login_page, methods=['GET', 'POST'])
    app.add_url_rule('/logout', 'logout_page', logout_page)

    return app

