from flask import Flask, request, make_response, session
import json
import secrets

app = Flask(__name__)

# Add secret key for session
app.secret_key = secrets.token_hex(16)

# Simulate a database
user_accounts = {
    'alice': {'balance': 10000, 'password': 'alice'},
    'attacker': {'balance': 0, 'password': '12345'},
    'bob': {'balance': 10000, 'password': 'bob'},
}


@app.route('/')
def home():
    return "Welcome to the Bank"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in user_accounts and user_accounts[username]['password'] == password:
            resp = make_response(f"Logged in as {username}")
            resp.set_cookie('user_session', json.dumps({'username': username}))
            # Generate session token
            session['csrf_token'] = secrets.token_hex(16)
            return resp
        else:
            return "Invalid credentials", 401
    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Log In">
        </form>
    '''


@app.route('/logout')
def logout():
    resp = make_response("Logged out")
    resp.set_cookie('user_session', '', expires=0)
    return resp


@app.route('/balance')
def balance():
    session_data = get_session_data()
    if not session_data:
        return "Please log in first", 401
    username = session_data['username']
    balance = user_accounts[username]['balance']
    return f"Your balance is ${balance}"


@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    session_data = get_session_data()
    if not session_data:
        return "Please log in first", 401

    if request.method == 'POST':
        from_account = session_data['username']
        to_account = request.form['to']
        amount = int(request.form['amount'])

        # Check CSRF token
        if request.form.get('csrf_token') != session.get('csrf_token'):
            return 'Invalid CSRF token', 403

        if to_account not in user_accounts:
            return "Recipient account does not exist", 400
        if amount <= 0:
            return "Invalid amount", 400
        if user_accounts[from_account]['balance'] < amount:
            return "Insufficient funds", 400

        # Perform transfer
        user_accounts[from_account]['balance'] -= amount
        user_accounts[to_account]['balance'] += amount

        return f"Transferred ${amount} to account {to_account}"

    # GET request: show transfer form
    return '''
        <form method="post">
            To account: <input type="text" name="to"><br>
            Amount: <input type="number" name="amount"><br>
            <input type="submit" value="Transfer">
        </form>
    '''


def get_session_data():
    session_cookie = request.cookies.get('user_session')
    if session_cookie:
        return json.loads(session_cookie)
    return None


if __name__ == '__main__':
    app.run(debug=True)
