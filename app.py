from flask import Flask, render_template, g, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from database import *

app = Flask(__name__)
app.config['SECRET_KEY'] = "adwgdaiugsdiuagwidgasiudg"


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def current_user():
    user_now = None
    if 'username' in session:
        db = get_db()
        user_get = db.execute('select id, name, expert, admin from users where name =?', [session['username']])
        user_now = user_get.fetchone()
    return user_now


@app.route('/')
def index():
    user = current_user()
    db = get_db()
    questions = db.execute(
        'select questions.question_text, questions.answer_text, askers.name as askers_name, experts.name as expert_name from questions join users as askers on askers.id == questions.asked_by_id join users as experts on experts.id == questions.expert_id where questions.answer_text is not null ')
    questions = questions.fetchall()
    return render_template('home.html', user=user, questions=questions)


@app.route('/register', methods=['POST', 'GET'])
def register():
    db = get_db()
    user = current_user()
    if request.method == "POST":
        name = request.form.get('name')
        password = request.form.get('password')
        hashed = generate_password_hash(password, method='sha256')
        db.execute('insert into users(name,password,expert,admin) values (?,?,?,?)', [name, hashed, False, False])
        db.commit()
        return redirect(url_for('login'))
    return render_template('register.html', user=user)


@app.route('/login', methods=['POST', 'GET'])
def login():
    user = current_user()
    db = get_db()
    if request.method == "POST":
        name = request.form.get('name')

        password = request.form.get('password')
        user_checker = db.execute('select name, password from users where name=?', [name])
        user_one = user_checker.fetchone()
        if user_one:
            if check_password_hash(user_one['password'], password):
                session['username'] = name
                return redirect(url_for('index'))
            else:
                print("parol notug'ri")
        else:
            print(False)
    return render_template('login.html', user=user)


@app.route('/question')
def question():
    user = current_user()
    return render_template('question.html', user=user)


@app.route('/answer/<int:question_id>', methods=['POST', 'GET'])
def answer(question_id):
    db = get_db()
    user = current_user()
    if request.method == "POST":
        answer_text = request.form.get('answer_text')
        db.execute('update questions set answer_text =? where id =?', [answer_text, question_id])
        db.commit()
        return redirect(url_for('unanswered'))
    question_get = db.execute('select id,question_text from questions where id=?', [question_id])
    question_get = question_get.fetchone()
    return render_template('answer.html', question_get=question_get, question_id=question_id, user=user)


@app.route('/ask', methods=['POST', 'GET'])
def ask():
    user = current_user()
    db = get_db()
    if request.method == "POST":
        question_text = request.form.get('question_text')
        expert_id = int(request.form.get('expert_id'))
        db.execute('insert into questions(question_text,asked_by_id,expert_id) values (?,?,?)',
                   [question_text, user['id'], expert_id])
        db.commit()
        return redirect(url_for('index'))
    experts = db.execute('select id, name ,expert, admin from users where expert=?', [True])
    return render_template('ask.html', experts=experts, user=user)


@app.route('/unanswered')
def unanswered():
    user = current_user()
    db = get_db()

    questions = db.execute(
        'select questions.id, questions.question_text, questions.asked_by_id, questions.expert_id, users.name from questions join users on questions.asked_by_id == users.id where questions.answer_text is null and questions.expert_id=?',
        [user['id']])
    questions = questions.fetchall()
    print(questions)
    return render_template('unanswered.html', questions_list=questions, user=user)


@app.route('/users')
def users():
    user = current_user()
    # db = get_db()
    # users_list = db.execute('select id,name,expert,admin from users where admin =?', [False])
    # users_list = users_list.fetchall()
    # return render_template('users.html', users_list=users_list, user=user)
    db = get_db()
    users_list = db.execute('select id,name,expert,admin from users where admin=?', [False])
    users_list = users_list.fetchall()
    return render_template('users.html', users_list=users_list, user=user)


@app.route('/promote/<int:user_id>')
def promote(user_id):
    db = get_db()
    user_check = db.execute('select id, expert from users where id=?', [user_id])
    user_check = user_check.fetchone()
    #
    if user_check['expert']:
        db.execute('update users set expert = FALSE where id=?', [user_id])
        db.commit()
    else:
        db.execute('update users set expert = True where id=?', [user_id])
        db.commit()
    return redirect(url_for('users'))


@app.route('/logout')
def logout():
    session['username'] = None
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
