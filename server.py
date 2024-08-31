from bottle import Bottle, request, response, run
import sqlite3
import uuid
import json
import hmac
import requests

app = Bottle()

# 基础信息
captcha_id = '' # 极验ID
captcha_key = '' # 极验KEY
admin_passwords = [] # 管理密码，可填多个
api_server = 'http://gcaptcha4.geetest.com' # 极验API服务器，一般无需改动
PORT = 8500 # 后端运行端口
HOST = '0.0.0.0' # 后端运行地址，一般无需改动

conn = sqlite3.connect('messages.db', check_same_thread=False)
c = conn.cursor()


def init_db():
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            qq TEXT,
            content TEXT,
            uuid TEXT,
            pos TEXT
        )
    ''')
    conn.commit()

@app.post('/message')
def get_messages():
    c.execute('SELECT name, qq, content, uuid, pos FROM messages')
    messages = [{'name': row[0], 'qq': row[1], 'content': row[2], 'uuid': row[3], 'pos': row[4]} for row in c.fetchall()]
    response.content_type = 'application/json'
    return json.dumps(messages)


@app.post('/submit')
def submit_message():
    try:
        data = request.json
        name = data.get('name')
        qq = data.get('qq')
        content = data.get('content')
        lot_number = data.get('lot_number')
        captcha_output = data.get('captcha_output')
        pass_token = data.get('pass_token')
        gen_time = data.get('gen_time') 
    except AttributeError:
        response.status = 500
        return {'result': 'error', 'reason': 'Incomplete parameters'}

    lotnumber_bytes = lot_number.encode()
    prikey_bytes = captcha_key.encode()
    sign_token = hmac.new(prikey_bytes, lotnumber_bytes, digestmod='SHA256').hexdigest()

    query = {
        "lot_number": lot_number,
        "captcha_output": captcha_output,
        "pass_token": pass_token,
        "gen_time": gen_time,
        "sign_token": sign_token,
    }

    url = api_server + '/validate' + '?captcha_id={}'.format(captcha_id)

    try:
        res = requests.post(url, query)
        assert res.status_code == 200
        gt_msg = json.loads(res.text)
    except:
        gt_msg = {'result': 'fail', 'reason': 'request geetest api fail'}

    if gt_msg['result'] == 'success':
        message_uuid = str(uuid.uuid4())
        c.execute('INSERT INTO messages (name, qq, content, uuid, pos) VALUES (?, ?, ?, ?, ?)', (name, qq, content, message_uuid, ''))
        conn.commit()
        return {'status': 'success'}
    else:
        response.status = 403
        return {'status': 'error', 'message': 'Behavior verification failed'}


@app.post('/del')
def delete_message():
    try:
        data = request.json
        message_uuid = data.get('uuid')
        password = data.get('password')
    except AttributeError:
        response.status = 500
        return {'result': 'error', 'reason': 'Incomplete parameters'}

    if password not in admin_passwords: 
        response.status = 403
        return {'status': 'error', 'message': 'Invalid password'}

    c.execute('DELETE FROM messages WHERE uuid = ?', (message_uuid,))
    conn.commit()
    return {'status': 'success'}

@app.post('/top')
def toggle_top():
    try:
        data = request.json
        message_uuid = data.get('uuid')
        password = data.get('password')
        top = data.get('top')
    except AttributeError:
        response.status = 500
        return {'result': 'error', 'reason': 'Incomplete parameters'}

    if password not in admin_passwords: 
        response.status = 403
        return {'status': 'error', 'message': 'Invalid password'}

    pos = 'top' if top else ''
    c.execute('UPDATE messages SET pos = ? WHERE uuid = ?', (pos, message_uuid))
    conn.commit()
    return {'status': 'success'}


if __name__ == '__main__':
    init_db()
    print("Message Board 开源版")
    run(app, host=HOST, port=PORT)
