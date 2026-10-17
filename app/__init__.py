import os
from flask import Flask
from config import configs

def create_app(env_name="dev"):
    app = Flask(__name__)
    if env_name in configs:
        app.config.from_object(configs[env_name])
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

    from app.routes import bp
    app.register_blueprint(bp)

    return app