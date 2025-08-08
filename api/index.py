# Vercel serverless function entry point
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app_v3 import app

# Export the Flask app for Vercel
def handler(request):
    return app(request.environ, lambda x: None)

# For direct import
application = app

if __name__ == "__main__":
    app.run()