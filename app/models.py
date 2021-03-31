from datetime import datetime
from hashlib import md5
from time import time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import app, db, login
from app.m3u import MTrack, M3UList
from flask_avatars import Identicon
import hashlib
from app import avatars

############################################################
#                    User Model
#
############################################################

followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

######################################################
#
#                   Post Model
#
######################################################


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)

    ####################################################
    #                Playlist Model
    #
    ####################################################


playlist_memberships = db.Table('playlist__memberships',
                             db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True),
                             db.Column('track_id', db.Integer, db.ForeignKey('track.id'), primary_key=True)
                             )


class Playlist(db.Model):

        id = db.Column(db.Integer, primary_key=True)
        playlist_name = db.Column(db.String(80), index=True, unique=True)
        playlist_filename = db.Column(db.String(255))
        avatar_s = db.Column(db.String(64))
        avatar_m = db.Column(db.String(64))
        avatar_l = db.Column(db.String(64))
        tracks = db.relationship('Track', secondary=playlist_memberships, lazy='subquery',
                                 backref=db.backref('playlists',lazy=True))

        def get_str_id(self):
            return str(self.id)

        def get_duration_str(self):
            pls_duration =  self.get_pl_duration()
            hrs, rem = divmod(pls_duration, 3600)
            mins, secs = divmod(rem, 60)
            return str(hrs) + ' hours, ' + str(mins) + ' minutes, ' + str(secs) + ' seconds'

        def get_pl_length(self):
            # number of tracks in playlist
            return len(self.tracks)

        def get_pl_duration_t(self):
            secs = self.get_pl_duration()
            hrs, rem  = divmod(secs, 3600)
            mins, secs2 = divmod(hrs,60)

            return hrs, mins, secs2



        def get_pl_duration(self):
            # in seconds
            return sum([t.duration for t in self.tracks])


        def get_mean_duration(self):
            # in seconds
            return int(self.get_pl_length() / self.get_pl_duration())

        def get_pl_avatar_hash(self):
            import hashlib, re
            pattern = re.compile('[\W_]+')
            pl_name = pattern.sub('', self.playlist_name) + '@enlightenradio.org'
            avatar_hash = hashlib.md5(pl_name.lower().encode('utf-8')).hexdigest()
            return avatar_hash


        def trk_in_playlist_p(self, trk):
            return trk in self.tracks

        def trk_in_playlist(self, trk):

            query_track_list = Track.query.join(playlist_memberships).\
                join(Playlist).filter((playlist_memberships.c.track_id == trk.id) &
                                      (playlist_memberships.c.playlist_id == self.id)).all()

            if query_track_list:

                return True
            return False

        def add_track(self, trk, com=True):
            ntrk = db.session.query(Track).filter_by(artist_title=trk.artist_title).first()
            self.tracks.append(ntrk)
            if com:
                db.session.commit()

        def add_trk_id_list(self,id_list:[]):
            for id in id_list:
                trk = Track.query.get(id)
                if not self.trk_in_playlist_p(trk):
                    self.add_track(trk,com=False)
                    print('added {} track to {} playlist'.format(trk.artist_title, self.playlist_name))
                else:
                    print('cannot add {} track to {} playlist: duplicate exists'.format(trk.artist_title, self.playlist_name))

            db.session.commit()

            # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            #                       Static Playlist Utils                                           +
            # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # #####################################################################################
        #                        add playlist to db                                           #
        # #####################################################################################

        @staticmethod
        def add_playlist(pls=None,com=True):
            if not pls:
                raise Exception('Playlist.add_playlist: Playlist param missing or None')
            if isinstance(pls, Playlist):
                try:
                    db.session.add(pls)
                    if com:
                        db.session.commit()
                except:
                    print('Playlist.add_playlist: db add {} playlist failed'.format(pls.playlist_name))
                    raise Exception('DB add fails for {}'.format(pls.playlist_name))
            else:
                raise Exception('Playlist.add_playlist: not a Playlist object, required param')

        # #######################################################################################
        #               Parse an M3U Playlist File into a Playlist and Tracks                   #
        # #######################################################################################

        @staticmethod
        def db_pl_exists(pl):
            if isinstance(pl, Playlist):
                exists = db.session.query(
                    db.session.query(Playlist.id).filter_by(playlist_name=pl.playlist_name).exists()
                ).scalar()
                return exists
            raise Exception('not a Playlist')

        @staticmethod
        def parse_pls_plus_trks(fn=None, store=None):

            m3u = M3UList.m3u_clean_factory(fn=fn,store_lib=store) # no duplicates
            pls = Playlist(playlist_name=m3u.name, playlist_filename=m3u.fn)
            trks = [Track.make_Track_obj(mt) for mt in m3u.tracks]
            return pls,trks


        @staticmethod
        def load_playlist_and_tracks(dpls, dtrks):
            Playlist.add_playlist(dpls)
            pls = Playlist.query.filter_by(playlist_name=dpls.name).first()
            for t in dtrks:
                pls.add_track(t, com=False)
            db.session.commit()


        @staticmethod
        def make_playlist_obj(m3u: M3UList):
            pls = Playlist(playlist_name=m3u.name, playlist_filename=m3u.fn)
            return pls

        @staticmethod
        def find_pls_by_name(expr):
            return Playlist.query.filter(Playlist.playlist_name.contains(expr)).all()

        @staticmethod
        def find_pls_by_fn(expr):
            return Playlist.query.filter(Playlist.playlist_filename.contains(expr)).all()

        @staticmethod
        def find_pls_by_track_at(expr):
            plsss = []
            plss = Playlist.query.all()
            for p in plss:
                for t in p.tracks:
                    if expr in t.artist_title:
                        plsss.append(p)
                        break
            return plsss


        ##################################################
        #
        #           Track Model
        #
        ##################################################


class Track(db.Model):

    # @staticmethod
    # def generate_avatar(artist_title):
    #
    #     return filenames

    id = db.Column(db.Integer, primary_key=True)
    album = db.Column(db.String(120))
    albumartist = db.Column(db.String(80))
    artist = db.Column(db.String(80))
    bitrate = db.Column(db.Integer)
    comment = db.Column(db.String(140))
    composer = db.Column(db.String(80))
    disc = db.Column(db.Integer)
    disc_total = db.Column(db.Integer)
    duration = db.Column(db.Integer)
    filesize = db.Column(db.Integer)
    genre = db.Column(db.String(20))
    samplerate = db.Column(db.Integer)
    title = db.Column(db.String(80))
    tracknum = db.Column(db.String(3))
    track_total = db.Column(db.String(3))
    year = db.Column(db.String(8))
    url =  db.Column(db.String(240))
    artist_title = db.Column(db.String(80), unique=True, index=True)
    filename = db.Column(db.String(80), unique=True, index=True)

# tag_attrs = {'album': 'string',  # album as string
#              'albumartist': 'string',  # album artist as string
#              'artist': 'string',  # artist name as string
#              'bitrate': 'int',  # bitrate in kBits/s
#              'comment': 'string',  # file comment as string
#              'composer': 'string',  # composer as string
#              'disc': 'int',  # disc number
#              'disc_total': 'int',  # the total number of discs
#              'duration': 'int',  # duration of the song in seconds
#              'filesize': 'int',  # file size in bytes
#              'genre': 'string',  # genre as string
#              'samplerate': 'int',  # samples per second
#              'title': 'string',  # title of the song
#              'tracknum': 'string',  # track number as string
#              'track_total': 'string',  # total number of tracks as string
#              'year': 'string',  # year or data as string
#              'url': 'string',  # string from internet link
#              'artist_title': 'string',  # string for m3u ext format track line one.
#              'filename': 'string'
#
#              }

    def get_duration_str(self):
        mins, secs = divmod(self.duration, 60)
        return '(' + str(mins) + ':' + str(secs) + ')'

    def get_tr_avatar_hash(self):
        import hashlib, re
        pattern = re.compile('[\W_]+')
        pl_name = pattern.sub('', self.artist_title) + '@enlightenradio.org'
        avatar_hash = hashlib.md5(pl_name.lower().encode('utf-8')).hexdigest()
        return avatar_hash

    def get_attrs(self):
        atrs = [a for a in dir(self) if not (a.startswith('__') or a.startswith('_')) and not callable(getattr(self, a))]
        d = vars(self)
        return [(a, d.get(a)) for a in atrs]

    def __str__(self):
        return 'app.models.Track: ID: ' + str(self.id) + ', artist-title: ' + self.artist_title + ', filename: ' + self.filename


    ################################################
    #  Static Track Utils
    ################################################


    @staticmethod
    def db_trk_exists(trk):
        if isinstance(trk,Track):
            exists = db.session.query(Track.id).filter_by(artist_title=trk.artist_title).first() is not None

            exists2 = db.session.query(Track.id).filter_by(filename=trk.filename).first() is not None
            return exists or exists2
        app.logger.info('not a Track')
        return False

    @staticmethod
    def add_track(t, com=True):
        if isinstance(t, Track):

            try:
                db.session.add(t)
                if com:
                    db.session.commit()
            except Exception as inst:
                print(inst)
                raise

    @staticmethod
    def make_Track_obj(trk: MTrack):

        try:

            t = Track(album=trk.tg_attrs.album, albumartist=trk.tg_attrs.albumartist, artist=trk.tg_attrs.artist,
                      bitrate=trk.tg_attrs.bitrate, comment=trk.tg_attrs.comment, composer='', disc=trk.tg_attrs.disc,
                      disc_total=trk.tg_attrs.disc_total, duration=trk.duration, filesize=trk.tg_attrs.filesize,
                      genre=trk.tg_attrs.genre, samplerate=trk.tg_attrs.samplerate, title=trk.tg_attrs.title,
                      tracknum=trk.tg_attrs.track, track_total=trk.tg_attrs.track_total, url=trk.url,
                      year=trk.tg_attrs.year, artist_title=trk.artist_title, filename=trk.fn)
            return t
        except Exception as inst:
            print(inst)
            return None

    @staticmethod
    def find_tracks_by_at(expr):
        return Track.query.filter(Track.artist_title.contains(expr))

    @staticmethod
    def find_tracks_by_fn(expr):
        return Track.query.filter(Track.filename.contains(expr))

    @staticmethod
    def find_track_by_id(idd):
        return Track.query.get(idd)

    @staticmethod
    def add_tracks(trks:[]):

        if len(trks) > 0 & isinstance(trks[0], Track):
            for trk in trks:
                if not Track.db_trk_exists(trk):
                    try:
                        Track.add_track(trk,com=False)
                        print('added track ' + str(trk))
                    except Exception as inst:
                        print('add Track {} failed: error={}'.format(trk.artist_title, inst))
                        raise
                else:
                    print('track exists: ', trk.artist_title)

            db.session.commit()
        else:
            print(" Empty array of MTrack s, or Invalid type.")

    @staticmethod
    def add_tracks_from_dir(dir):
        from config import Config

        trk_files = Config.dir_to_filelist(dir)
        mtrks = Config.ffiles_to_tracks(trk_files)

        try:
            Track.add_tracks(mtrks)
        except Exception as inst:
            print(inst)





