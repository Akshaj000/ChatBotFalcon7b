import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from falcon import LLM
from celery import Celery
from dotenv import find_dotenv, load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_login import login_user, logout_user, login_required, current_user
from flask_migrate import Migrate


load_dotenv(find_dotenv())

app = Flask(__name__)

# Configuration
DEBUG = os.environ.get("DEBUG", "0") == "1"
app.debug = DEBUG

app.config.update(
    CELERY_BROKER_URL=os.environ.get("KV_URL", "redis://localhost"),
    CELERY_RESULT_BACKEND=os.environ.get("KV_URL", "redis://localhost"),
    CELERY_TASK_IGNORE_RESULT=True,
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True,
    SQLALCHEMY_DATABASE_URI=os.environ.get("POSTGRES_URL", "sqlite:///db.sqlite"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.environ.get("SECRET_KEY", None)
)

# Initialize Celery
celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)

# Initialize LLM model
llm = LLM()

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Migrate
migrate = Migrate(app, db)


# Initialize LoginManager
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))


@app.route("/login", methods=["GET", "POST"])
def login():
    from models import User
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("home"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    from models import User
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# Routes
@app.route("/")
@login_required
def home():
    return render_template("index.html")


@app.route("/new")
@login_required
def new():
    global llm
    llm.delete_index()
    llm = LLM()
    return jsonify(message="New conversation started."), 200


@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    try:
        data = request.get_json()
        if data is None or "message" not in data:
            return jsonify(error="Invalid JSON data or missing 'message' field."), 400

        message = data["message"]
        processed_message = str(llm.predict(message))
        if processed_message is None:
            return jsonify(error="Error processing the message."), 500

        return jsonify(processed_message=processed_message)
    except Exception as e:
        return jsonify(error="An error occurred: {}".format(str(e))), 500


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@celery.task
def create_index_task():
    llm.create_index()


@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify(error="No file part in the request."), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify(error="No selected file."), 400

        if file and allowed_file(file.filename):
            llm.upload_file(file=file)
            create_index_task.delay()
            return jsonify(message="File upload task started."), 200
        else:
            return jsonify(error="Invalid file format. Allowed formats: txt, pdf, doc, docx."), 400

    except Exception as e:
        return jsonify(error="An error occurred: {}".format(str(e))), 500


@app.route('/check-upload', methods=['GET'])
@login_required
def check_upload():
    status = llm.upload_status
    return jsonify(upload_status=status), 200


if __name__ == '__main__':
    app.run(debug=DEBUG)
