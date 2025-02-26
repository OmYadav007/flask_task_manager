import os
import datetime
import logging

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, set_access_cookies, unset_jwt_cookies
)
import secrets

app = Flask(__name__)

if not os.environ.get('SECRET_KEY'):
    os.environ['SECRET_KEY'] = secrets.token_hex(32)  

if not os.environ.get('JWT_SECRET_KEY'):
    os.environ['JWT_SECRET_KEY'] = secrets.token_hex(32) 

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_manager.db'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1)
app.config['JWT_COOKIE_CSRF_PROTECT'] = False

db = SQLAlchemy(app)
jwt = JWTManager(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class User(db.Model):
    """This model stores the details of the user and password in hashed format"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)  


class Task(db.Model):
    """This model stores task details with title description ,user id and completed or not completed status."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)

@app.before_request
def create_tables():
    
    db.create_all()

@app.route('/')
def index():

    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """ This function handles the user registration process and if a username already exists it gives an error and if a new user signs up it adds it into the db"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            logger.warning("Registration attempt with existing username: %s", username)
            return render_template('register.html', error="Username already exists")
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        logger.info("New user registered: %s", username)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """this function handles login and then sets JWT tokens in cookies on successful auth"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        logger.debug("Login attempt for user: %s", username)
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            access_token = create_access_token(identity=str(user.id))
            response = redirect(url_for('tasks'))
            set_access_cookies(response, access_token)
            logger.info("User %s logged in successfully", username)
            return response
        else:
            logger.warning("Failed login attempt for user: %s", username)
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    """ This function logs out user and unsets the jwt token"""
    response = redirect(url_for('login'))
    unset_jwt_cookies(response)
    logger.info("User logged out")
    return response

@app.route('/tasks')
@jwt_required()
def tasks():
    """This function retrives all the task from db for the current user and displays them"""
    current_user = get_jwt_identity()
    tasks = Task.query.filter_by(user_id=current_user).all()
    return render_template('tasks.html', tasks=tasks)


@app.route('/add_task', methods=['POST'])
@jwt_required()
def add_task():
    """This function allows the user to add a new task."""
    title = request.form.get('title')
    description = request.form.get('description')
    current_user = get_jwt_identity()
    new_task = Task(title=title, description=description, user_id=current_user)
    db.session.add(new_task)
    db.session.commit()
    logger.info("Task added for user id: %s", current_user)
    return redirect(url_for('tasks'))


@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@jwt_required()
def edit_task(task_id):
    """This function helps user to edit the task title and description and also the task completed or not status"""
    current_user = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=current_user).first_or_404()
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        
        task.completed = True if request.form.get('completed') == 'on' else False

        db.session.commit()
        return redirect(url_for('tasks'))
    return render_template('edit_task.html', task=task)

@app.route('/delete_task/<int:task_id>', methods=['POST'])
@jwt_required()
def delete_task(task_id):
    """This function helps the user to delete a task. ."""
    current_user = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=current_user).first_or_404()
    db.session.delete(task)
    db.session.commit()
    logger.info("Task %s deleted for user id: %s", task_id, current_user)
    return redirect(url_for('tasks'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port="8002")
