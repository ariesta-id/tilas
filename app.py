# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "flask",
#     "flask-login",
#     "flask-sqlalchemy",
#     "oauthlib",
#     "requests",
# ]
# [tool.uv]
# exclude-newer = "2025-01-02T14:15:09Z"
# ///
from flask import Flask, render_template, request, redirect, url_for, json
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from models import db, Note, User
from oauthlib.oauth2 import WebApplicationClient
import requests
import os


class ProxiedRequest(requests.Request):
    # https://stackoverflow.com/questions/19840051/mutating-request-base-url-in-flask
    def __init__(self, environ, populate_request=True, shallow=False):
        super(requests.Request, self).__init__(environ, populate_request, shallow)
        # Support SSL termination. Mutate the host_url within Flask to use https://
        # if the SSL was terminated.
        x_forwarded_proto = self.headers.get("X-Forwarded-Proto")
        if x_forwarded_proto == "https":
            self.url = self.url.replace("http://", "https://")
            self.host_url = self.host_url.replace("http://", "https://")
            self.base_url = self.base_url.replace("http://", "https://")
            self.url_root = self.url_root.replace("http://", "https://")


app = Flask(__name__)
app.request_class = ProxiedRequest
db_path = os.path.expanduser(os.getenv("DATABASE_PATH", "~/tilas-instance/tilas.db"))
print(f"Database location: {db_path}")
os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(24)
db.init_app(app)

# Google Login code from https://realpython.com/flask-google-login/

# User session management setup
login_manager = LoginManager()
login_manager.init_app(app)

# OAuth 2 client setup
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
client = WebApplicationClient(GOOGLE_CLIENT_ID)

ALLOWED_EMAILS = os.getenv("ALLOWED_EMAILS", "").split(",")


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        note = Note(note_content=request.form["note"], user_id=current_user.id)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for("index"))
    notes = Note.query.filter_by(user_id=current_user.id).all()
    return render_template("index.html", notes=notes)


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]

        # Check if the email is in the whitelist
        if users_email not in ALLOWED_EMAILS:
            return "You are not authorized to use this app.", 401

    # Create a user in your db with the information provided
    # by Google
    user = User(id=unique_id, name=users_name, email=users_email, profile_pic=picture)

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # https://stackoverflow.com/questions/69561231/getting-insecure-transport-oauth-2-must-utilize-https-with-cert-managed-by-her
    app.run(debug=True, host="0.0.0.0")
