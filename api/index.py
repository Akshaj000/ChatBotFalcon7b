import os
from flask import Flask, render_template, request
from model import LLM

# web GUI
app = Flask(__name__)
llm = LLM()

# Folder to store uploaded documents
UPLOAD_FOLDER = 'api/static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def delete_old_document():
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.startswith('uploaded_document.'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.remove(file_path)
    return "Old documents deleted.", 200


def any_file_uploaded():
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.startswith('uploaded_document.'):
            return True
    return False


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/new")
def new():
    global llm
    llm.delete_index()
    llm = LLM()
    delete_old_document()
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
            filename = "uploaded_document." + file.filename.rsplit('.', 1)[1].lower()
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            llm.load_document()
            return "File uploaded successfully.", 200
        else:
            return "Invalid file format. Allowed formats: txt, pdf, doc, docx.", 400

    except Exception as e:
        return "An error occurred: {}".format(str(e)), 500


if __name__ == '__main__':
    app.run(debug=True)
