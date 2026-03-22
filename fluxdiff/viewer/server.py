from flask import Flask, send_from_directory, render_template_string
import os
import webbrowser
import threading

app = Flask(__name__)

OUTPUT_DIR = os.path.abspath("output")
IMAGE_FILENAMES = [
    "before.png",
    "after.png",
    "diff_overlay.png",
]

@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PCB Diff Viewer</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 900px; margin: auto; }
            h1 { text-align: center; }
            .img-container { display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }
            .img-block { text-align: center; }
            img { max-width: 400px; max-height: 400px; margin-bottom: 8px; border: 1px solid #ccc; }
        </style>
    </head>
    <body>
        <h1>PCB Diff Viewer</h1>
        <div class="img-container">
        {% for filename in image_filenames %}
            <div class="img-block">
                <h3>{{ filename }}</h3>
                <img src="/images/{{ filename }}" alt="{{ filename }}">
            </div>
        {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, image_filenames=IMAGE_FILENAMES)

@app.route("/images/<path:filename>")
def images(filename):
    return send_from_directory(OUTPUT_DIR, filename)


# ⭐ ADD THIS FUNCTION
def run_viewer_server():

    # auto-open browser
    threading.Timer(
        1,
        lambda: webbrowser.open("http://localhost:5000")
    ).start()

    app.run(host="localhost", port=5000)


if __name__ == "__main__":
    run_viewer_server()