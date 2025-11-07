from factory import create_app
import os
import sys

app = create_app()

if __name__ == "__main__":
    # Allow running via: python app.py run --no-debugger --no-reload
    # We ignore extra CLI args for compatibility with existing launch configs.
    debug = os.getenv("FLASK_ENV", "development") == "development"
    port = int(os.getenv("PORT", "5001"))
    app.run(debug=debug, port=port)
