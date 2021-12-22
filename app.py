from flask_login import LoginManager, login_manager, login_user, login_required, logout_user, current_user
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room
from pymongo.errors import DuplicateKeyError

from db import add_room_members, get_room, get_room_members, get_rooms_for_user, get_user, is_room_admin, is_room_member, remove_room_members, save_room, save_user, update_room

app = Flask(__name__)
app.secret_key = 'my secret key'
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.route('/')
def home():
    rooms = []
    if current_user.is_authenticated:
        rooms = get_rooms_for_user(current_user.username)

    return render_template('index.html', rooms=rooms)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # redirect to home if user is logged in
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)
            return redirect(url_for('home'))
        else:
            message = 'Failed to login!'

    return render_template('login.html', message=message)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        # redirect to home if user is logged in
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            save_user(username, email, password)
            return redirect(url_for('login'))
        except DuplicateKeyError:
            message = 'User already exists!'

    return render_template('signup.html', message=message)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/create-room', methods=['GET', 'POST'])
@login_required
def create_room():
    message = ''
    if request.method == 'POST':
        room_name = request.form.get('room_name')
        usernames = [username.strip()
                     for username in request.form.get('members').split(',')]

        if len(room_name) and len(usernames):
            room_id = save_room(room_name, current_user.username)

            # prevent the creator to insert his own username
            if current_user.username in usernames:
                usernames.remove(current_user.username)

            add_room_members(room_id, room_name, usernames,
                             current_user.username)

            return redirect(url_for('view_room', room_id=room_id))

        else:
            message = 'Failed to create room'

    return render_template('create_room.html', message=message)


@app.route('/rooms/<room_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = get_room(room_id)
    if room and is_room_admin(room_id, current_user.username):
        existing_room_members = [member['_id']['username']
                                 for member in get_room_members(room_id)]
        room_members_str = ','.join(existing_room_members)
        message = ''
        if request.method == 'POST':
            room_name = request.form.get('room_name')
            room['room_name'] = room_name
            update_room(room_id, room_name)

            new_members = [username.strip()
                           for username in request.form.get('members').split(',')]
            members_to_add = list(
                set(new_members) - set(existing_room_members))
            members_to_remove = list(
                set(existing_room_members) - set(new_members))

            if len(members_to_add):
                add_room_members(room_id, room_name,
                                 members_to_add, current_user.username)

            if len(members_to_remove):
                remove_room_members(room_id, members_to_remove)

            message = 'Room edited successfully'
            room_members_str = ','.join(new_members)

        return render_template('edit_room.html', room=room, room_members_str=room_members_str, message=message)
    else:
        return 'Room not found', 404


@app.route('/rooms/<room_id>')
@login_required
def view_room(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        room_members = get_room_members(room_id)
        return render_template('view_room.html', username=current_user.username, room=room, room_members=room_members)
    else:
        return 'Room not found', 404


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info('{} has sent the message to the {} room : {}'.format(
        data['username'], data['room'], data['message']))

    socketio.emit('receive_message', data, room=data['room'])


@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info('{} has joined the room {}'.format(
        data['username'], data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement', data)


@login_manager.user_loader
def load_user(username):
    # return information for particular user
    return get_user(username)


if __name__ == '__main__':
    socketio.run(app, debug=True)
