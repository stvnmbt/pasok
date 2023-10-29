from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///path/to/instance/db.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Import other necessary modules and register Blueprints
    from src.accounts.views import accounts_bp
    app.register_blueprint(accounts_bp)

    # Add other configurations and extensions as needed

    return app
