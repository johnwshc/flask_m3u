import os
import requests
from bs4 import BeautifulSoup
import json

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['your-email@example.com']
    POSTS_PER_PAGE = 25
    TRACKS_PER_PAGE = 20
    AVATARS_SAVE_PATH = os.path.join(basedir, 'avatars')
    print('config: ' + AVATARS_SAVE_PATH)
    EMAIL_SERVER_CMD = 'flask_m3u>python -m smtpd -n -c DebuggingServer localhost:8025'

    M3U_DIRS = {'clean': basedir + '\\pls\\clean\\', 'dirty': basedir + '\\pls\\dirty\\'}

    MDIRTY = basedir + '\\pls\\dirty'
    MCLEAN = basedir + '\\pls\\clean'

    MEDIA_SRCS_KEYS =['ia_downloads', 'youtube', 'itunes', 'concerts', 'youtube2', 'test']
    MEDIA_SRC_DIRS = {'ia_downloads' : 'E:\\ia_downloads', 'youtube': 'C:\\Users\\rooster\\Music\\youtube',
                      'itunes': 'F:\\iTunes\\iTunes Media\\Music',
                      'concerts': 'C:\\Users\\rooster\\Music\\Concert Vault',
                      'youtube2':'E:\\youtube_downloads', 'youtube3': 'F:\\youtube_downloads'}
    PLAYLIST_SRC_DIRS = {'project_clean': basedir + '\\pls\\clean\\', 'project_dirty': basedir + '\\pls\\dirty\\',
                         'prod': "\\Users\\rooster\\Music\\playlists\\"}

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #                                Playlist Utils
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++





    # ##############################################################################
    #                    return a list of audio files from a directory             #
    ################################################################################

    @staticmethod
    def dir_to_filelist(dirr):
        print('in dir: ' + dirr)
        trks = []
        for root, dirs, files in os.walk(dirr):
            for file in files:
                # print('inspecting file: ' + file)
                if (file.endswith(".mp3") or file.endswith('.m4a') or file.endswith('.flac')):
                    trks.append(os.path.join(root, file))

        return trks

    # ##############################################################################
    #                   return a list of MTracks from a Filelist                   #
    ################################################################################

    @staticmethod
    def ffiles_to_tracks(fls:[]):
        from app.models import MTrack
        mtrks = []
        for ftrk in fls:
            try:
                mtrk = MTrack.mtrack_factory(fn=ftrk)
                mtrks.append(mtrk)

            except Exception as inst:
                print('MTrack constructor fails: fn= {}\n error={}'.format(ftrk,inst))
                continue

        return mtrks

    # ##############################################################################
    #                  convert MTrack                    #
    ################################################################################

    @staticmethod
    def mtracks_to_tracks(mtrks):
        from app.models import Track
        from app.m3u import  MTrack
        if (len(mtrks) > 0) and (isinstance(mtrks[0], MTrack)):
            trks = [Track.make_Track_obj(mt) for mt in mtrks]
        return trks

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #                        Track  Utils
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # ##############################################################################
    #                  Load JSON encoded filelist                                  #
    ################################################################################

    @staticmethod
    def load_media_src_dict(f):
        with open(f) as file:
            return json.load(file)

        # ##############################################################################
        #                  SAVE  JSON encoded filelist                                 #
        ################################################################################

    @staticmethod
    def save_media_src_json(files:[], name='concerts', dest='json/'):
        js = json.dumps({name:files})
        fn = dest + name + '.json'
        with open(fn,"w+") as f:
            json.dump({name: files}, f)
        return js

    # ##############################################################################
    #                  READ  JSON encoded filelist                                 #
    ################################################################################

    @staticmethod
    def read_media_src_json(name, dest='json/'):
        fn = dest + name + '.json'
        js = json.load(fn)
        return js

    # ##############################################################################
    #                  Get HTML Body content  FIX!!                                #
    ################################################################################

    @staticmethod
    def get_html_body_content(file=None, txt=None, url=None):
        file1 = 'app\\static\\bluegrass.pls.html'
        file2 = 'app\\static\\bluegrass2.pls.html'
        file = file1
        if file:
            with open(file) as f:
                txth = f.read()
            soup = BeautifulSoup(txth, 'lxml')
            return soup.head, soup.body
        elif txt:
            soup = BeautifulSoup(txt, 'lxml')
            return soup.head, soup.body

        elif url:
            txtu = requests.get(url).text
            soup = BeautifulSoup(txtu, 'lxml')
            return soup.head, soup.body

        else:
            return None

    # ##############################################################################
    #                  Prettify HTML                                               #
    ################################################################################

    @staticmethod
    def pretty_html(html):
        return BeautifulSoup(html, 'lxml').prettify()
