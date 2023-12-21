import os
import threading

from .database import db
from flask import Flask, request, jsonify
from flask_cors import CORS
from .utils.extract_person import extract_person
from .utils.analyze_person import analyze_person
from .extensions.extensions import Migrate, JWTManager


def pulsse_app(config_file=os.path.join(os.path.dirname(__file__), "..", "config.py")):
    app = Flask(__name__)
    app.config.from_pyfile(config_file)
    cors = CORS(origins='*')
    cors.init_app(app)
    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)

    @app.before_request
    def basic_authentication():
        headers = { 'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type' }
        if request.method == 'OPTIONS' or request.method == 'options':
            return jsonify(headers), 200

    from Pulsse.views.user_view import user_blueprint
    app.register_blueprint(user_blueprint)

    from Pulsse.views.customer_view import customer_blueprint
    app.register_blueprint(customer_blueprint)

    from Pulsse.views.visit_view import visit_blueprint
    app.register_blueprint(visit_blueprint)

    from Pulsse.views.generate_frames_view import frames_blueprint
    app.register_blueprint(frames_blueprint)

    from Pulsse.views.dashboard import dashboard_blueprint
    app.register_blueprint(dashboard_blueprint)

    thread1 = threading.Thread(target=extract_person, args=(1, app))
    thread1.daemon = True
    thread1.start()
    # thread2 = threading.Thread(target=extract_person, args=(2, app))
    # thread2.daemon = True
    # thread2.start()
    # thread3 = threading.Thread(target=extract_person, args=(3, app))
    # thread3.daemon = True
    # thread3.start()

    # thread2.join()
    # thread3.join()

    analyze_thread = threading.Thread(target=analyze_person, args=(1))
    analyze_thread.daemon = True
    analyze_thread.start()

    thread1.join()
    analyze_thread.join()

    return app


