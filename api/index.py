import flask
from flask import Flask, render_template, request
from flask_cors import CORS, cross_origin

from api.model import LLM


# web GUI
app = Flask(__name__)
cors = CORS(app, origins=['https://localhost', 'https://www.akshaj.in', 'https://www.akshaj.in/terminal', 'https://www.akshaj.in/assistant'])
llm = LLM()


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf'}
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
@cross_origin()
def send_message():
    try:
        data = request.get_json()
        if data is None or "message" not in data:
            return "Invalid JSON data or missing 'message' field.", 400
        message = data["message"]
        processed_message = str(llm.predict(message))
        if processed_message is None:
            return "Error processing the message.", 500
        response = flask.jsonify({"message": processed_message})
        return response, 200
    except Exception as e:
        return "An error occurred: {}".format(str(e)), 500


@app.route('/generate', methods=['POST'])
@cross_origin()
def generate():
    try:
        data = request.get_json()
        if data is None or "message" not in data:
            return "Invalid JSON data or missing 'message' field.", 400
        message = data["message"]
        processed_message = str(llm.generate(message))
        if processed_message is None:
            return "Error processing the message.", 500
        response = flask.jsonify({"message": processed_message})
        return response, 200
    except Exception as e:
        return "An error occurred: {}".format(str(e)), 500


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
            llm.create_index()
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
    app.run()
