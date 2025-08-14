import os
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from src.routes import register_routes
from src.db import init_db

load_dotenv()

def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY", "dev")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Only initialize DB if not in serverless environment
    if not os.getenv("VERCEL"):
        try:
            init_db()
        except Exception as e:
            print(f"Database initialization failed: {e}")
            # Continue without DB initialization in serverless

    # Register routes
    register_routes(app)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    # Serve frontend static files
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(f"../frontend/dist/{path}"):
            return send_from_directory('../frontend/dist', path)
        else:
            return send_from_directory('../frontend/dist', 'index.html')

    return app

# Create the Flask app instance for Vercel
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True) 