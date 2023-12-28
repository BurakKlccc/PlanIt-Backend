from .extensions import db
from flask import render_template, redirect, url_for, flash, request,Blueprint,jsonify,make_response,session
from .models import User,Event,Session, FilePath
from flask_login import login_user, logout_user, current_user,login_required
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
#add_file_to_event
from flask_uploads import UploadSet, configure_uploads, ALL
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os


#routesa initten app geliyor 
main=Blueprint("main", __name__)



@main.route('/<int:user_id>')
@main.route('/home/<int:user_id>')
def home_page(user_id):
    render_template('home.html')

@main.route('/register', methods=['GET', 'POST'])
def register_page():

    data = request.get_json()
    unique_id=str(uuid.uuid4())
    if not data:
        return make_response("invalid content type",415)
    
    if User.query.filter_by(username=data["username"]).first():
        return jsonify(message="Bu kullanıcı adı zaten kullanılıyor."),409
    
    
    if User.query.filter_by(email_address=data["email"]).first():
        return jsonify(message="Bu email zaten kullanılıyor."),409
    
    hashed_password=generate_password_hash(data["password"])
    
    user_to_create = User(id=unique_id,
                        username=data['username'],
                          email_address=data['email'],
                          password_hash=hashed_password)  # Burada şifre hash'lenmelidir
     # Kullanıcıyı veritabanına ekle
    
    try:
        db.session.add(user_to_create)
        db.session.commit()
        return jsonify({"Message":"Success"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Kullanıcı kaydedilemedi.', 'error': str(e)}), 500
    # Başarılı kayıt için JSON cevabı döndür

@main.route('/login', methods=['GET', 'POST'])
def login_page():
    data=request.get_json()
    
    if not data:
        return make_response("invalid content type",415)
    
    user=User.query.filter_by(username=data["username"]).first()
    #kullanıcı adı bulunduysa
 
    if (user):    
        if check_password_hash(user.password_hash,data["password"]):
            session=create_session(user.id)
            return jsonify({"Message":"Success"})
        else:
            return jsonify(message="Şifreler uyuşmuyor"),406
    else:
        return jsonify(message="Başarısız"), 404
    
def create_session(user_id):
    new_session = Session(
        user_id=user_id,
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    db.session.add(new_session)
    db.session.commit()
    return new_session

def check_session_active(session_id):
    session = Session.query.get(session_id)
    if session and session.is_active:
        return True
    return False

#@login_required
@main.route('/create_event', methods=['POST'])
def create_event():
    data = request.get_json()
    #title date owner id
    unique_id=str(uuid.uuid4())
    new_event = Event(id=unique_id,title=data['title'], date=data['date'])
    db.session.add(new_event)
    db.session.commit()
    return jsonify({'message': 'New event created.'}), 201

@main.route('/delete_event/<id>', methods=['DELETE'])
def delete_event(id):
    #find the event to delete by its id
    event_to_delete = Event.query.get(id)
    if not event_to_delete:
        return jsonify({'error': 'Event not found'}), #hata kodeu girilecek
    #delete it from database
    db.session.delete(event_to_delete)
    db.session.commit()
    #return confirmation message
    return jsonify({'message': 'Event deleted.'}), 202


@main.route('/update_event/<id>', methods=['PUT'])
def update_event(id):
    data = request.get_json()
    #find the event to update by its id
    event_to_update = Event.query.get(id)
    if not event_to_update:
        return jsonify({'error': 'Event not found'}), #hata kodu girilecek
    #update the event (title, date)
    event_to_update.title = data.get('title', event_to_update.title)
    event_to_update.date = data.get('date', event_to_update.date)
    db.session.commit()
    return jsonify({'message': 'Event updated.'}), 203

@main.route('/add_file_to_event/<id>', methods=['PUT'])
def add_file_to_event(id):
    event_to_add_file = Event.query.get(id)

    if not event_to_add_file:
        return jsonify({'error': 'Event not found'}), 404
    
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        file.save(file_path)
        event_to_add_file.file_path = file_path 
        db.session.commit()

        file_path_id = str(uuid.uuid4())
        
        file_path_obj = FilePath(id=file_path_id, path=file_path, event_id=event_to_add_file.id)
        db.session.add(file_path_obj)
        db.session.commit()
        return jsonify({'message': 'File uploaded successfully', 'filename': filename}), 204
    else:
        return jsonify({'error': 'Invalid or missing file'}), 406

def allowed_file(filename):
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@main.route('/delete_file_from_event/<event_id>/<file_path_id>', methods=['DELETE'])
def delete_file_from_event(event_id, file_path_id):
    event_to_delete_file = Event.query.get(event_id)
    
    if not event_to_delete_file:
        return jsonify({'error': 'Event not found'}), 404

    file_path_obj = FilePath.query.get(file_path_id)

    if not file_path_obj or file_path_obj.event_id != event_to_delete_file.id:
        return jsonify({'error': 'File path not found for the event'}), 404

    db.session.delete(file_path_obj)
    os.remove(file_path_obj.path)
    db.session.commit()

    return jsonify({'message': 'File deleted successfully'}), 204



@login_required
@main.route('/api/events/<date>', methods=['GET'])
def get_events(date):
    date = datetime.strptime(date, '%Y-%m-%d').date()
    events = Event.query.filter_by(date=date).all()
    return jsonify([{
        'id': event.id,
        'title': event.title,
        'date': event.date,
    } for event in events])
            
@login_required
@main.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("home_page"))









