from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, send_from_directory, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db, avatars
from app.forms import LoginForm, RegistrationForm, EditProfileForm, \
    EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm, EditTrackForm, InputGridTableForm,\
    InputGridRecordForm
from app.models import User, Post, Playlist, Track
from app.email import send_password_reset_email
from app.m3u import M3UList, MTrack, Playlists
from jinja2 import Template
from config import Config
from flask_table import Table, Col
from werkzeug.datastructures import MultiDict

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)


@app.route('/playlist/<id>', methods=['GET', 'POST'])
def m3u_playlist(id):
    # from config import Config
    pls = Playlist.query.get(id)
    # fn = Config.M3U_DIRS['clean'] + 'bob dylan.m3u'
    # fn = pls.playlist_filename
    # m3u = M3UList.m3u_clean_factory(fn,name=pls.playlist_name)
    return render_template('playlist.html', pls=pls, avatars=avatars)


@app.route('/playlists', methods=['GET'])
def playlists():
    plss =  Playlist.query.all()
    npl = len(plss)
    return render_template('playlists.html', plss=plss, num_pl=npl)


@app.route('/track/<id>', methods=['GET', 'POST'])
def track(id):
    trk = Track.query.get(id)
    return render_template('track.html',trk=trk)


@app.route('/edit_track/<id>', methods=['GET', 'POST'])
def edit_track(id):
    trk = Track.query.get(id)
    form = EditTrackForm(id=trk.id,album=trk.album,
                         albumartist=trk.albumartist, artist=trk.artist, comment=trk.comment,
                         composer=trk.composer, genre=trk.genre, title=trk.title)
    if form.validate_on_submit():
        if not id:
            flash('track  not found.')
            return redirect(url_for('playlists'))
        trk.album = form.album.data
        trk.albumartist = form.albumartist.data
        trk.artist = form.artist.data
        trk.comment = form.comment.data
        trk.composer = form.composer.data
        trk.genre = form.genre.data
        trk.title = form.title.data
        db.session.commit()
        redirect(url_for('track', id=id))

    return render_template('edit_track.html', form=form, trk=trk)


@app.route('/add_tracks/<pid>', methods=['GET', 'POST'])
def add_tracks_pl(pid):
    if request.method == 'POST':
        for v in request.form.values():
            print('val: {}'.format(v))
        chk_ids = request.form.getlist('add_2_playlist')
        # cids = [s.split('_')]
        # redirect(url_for('playlists'))
        return 'Done'

    if request.method == 'GET':
        pls = Playlist.query.get(pid)
        page = request.args.get('page', 1, type=int)
        trks = Track.query.paginate(page, app.config['TRACKS_PER_PAGE'], False)
        next_url = url_for('index', page=trks.next_num) \
            if trks.has_next else None
        prev_url = url_for('index', page=trks.prev_num) \
            if trks.has_prev else None
        # print(len(trks))
        return render_template('add_tracks.html', trks=trks, pls=pls,  title='Add Tracks', prev_url=prev_url, next_url=next_url)


        # for t in trks:
        #     data = {'tid': t.id}
        #     trk_form  = InputGridRecordForm(data=MultiDict(data))
        #     records.append(trk_form)
        #     pairs.append((trk_form, t))

        # print('len trks : {}'.format(len(trks)))
        # print('len forms: {}'.format(len(records)))
        # data2 = {'gridtblrecords': records}
        # form = InputGridTableForm(MultiDict(data2))

    # else:
    #     form = InputGridTableForm()


    # return render_template('inputgrid.html', form=form, pls=pls,pairs=pairs )


def from_template(form=None, pls=None):

    template = '''
    <body>
    <h1> Add to {{ pls.playlist_name }} Playlist </h1>
    <table>
        <tbody>
            {{ form.csrf_token }}
            {% for grid_record in form.gridtblrecords %}
                <tr>
                    {% for field in grid_record %}
                        <td>{{ field.label }}</td>
                        <td> 
                    {% endfor %}
                </tr>
            {% endfor %}
        </tbody>
    </table>
    </body> '''
    return Config.pretty_html(Template(template, autoescape=True).render(form=form, pls=pls))


@app.route('/pl_remove_track/<pl_id>/<trk_id>', methods=['GET',])
def pl_remove_track(pl_id,trk_id):
    pls = db.session.query(Playlist).get(pl_id)
    trk =  db.session.query(Track).get(trk_id)
    pls.tracks.remove(trk)
    db.session.commit()
    return redirect(url_for('m3u_playlist',id=pls.id))



@app.route('/run-tasks')
def run_tasks():
    for i in range(10):
        app.apscheduler.add_job(func=scheduled_task, trigger='date', args=[i], id='j' + str(i))

    return 'Scheduled several long running tasks.', 200


def scheduled_task(task_id):
    import time
    for i in range(10):
        time.sleep(1)
        print('Task {} running iteration {}'.format(task_id, i))




