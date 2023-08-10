from flask import jsonify, request, Blueprint, render_template
from flask_login import login_required, current_user
from falcon import LLM

llm_bp = Blueprint("llm", __name__)


@llm_bp.route('/sessions')
@login_required
def sessions():
    from models import Session
    ssns = Session.query.filter_by(user_id=current_user.id).all()
    return render_template("sessions.html", sessions=ssns)


@llm_bp.route('/create-session', methods=['POST'])
@login_required
def create_session():
    from models import Session
    from app import db
    session = Session(user_id=current_user.id, name="New Session", data={})
    db.session.add(session)
    db.session.commit()
    data = {
        "session_id": session.id,
        "name": session.name,
        "data": session.data
    }
    return jsonify(data), 200


@llm_bp.route('/get-sessions', methods=['GET'])
@login_required
def get_sessions():
    from models import Session
    sessions = Session.query.filter_by(user_id=current_user.id).all()
    data = [{
        "session_id": session.id,
        "name": session.name,
        "data": session.data
    } for session in sessions]
    return jsonify(data), 200


@llm_bp.route('/get-session/<int:session_id>', methods=['GET'])
@login_required
def get_session(session_id):
    from models import Session
    if session_id is None:
        return jsonify(error="Invalid session ID."), 400
    sessions = Session.query.filter_by(id=session_id)
    if not sessions.count():
        return jsonify(error="Session not found."), 404
    session = sessions.first()
    if session is None:
        return jsonify(error="Session not found."), 404
    data = {
        "session_id": session.id,
        "name": session.name,
        "data": session.data
    }
    return jsonify(data), 200


@llm_bp.route('/update-session', methods=['POST'])
@login_required
def update_session():
    from models import Session
    from app import db
    data = request.get_json()
    if data is None or "session_id" not in data:
        return jsonify(error="Invalid JSON data or missing 'session_id' field."), 400
    session_id = data["session_id"]
    sessions = Session.query.filter_by(id=session_id)
    if not sessions.count():
        return jsonify(error="Session not found."), 404
    session = sessions.first()
    if "name" in data:
        session.name = data["name"]
    db.session.commit()
    data = {
        "session_id": session.id,
        "name": session.name,
        "data": session.data
    }
    return jsonify(data), 200


@llm_bp.route('/delete-session', methods=['POST'])
@login_required
def delete_session():
    from models import Session
    from app import db
    data = request.get_json()
    if data is None or "session_id" not in data:
        return jsonify(error="Invalid JSON data or missing 'session_id' field."), 400
    session_id = data["session_id"]
    sessions = Session.query.filter_by(id=session_id)
    if not sessions.count():
        return jsonify(error="Session not found."), 404
    session = sessions.first()
    db.session.delete(session)
    db.session.commit()
    return jsonify(), 200


@llm_bp.route('/send-message', methods=['POST'])
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


@llm_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify(error="No file part in the request."), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify(error="No selected file."), 400

        if file and allowed_file(file.filename):
            from tasks import create_index_task
            from app import llm
            llm.upload_file(file=file)
            create_index_task.delay()
            return jsonify(message="File upload task started."), 200
        else:
            return jsonify(error="Invalid file format. Allowed formats: txt, pdf, doc, docx."), 400

    except Exception as e:
        return jsonify(error="An error occurred: {}".format(str(e))), 500


@llm_bp.route('/check-upload', methods=['GET'])
@login_required
def check_upload():
    status = llm.upload_status
    return jsonify(upload_status=status), 200


@llm_bp.route("/new")
@login_required
def new():
    llm = LLM()
    return jsonify(message="New conversation started."), 200


__all__ = [
    "llm_bp"
]
