import os

from flask import Flask, render_template, request
from api.model import LLM
from celery import Celery, Task
from celery.utils.log import get_task_logger
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


def celery_init_app(flask: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with flask.app_context():
                return self.run(*args, **kwargs)

    celery = Celery(flask.name, task_cls=FlaskTask)
    celery.config_from_object(flask.config["CELERY"])
    celery.set_default()
    flask.extensions["celery"] = celery
    return celery


app = Flask(__name__)
DEBUG = False
if os.environ.get("DEBUG", 0) == "1":
    DEBUG = True
app.debug = DEBUG
app.config.from_mapping(
    CELERY=dict(
        broker_url="redis://localhost",
        result_backend="redis://localhost",
        task_ignore_result=True,
        broker_connection_retry_on_startup=True,
    ) if DEBUG else dict(
        broker_url=os.environ["REDIS_URL"],
        result_backend=os.environ["REDIS_URL"],
        task_ignore_result=True,
        broker_connection_retry_on_startup=True,
    )
)
celery_app = celery_init_app(app)
llm = LLM()
logger = get_task_logger(__name__)
celery_worker = celery_app.Worker()


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/new")
def new():
    global llm
    llm.delete_index()
    llm = LLM()
    return "New conversation started.", 200


@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        if data is None or "message" not in data:
            return "Invalid JSON data or missing 'message' field.", 400
        message = data["message"]
        processed_message = str(llm.predict(message))
        if processed_message is None:
            return "Error processing the message.", 500
        return processed_message
    except Exception as e:
        return "An error occurred: {}".format(str(e)), 500


@celery_app.task
def create_index_task():
    try:
        logger.info("Creating index...")
        llm.create_index()
        logger.info("Index creation completed.")
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return "No file part in the request.", 400

        file = request.files['file']

        # If the user does not select a file, the browser submits an empty part without filename
        if file.filename == '':
            return "No selected file.", 400

        if file and allowed_file(file.filename):
            llm.upload_file(file)
            create_index_task.delay()
            return "File is uploading.", 200
        else:
            return "Invalid file format. Allowed formats: txt, pdf, doc, docx.", 400

    except Exception as e:
        return "An error occurred: {}".format(str(e)), 500


@app.route('/check-upload', methods=['GET'])
def check_upload():
    status = llm.upload_status
    return status, 200


if __name__ == '__main__':
    celery_worker_main = celery_worker.Main(
        app=celery_app,
        options={
            'broker': app.config['CELERY']['broker_url'],
            'loglevel': 'INFO',
            'traceback': True,
        }
    )
    celery_worker_main.run()
    app.run(debug=DEBUG)
