from flask import Flask, send_from_directory, render_template_string, jsonify
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

# 🔥 GLOBAL DATA STORAGE
diff_result_global = None
bom_global = None
supply_global = None


# ---------- API ----------
@app.route("/api/diff")
def get_diff():
    if diff_result_global is None:
        return jsonify({"error": "No diff available"})

    return jsonify({
        "components": diff_result_global.component_changes,
        "nets": diff_result_global.net_changes,
        "routing": diff_result_global.routing_changes
    })


@app.route("/api/bom")
def get_bom():
    if bom_global is None:
        return jsonify([])
    return jsonify(bom_global)


@app.route("/api/supply")
def get_supply():
    return jsonify(supply_global or [])


# ---------- UI ----------
@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FluxDiff Viewer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                background: #f4f6f8;
            }

            .container {
                display: flex;
                height: 100vh;
            }

            /* LEFT SIDE */
            .images {
                width: 60%;
                padding: 20px;
                overflow-y: scroll;
                background: #f9f9f9;
            }

            .img-block {
                margin-bottom: 20px;
                text-align: center;
            }

            img {
                max-width: 100%;
                border: 1px solid #ccc;
                border-radius: 6px;
            }

            /* RIGHT PANEL */
            .panel {
                width: 40%;
                padding: 20px;
                border-left: 2px solid #ddd;
                overflow-y: scroll;
                background: white;
            }

            h2 {
                margin-top: 0;
            }

            /* SUMMARY */
            .summary {
                display: flex;
                justify-content: space-around;
                background: #eef1f4;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 20px;
                font-weight: bold;
            }

            /* SECTION */
            .section {
                margin-bottom: 25px;
            }

            .section h3 {
                cursor: pointer;
                margin-bottom: 10px;
            }

            /* CARD */
            .card {
                background: #f8f9fa;
                padding: 12px;
                border-radius: 10px;
                margin-bottom: 10px;
                transition: 0.2s;
                font-size: 14px;
            }

            .card:hover {
                background: #e9ecef;
            }

            /* COLORS */
            .critical { color: red; font-weight: bold; }
            .warning { color: orange; }
            .info { color: green; }
            .component { color: #007bff; }

        </style>
    </head>

    <body>

    <div class="container">

        <!-- LEFT -->
        <div class="images">
            {% for filename in image_filenames %}
                <div class="img-block">
                    <h3>{{ filename }}</h3>
                    <img src="/images/{{ filename }}">
                </div>
            {% endfor %}
        </div>

        <!-- RIGHT -->
        <div class="panel">

            <h2>🔍 PCB Changes</h2>

            <!-- SUMMARY -->
            <div class="summary">
                <div>🔧 <span id="compCount">0</span></div>
                <div>⚡ <span id="netCount">0</span></div>
                <div>🛣 <span id="routeCount">0</span></div>
            </div>

            <div class="section">
                <h3 onclick="toggle('components')">🔧 Components</h3>
                <div id="components"></div>
            </div>

            <div class="section">
                <h3 onclick="toggle('nets')">⚡ Nets</h3>
                <div id="nets"></div>
            </div>

            <div class="section">
                <h3 onclick="toggle('routing')">🛣 Routing</h3>
                <div id="routing"></div>
            </div>

            <div class="section">
                <h3 onclick="toggle('bom')">📦 BOM</h3>
                <div id="bom"></div>
            </div>

            <div class="section">
                <h3 onclick="toggle('supply')">🚛 Supply Chain</h3>
                <div id="supply"></div>
            </div>

        </div>

    </div>

    <script>

    function toggle(id) {
        const el = document.getElementById(id);
        el.style.display = (el.style.display === "none") ? "block" : "none";
    }

    function getClass(text) {
        if (text.includes("CRITICAL")) return "critical";
        if (text.includes("WARNING")) return "warning";
        if (text.includes("INFO")) return "info";
        return "component";
    }

    function formatText(text) {
        if (text.includes("Component value changed"))
            return "🔧 " + text.replace("Component value changed:", "");

        if (text.includes("Component moved"))
            return "📍 " + text.replace("Component moved:", "");

        if (text.includes("Trace added"))
            return "➕ " + text.replace("Trace added:", "");

        if (text.includes("WARNING"))
            return "🟡 " + text;

        if (text.includes("CRITICAL"))
            return "🔴 " + text;

        return text;
    }

    function render(list, id) {
        const container = document.getElementById(id);

        if (!list || list.length === 0) {
            container.innerHTML = "<div class='card'>No changes</div>";
            return;
        }

        list.forEach(item => {
            const div = document.createElement("div");
            div.className = "card " + getClass(item);
            div.innerText = formatText(item);
            container.appendChild(div);
        });
    }

    fetch("/api/diff")
        .then(res => res.json())
        .then(data => {

            document.getElementById("compCount").innerText = data.components.length;
            document.getElementById("netCount").innerText = data.nets.length;
            document.getElementById("routeCount").innerText = data.routing.length;

            render(data.components, "components");
            render(data.nets, "nets");
            render(data.routing, "routing");

        })
        .catch(err => console.error(err));

    fetch("/api/bom")
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById("bom");

            if (!data || data.length === 0) {
                container.innerHTML = "<div class='card'>No BOM data</div>";
                return;
            }

            data.forEach(item => {
                const div = document.createElement("div");
                div.className = "card";

                div.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <b>${item.display_name}</b>
                        <span style="background:#eee;padding:2px 6px;border-radius:6px;font-size:12px;">${item.type}</span>
                    </div>
                    <i>${item.footprint}</i><br>
                    <b>Count:</b> ${item.count}<br>
                    <b>Refs:</b> ${item.refs}
                `;

                container.appendChild(div);
            });
        })
        .catch(err => console.error(err));

    const container_supply = document.getElementById("supply");
    container_supply.innerHTML = "<div class='card'>🔄 Syncing with ERP...</div>";

    fetch("/api/supply")
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById("supply");

            if (!data || data.length === 0) {
                container.innerHTML = "<div class='card'>No supply data</div>";
                return;
            }

            data.forEach(item => {
                const div = document.createElement("div");

                let color = "green";
                if (item.status === "CRITICAL") color = "red";
                else if (item.status === "WARNING") color = "orange";

                div.className = "card";
                div.innerHTML = `
                    <b>${item.name}</b><br>
                    Required: ${item.required}<br>
                    Stock: ${item.stock}<br>
                    <span style="color:${color};font-weight:bold;">
                        ${item.status}
                    </span>
                `;

                container.appendChild(div);
            });
        })
        .catch(err => console.error(err));

    </script>

    </body>
    </html>
    """
    return render_template_string(html, image_filenames=IMAGE_FILENAMES)


# ---------- IMAGE ROUTE ----------
@app.route("/images/<path:filename>")
def images(filename):
    return send_from_directory(OUTPUT_DIR, filename)


# ---------- SERVER ----------
def run_viewer_server(diff_result=None, bom=None, supply=None):

    global diff_result_global, bom_global, supply_global
    diff_result_global = diff_result
    bom_global = bom
    supply_global = supply

    threading.Timer(
        1,
        lambda: webbrowser.open("http://localhost:5000")
    ).start()

    app.run(host="localhost", port=5000)


if __name__ == "__main__":
    run_viewer_server()