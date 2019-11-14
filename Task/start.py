import re
import json
from datetime import datetime
from re import *

# global variables for some operations
# attempts is count of trying to log in with current account
attempts = 0
delta_time = 0
time1 = datetime.now()
login_out = ''
time_out = time1

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# connect to database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3306/test_task'
db = SQLAlchemy(app)


# initialization DB
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(32), unique=True, nullable=False)
    pwd = db.Column(db.String(17), nullable=False)
    email = db.Column(db.String(32), unique=True, nullable=False)
    phone = db.Column(db.String(32), unique=True, nullable=False)
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32), nullable=False)

    def __init__(self, login, pwd, email, phone, f_name, l_name):
        self.login = login
        self.pwd = pwd
        self.email = email
        self.phone = phone
        self.first_name = f_name
        self.last_name = l_name


# this command using to create table in db
# db.create_all()


@app.route('/')
def start():
    return render_template('index.html')


@app.route('/registration', methods=['GET'])
def reg():
    return render_template('registration.html')


@app.route('/authorisation', methods=['GET'])
def aut():
    return render_template('authorisation.html')


# checking validation of password following example
def passwd_is_valid(passwd):
    validation = 0
    if type(passwd) is str:
        # checking length of password
        if 10 <= len(passwd) <= 16:
            upper = 0
            lower = 0
            # checking upper and lower symbols in password
            for letter in passwd:
                if letter.isupper():
                    upper = 1
                if letter.islower():
                    lower = 1
            # checking special symbols in password
            if upper and lower:
                spec_check = re.search(r'[&!$#*]', passwd)
                if spec_check:
                    validation = 1
    if validation:
        return 1
    else:
        return 0


# checking of login unique
def login_is_unique(login):
    # checking uniqueness of login by using mysql connector
    import mysql.connector

    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="1234",
        database="test_task"
    )

    mycursor = mydb.cursor()
    mycursor.execute("SELECT login FROM user")

    myresult = mycursor.fetchall()

    for i in range(len(myresult)):
        log = myresult[i]

        if login != log[0]:
            return 1
    return 0


# checking validation of password
def email_is_walid(email):
    # checking validation of email using re
    pattern = compile('(^|\s)[-a-z0-9_.]+@([-a-z0-9]+\.)+[a-z]{2,6}(\s|$)')
    is_valid = pattern.match(email)
    if is_valid:
        return 1
    else:
        return 0


@app.route('/add_user', methods=["POST"])
def check_input_data():
    login = request.form['login']
    passwd = request.form['pass']
    mail = request.form['email']
    phone_num = request.form['phone']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    login_check = login_is_unique(login)
    passwd_check = passwd_is_valid(passwd)
    email_check = email_is_walid(mail)
    # sending result to front by results from login_is_unique, passwd_is_valid and email is valid
    if login_check and passwd_check and email_check:
        first_name = first_name.capitalize()
        last_name = last_name.capitalize()
        db.session.add(User(login, passwd, mail, phone_num, first_name, last_name))
        db.session.commit()
        json_str = '''
        HTTP Status Code: 200
        Representation:
        {
            "login": %s
        }
        ''' % login

        return jsonify({json_str: 'Success'})
    # if login is't unique program will send message to front
    elif login_check == 0:
        json_str = '''
                HTTP Status Code: 400
                Representation:
                {
                    "login": %s
                }
                ''' % login
        return jsonify({json_str: 'Not unique login'})
    # if password is't valid program will send message to front
    elif passwd_check == 0:
        json_str = '''
                        HTTP Status Code: 400
                        Representation:
                        {
                            "login": %s
                        }
                        ''' % login
        return jsonify({json_str: 'Wrong password'})
    # if e'mail is't valid program will send message to front
    elif email_check == 0:
        json_str = '''
                        HTTP Status Code: 400
                        Representation:
                        {
                            "login": %s
                        }
                        ''' % login
        return jsonify({json_str: 'Incorrect email'})
    else:
        json_str = '''
                        HTTP Status Code: 400
                        Representation:
                        {
                            "login": %s
                        }
                        ''' % login
        return jsonify({json_str: 'Wrong Data'})


# checking user's login and password
def user_check(login, passwd):
    import mysql.connector

    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="1234",
        database="test_task"
    )

    mycursor = mydb.cursor()
    mycursor.execute("SELECT login, pwd FROM user")

    myresult = mycursor.fetchall()

    for i in range(len(myresult)):
        log = myresult[i]
        if login == log[0]:
            if log[1] == passwd:
                return 1
            return 2
    return 0


@app.route('/confirm_user', methods=["POST"])
def check_curr_user():
    global attempts, delta_time, time1, login_out, time_out
    time_n = datetime.now()
    login = request.form['login']
    passwd = request.form['pass']
    find_user = user_check(login, passwd)
    # in attempts we'd wrote unsuccessful attempts to log in
    # if attempts = 3 and time < 15 minutes and login belongs to the user who has not passed verification
    # we're opening start page 'index.html'
    if attempts == 3:
        if login_out == login:
            t_n = datetime.now()
            time_delta = (t_n - time_out).total_seconds()
            if time_delta < 900:
                return render_template('index.html')
            else:
                attempts = 0
    # checking results from user_check
    # if result = 1 then success
    # if result = 2 then wrong password
    # if result = 0 then wrong login
    if find_user == 1:
        json_str = '''
                HTTP Status Code: 200
                Representation:
                {
                    "login": %s
                }
                ''' % login
        return jsonify({json_str: 'success'})
    elif find_user == 2:
        json_str = '''
                HTTP Status Code: 400
                Representation:
                {
                    "login": %s
                }
                ''' % login
        if login == login_out:
            attempts += 1
            time_n = datetime.now()
            delta_time = (time_n - time1).total_seconds()
        else:
            attempts = 1
            login_out = login
            time1 = datetime.now()
            delta_time = (time_n - time1).total_seconds()
        if attempts == 3 and delta_time < 60:
            with open("data_file.json", "w") as write_file:
                json.dump(json_str, write_file)
            return render_template('index.html')
        elif attempts == 3 and delta_time > 60:
            attempts = 0
        return jsonify({json_str: 'Wrong password'})
    elif find_user == 0:
        json_str = '''
                        HTTP Status Code: 400
                        Representation:
                        {
                            "login": %s
                        }
                        time
                        ''' % login
        if login == login_out:
            attempts += 1
            time_n = datetime.now()
            delta_time = (time_n - time1).total_seconds()
        else:
            attempts = 1
            login_out = login
            time1 = datetime.now()
            delta_time = (time_n - time1).total_seconds()
            time_out = datetime.now()
        # if attempts = 3 and delta_time <= 60 then user will be redirected to 'registration.html'
        if attempts == 3 and delta_time <= 60:
            return render_template('registration.html')
        elif attempts == 3 and delta_time > 60:
            attempts = 0
        return jsonify({json_str: 'Wrong login'})


if __name__ == "__main__":
    app.run()
