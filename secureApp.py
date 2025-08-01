from flask import Flask, redirect, request, session, render_template_string
from flask_session import Session
import requests, os, uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# IBM App ID Configuration
CLIENT_ID = "139542fc-bad9-4f5a-9ab7-b2261416bd0a"
CLIENT_SECRET = "YzA1NWUyNDMtZDVmMi00N2JjLTk1ZDAtNTMxMWJhYTE4NGJi"
DISCOVERY_URL = "https://eu-gb.appid.cloud.ibm.com/oauth/v4/a93a2174-99b1-4c43-bbdb-3a1381e44515/.well-known/openid-configuration"
REDIRECT_URI = "http://localhost:5000/callback"

# Fetch OIDC endpoints
discovery = requests.get(DISCOVERY_URL).json()
auth_endpoint = discovery['authorization_endpoint']
token_endpoint = discovery['token_endpoint']
userinfo_endpoint = discovery['userinfo_endpoint']

@app.route('/')
def home():
    return render_template_string("""
        <h2>IBM App ID Authentication</h2>
        <a href="/login">Login with IBM App ID</a>
    """)

@app.route('/login')
def login():
    state = str(uuid.uuid4())
    session['state'] = state
    url = (
        f"{auth_endpoint}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope=openid%20email%20profile&state={state}"
    )
    return redirect(url)

@app.route('/callback')
def callback():
    if request.args.get('state') != session.get('state'):
        return "Invalid state", 400

    code = request.args.get('code')
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    token_response = requests.post(token_endpoint, data=token_data)
    tokens = token_response.json()
    access_token = tokens.get("access_token")

    if not access_token:
        return "Login failed", 401

    headers = {'Authorization': f'Bearer {access_token}'}
    user_info = requests.get(userinfo_endpoint, headers=headers).json()
    session['user'] = user_info

    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    user = session['user']
    return render_template_string(f"""
        <h2>Welcome, {user.get('name')}</h2>
        <p>Email: {user.get('email')}</p>
        <a href="/logout">Logout</a>
    """)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)