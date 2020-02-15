from flask import Flask, request

app = Flask(__name__)


@app.route("/keypress/<key>")
def keypress(key):
    pass


@app.route("/launch/<code>")
def launch(code):
    request.args.get("contentID", None)


@app.route("/query/apps")
def list_apps():
    pass


@app.route("/query/active-app")
def active_app():
    pass


@app.route("/query/icon/<app_id>")
def app_icon(app_id):
    pass


if __name__ == "__main__":
    app.run(port=8060, debug=True)
