import gevent
from gevent import monkey
monkey.patch_all()
import random
import datetime
import hashlib
from flask import Flask, session, request, redirect, url_for, render_template, flash
from flask_socketio import emit, join_room,SocketIO,leave_room, Namespace
import os
import query


app = Flask(__name__)
app.config.update({     #配置APP模块
    'DEBUG':True,
    'TEMPLATES_AUTO_RELOAD' :True,
    'SECRET_KEY': os.urandom(10)
})
socketio = SocketIO(cors_allowed_origins="*")
socketio.init_app(app)



# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        sql="select username,password from user where email = %s" 
        params=[email]
        result1 = query.query(sql,params)
        if result1[1] == password:
            print("登陆成功")
            flash('登陆成功')
            session['username'] = result1[0]
            session['email'] = email
            session.permanent = True
            return redirect(url_for('chatroom'))
        else:
            print('error')


@app.route('/chatroom', methods=['GET', 'POST'])
def chatroom():
    if request.method=='GET':
        return render_template("ChatPage.html")
    if request.method=='POST':
        msg = request.form.get('message')
        # emit('message', {'data': msg}, broadcast=True)

# 注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        print(username,email,password)
        sql = 'insert into user(username,email,password) values(%s,%s,%s)'
        params = [username,email,password]
        msg = query.update(sql,params)
        if msg == 'Changed successfully':
                print("注册成功")
                flash('注册成功')
                return redirect(url_for('login'))
        else:
                print("注册失败")
                flash('注册失败')
                return render_template('register.html')
        
        return render_template('login.html')

# 登录状态保持
@app.context_processor
def login_status():
    # 从session中获取
    username = session.get('username')
    email = session.get('email')
    return{'username':username,'email':email}

# #连接主页
# @socketio.on('connect',namespace='/chatroom')
# def connect():
#     t=str(session.get('username'))
#     print(t+'连接主页成功')
#     emit('Uconnect', {'data': t},namespace='/chatroom')

@socketio.on('joined',namespace='/chatroom')
def joined(information):
    join_room(information)
    time = datetime.datetime.now()
    time = datetime.datetime.strftime(time, '%Y-%m-%d %H:%M:%S')
    emit('Uconnect', {'data': session["username"],'time':time},room=information,broadcast=True)


@socketio.on('leave',namespace='/chatroom')
def leave(information):
    join_room(information)
    time = datetime.datetime.now()
    time = datetime.datetime.strftime(time, '%Y-%m-%d %H:%M:%S')
    emit('Uleave', {'data': session["username"],'time':time}, room=information, broadcast=True)
    print('离开聊天室')



@socketio.on('chat message', namespace='/chatroom')
def on_message(x):
    print('收到消息',x)
    time = datetime.datetime.now()
    time = datetime.datetime.strftime(time, '%Y-%m-%d %H:%M:%S')
    emit('back message', {'data': x,'user':session["username"],'time':time},room='chatroom',broadcast=True)
    print('发送成功')



if __name__ == '__main__':
    socketio.run(app)
    