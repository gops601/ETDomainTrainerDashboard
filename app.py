import os
import pymysql
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, OU, TrainingType, TrainingEntry
from functools import wraps
from datetime import datetime

# Initialize extensions
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

def create_database_if_not_exists(config):
    # Connect without specifying database to create it if needed
    try:
        if config.MYSQL_PASSWORD:
            conn = pymysql.connect(host=config.MYSQL_HOST, user=config.MYSQL_USER, password=config.MYSQL_PASSWORD)
        else:
            conn = pymysql.connect(host=config.MYSQL_HOST, user=config.MYSQL_USER)
        
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.MYSQL_DB}")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

def create_app():
    # Setup configuration
    config = Config()
    
    # Try to create database if it doesn't exist
    create_database_if_not_exists(config)
    
    app = Flask(__name__)
    app.config.from_object(config)
    
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    # Register routes
    register_routes(app)
    
    # Initialize DB schema
    with app.app_context():
        db.create_all()
        create_default_admin()
        
    return app

def create_default_admin():
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(name='System Admin', email='admin@example.com', password=hashed_password, role='admin', must_change_password=False)
        db.session.add(admin)
        db.session.commit()
        print("Default admin created (admin@example.com / admin123)")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def register_routes(app):
    
    @app.before_request
    def check_password_change():
        if current_user.is_authenticated:
            if current_user.must_change_password and request.endpoint not in ['change_password', 'logout', 'static']:
                flash('Please change your default password before continuing.', 'warning')
                return redirect(url_for('change_password'))
                
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('trainer_dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user)
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Login Unsuccessful. Please check email and password.', 'danger')
                
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))
        
    @app.route('/change_password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        if request.method == 'POST':
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password != confirm_password:
                flash('Passwords do not match.', 'danger')
            else:
                current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                current_user.must_change_password = False
                db.session.commit()
                flash('Password updated successfully.', 'success')
                return redirect(url_for('index'))
                
        return render_template('change_password.html')

    # ==========================
    # ADMIN ROUTES
    # ==========================
    @app.route('/admin/dashboard')
    @login_required
    @admin_required
    def admin_dashboard():
        week_from = request.args.get('week_from')
        week_to = request.args.get('week_to')
        trainer_id = request.args.get('trainer_id')
        ou_id = request.args.get('ou_id')
        type_id = request.args.get('type_id')
        
        query = TrainingEntry.query
        
        if week_from:
            query = query.filter(TrainingEntry.from_date >= week_from)
        if week_to:
            query = query.filter(TrainingEntry.to_date <= week_to)
        if trainer_id:
            query = query.filter(TrainingEntry.trainer_id == trainer_id)
        if ou_id:
            query = query.filter(TrainingEntry.ou_id == ou_id)
        if type_id:
            query = query.filter(TrainingEntry.training_type_id == type_id)
            
        entries = query.order_by(TrainingEntry.created_at.desc()).all()
        
        # Calculate KPIs
        total_training_hrs = sum(e.duration for e in entries if e.is_training)
        total_non_training_hrs = sum(e.duration for e in entries if not e.is_training)
        total_participants = sum((e.participants_count or 0) for e in entries if e.is_training)
        total_entries = len(entries)
        
        kpis = {
            'total_training_hrs': total_training_hrs,
            'total_non_training_hrs': total_non_training_hrs,
            'total_participants': total_participants,
            'total_entries': total_entries
        }
        
        trainers = User.query.filter_by(role='trainer').all()
        ous = OU.query.all()
        training_types = TrainingType.query.all()
        
        return render_template('admin/dashboard.html', entries=entries, trainers=trainers, ous=ous, training_types=training_types, kpis=kpis)

    @app.route('/admin/trainers', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def manage_trainers():
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            role = request.form.get('role', 'trainer')
            
            existing = User.query.filter_by(email=email).first()
            if existing:
                flash('Email already registered.', 'danger')
            else:
                hashed = bcrypt.generate_password_hash('Trainer@ict').decode('utf-8')
                new_user = User(name=name, email=email, password=hashed, role=role, must_change_password=True)
                db.session.add(new_user)
                db.session.commit()
                flash('Trainer added successfully with default password Trainer@ict.', 'success')
            return redirect(url_for('manage_trainers'))
            
        trainers = User.query.all()
        return render_template('admin/manage_trainers.html', trainers=trainers)
        
    @app.route('/admin/trainers/delete/<int:id>')
    @login_required
    @admin_required
    def delete_trainer(id):
        user = User.query.get_or_404(id)
        if user.id == current_user.id:
            flash('You cannot delete yourself!', 'danger')
        else:
            db.session.delete(user)
            db.session.commit()
            flash('User deleted.', 'success')
        return redirect(url_for('manage_trainers'))
        
    @app.route('/admin/trainers/reset_password/<int:id>')
    @login_required
    @admin_required
    def reset_password(id):
        user = User.query.get_or_404(id)
        user.password = bcrypt.generate_password_hash('Trainer@ict').decode('utf-8')
        user.must_change_password = True
        db.session.commit()
        flash(f"Password for {user.name} has been reset to Trainer@ict.", 'success')
        return redirect(url_for('manage_trainers'))

    @app.route('/admin/ous', methods=['GET', 'POST'])
    @login_required
    def manage_ous():
        if request.method == 'POST':
            if current_user.role != 'admin':
                flash('Only admins can add Organizational Units.', 'danger')
                return redirect(url_for('manage_ous'))
            name = request.form.get('name')
            existing = OU.query.filter_by(name=name).first()
            if existing:
                flash('OU already exists.', 'danger')
            else:
                new_ou = OU(name=name)
                db.session.add(new_ou)
                db.session.commit()
                flash('OU added successfully.', 'success')
            return redirect(url_for('manage_ous'))
            
        ous = OU.query.all()
        return render_template('admin/manage_ous.html', ous=ous)

    @app.route('/admin/ous/delete/<int:id>')
    @login_required
    @admin_required
    def delete_ou(id):
        ou = OU.query.get_or_404(id)
        db.session.delete(ou)
        db.session.commit()
        flash('OU deleted.', 'success')
        return redirect(url_for('manage_ous'))

    @app.route('/admin/training_types', methods=['GET', 'POST'])
    @login_required
    def manage_training_types():
        if request.method == 'POST':
            if current_user.role != 'admin':
                flash('Only admins can add Training Types.', 'danger')
                return redirect(url_for('manage_training_types'))
            name = request.form.get('name')
            ou_id = request.form.get('ou_id')
            
            new_type = TrainingType(name=name, ou_id=ou_id)
            db.session.add(new_type)
            db.session.commit()
            flash('Training Type added successfully.', 'success')
            return redirect(url_for('manage_training_types'))
            
        types = TrainingType.query.all()
        ous = OU.query.all()
        return render_template('admin/manage_training_types.html', types=types, ous=ous)

    @app.route('/admin/training_types/delete/<int:id>')
    @login_required
    @admin_required
    def delete_training_type(id):
        t_type = TrainingType.query.get_or_404(id)
        db.session.delete(t_type)
        db.session.commit()
        flash('Training Type deleted.', 'success')
        return redirect(url_for('manage_training_types'))

    @app.route('/admin/entry/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_entry(id):
        entry = TrainingEntry.query.get_or_404(id)
        if request.method == 'POST':
            entry.from_date = datetime.strptime(request.form.get('from_date'), '%Y-%m-%d').date()
            entry.to_date = datetime.strptime(request.form.get('to_date'), '%Y-%m-%d').date()
            
            is_training_str = request.form.get('is_training')
            entry.is_training = is_training_str == 'true'
            
            if entry.is_training:
                entry.ou_id = int(request.form.get('ou_id')) if request.form.get('ou_id') else None
                entry.training_type_id = int(request.form.get('type_id')) if request.form.get('type_id') else None
                entry.participants_count = int(request.form.get('participants')) if request.form.get('participants') else None
                entry.mode = request.form.get('mode')
            else:
                entry.ou_id = None
                entry.training_type_id = None
                entry.participants_count = None
                entry.mode = None
                
            entry.title = request.form.get('title')
            entry.duration = float(request.form.get('duration', 0.0))
            entry.remarks = request.form.get('remarks', '')
            
            db.session.commit()
            flash('Entry updated successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
            
        ous = OU.query.all()
        types = TrainingType.query.all()
        return render_template('admin/edit_entry.html', entry=entry, ous=ous, types=types)

    # ==========================
    # TRAINER ROUTES
    # ==========================
    @app.route('/trainer/dashboard')
    @login_required
    def trainer_dashboard():
        if current_user.role != 'trainer' and current_user.role != 'admin':
            return redirect(url_for('index'))
            
        entries = TrainingEntry.query.filter_by(trainer_id=current_user.id).order_by(TrainingEntry.created_at.desc()).all()
        
        # Calculate KPIs
        total_training_hrs = sum(e.duration for e in entries if e.is_training)
        total_non_training_hrs = sum(e.duration for e in entries if not e.is_training)
        total_participants = sum((e.participants_count or 0) for e in entries if e.is_training)
        total_entries = len(entries)
        
        kpis = {
            'total_training_hrs': total_training_hrs,
            'total_non_training_hrs': total_non_training_hrs,
            'total_participants': total_participants,
            'total_entries': total_entries
        }
        
        return render_template('trainer/dashboard.html', entries=entries, kpis=kpis)

    @app.route('/trainer/entry', methods=['GET', 'POST'])
    @login_required
    def trainer_entry():
        if request.method == 'POST':
            from_date_str = request.form.get('from_date')
            to_date_str = request.form.get('to_date')
            
            # Form arrays
            is_training = request.form.getlist('is_training[]')
            ou_ids = request.form.getlist('ou_id[]')
            type_ids = request.form.getlist('type_id[]')
            titles = request.form.getlist('title[]')
            participants = request.form.getlist('participants[]')
            durations = request.form.getlist('duration[]')
            modes = request.form.getlist('mode[]')
            remarks = request.form.getlist('remarks[]')
            
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
                
                # Check lengths (base on titles since it's always present)
                n = len(titles)
                    
                for i in range(n):
                    if not titles[i]:
                        continue # Skip empty rows
                        
                    is_train = is_training[i] == 'true' if i < len(is_training) else True
                    
                    entry = TrainingEntry(
                        trainer_id=current_user.id,
                        from_date=from_date,
                        to_date=to_date,
                        is_training=is_train,
                        ou_id=int(ou_ids[i]) if is_train and ou_ids[i] else None,
                        training_type_id=int(type_ids[i]) if is_train and type_ids[i] else None,
                        title=titles[i],
                        participants_count=int(participants[i]) if is_train and participants[i] else None,
                        duration=float(durations[i]) if i < len(durations) and durations[i] else 0.0,
                        mode=modes[i] if is_train and i < len(modes) else None,
                        remarks=remarks[i] if i < len(remarks) else ""
                    )
                    db.session.add(entry)
                
                db.session.commit()
                flash('Training entries submitted successfully!', 'success')
                return redirect(url_for('trainer_dashboard'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred: {str(e)}', 'danger')
                
        ous = OU.query.all()
        training_types = TrainingType.query.all()
        return render_template('trainer/entry_form.html', ous=ous, training_types=training_types)

    @app.route('/trainer/entry/delete/<int:id>')
    @login_required
    def delete_entry(id):
        entry = TrainingEntry.query.get_or_404(id)
        if entry.trainer_id != current_user.id:
            flash('Permission denied.', 'danger')
        else:
            db.session.delete(entry)
            db.session.commit()
            flash('Entry deleted successfully.', 'success')
        return redirect(url_for('trainer_dashboard'))

    # ==========================
    # API ROUTES
    # ==========================
    @app.route('/api/training_types/<int:ou_id>')
    @login_required
    def api_training_types(ou_id):
        types = TrainingType.query.filter_by(ou_id=ou_id).all()
        return jsonify([{'id': t.id, 'name': t.name} for t in types])

if __name__ == '__main__':
    app = create_app()
    app.run(port=5001,debug=True)
