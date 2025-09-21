from flask import Flask
from waitress import serve
from extensions import db
from config import Config
from infrastructure.routes import bp as routes_bp
import os

def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    db.init_app(flask_app)
    flask_app.register_blueprint(routes_bp)

    with flask_app.app_context():
        db.create_all()  # чтобы таблицы создавались при старте

    return flask_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3531))
    serve(app, host="0.0.0.0", port=port)

