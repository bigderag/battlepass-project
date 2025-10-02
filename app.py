import json
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'a_very_secret_key_for_battle_pass'  # این کلید را در پروژه واقعی تغییر دهید

DATABASE_FILE = 'database.json'

# --- توابع کار با دیتابیس ---
def read_data():
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_data(data):
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- صفحات و منطق برنامه ---

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        data = read_data()
        if data['users'][session['username']]['is_admin']:
            return redirect(url_for('admin_panel'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        data = read_data()
        if username in data['users'] and data['users'][username]['password'] == password:
            session['username'] = username
            flash('خوش آمدید!', 'success')
            if data['users'][username]['is_admin']:
                return redirect(url_for('admin_panel'))
            return redirect(url_for('dashboard'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است.', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    data = read_data()
    user_data = data['users'][username]
    tasks = data['tasks']
    shop_items = data['shop_items']
    user_submissions = [s for s in data['submissions'] if s['username'] == username]
    
    return render_template('dashboard.html', user=user_data, tasks=tasks, shop_items=shop_items, submissions=user_submissions, username=username)

@app.route('/admin')
def admin_panel():
    if 'username' not in session or not read_data()['users'][session['username']]['is_admin']:
        return redirect(url_for('login'))
        
    data = read_data()
    pending_submissions = [s for s in data['submissions'] if s['status'] == 'pending']
    return render_template('admin.html', submissions=pending_submissions, username=session['username'])

@app.route('/submit_task/<int:task_id>', methods=['POST'])
def submit_task(task_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    data = read_data()
    task = next((t for t in data['tasks'] if t['id'] == task_id), None)
    if task:
        new_submission_id = max([s['id'] for s in data['submissions']] or [0]) + 1
        submission = {
            'id': new_submission_id,
            'username': session['username'],
            'task_id': task_id,
            'task_title': task['title'],
            'status': 'pending'
        }
        data['submissions'].append(submission)
        write_data(data)
        flash('تسک شما برای تایید ارسال شد.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/approve/<int:submission_id>')
def approve_submission(submission_id):
    if 'username' not in session or not read_data()['users'][session['username']]['is_admin']:
        return redirect(url_for('login'))
        
    data = read_data()
    submission = next((s for s in data['submissions'] if s['id'] == submission_id), None)
    if submission and submission['status'] == 'pending':
        submission['status'] = 'approved'
        task = next((t for t in data['tasks'] if t['id'] == submission['task_id']), None)
        if task:
            data['users'][submission['username']]['points'] += task['points']
            write_data(data)
            flash(f"تسک '{submission['task_title']}' تایید شد.", 'success')
    return redirect(url_for('admin_panel'))

@app.route('/purchase/<int:item_id>', methods=['POST'])
def purchase_item(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    data = read_data()
    item = next((i for i in data['shop_items'] if i['id'] == item_id), None)
    user = data['users'][username]

    if item and user['points'] >= item['cost']:
        user['points'] -= item['cost']
        write_data(data)
        flash(f"شما '{item['title']}' را با موفقیت خریدید!", 'success')
    else:
        flash('امتیاز شما برای خرید این آیتم کافی نیست.', 'danger')
        
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('شما با موفقیت خارج شدید.', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
