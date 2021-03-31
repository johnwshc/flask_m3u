from app import app
from app.models import Playlist, Track
from app.m3u import MTrack, M3UList
from app import db
from config import Config
from pathlib import PurePath


# import json
import os

class DB_MT_Test:
    test_file1 = 'pls\\dirty\\allman bros.m3u'
    test_name1 = "allman bros"

    def __init__(self):
        self.m3u = M3UList.m3u_clean_factory(fn=DB_MT_Test.test_file1,name=DB_MT_Test.test_name1)
        self.dirty_m3u_dir = Config.MDIRTY
        self.clean_m3u_dir = Config.MCLEAN
        #  dirty file_list
        self.dirty_list = [f for f in os.listdir(self.dirty_m3u_dir) if f.endswith('.m3u')]
        self.clean_list = [f for f in os.listdir(self.clean_m3u_dir) if f.endswith('.m3u')]

    def clean_dirty_dir(self):
        clean_m3us = []
        for f in self.dirty_list:
            nf =  self.dirty_m3u_dir + '\\' + f
            print('full fn loading m3u: {}'.format(nf))
            try:
                m3u = M3UList.m3u_clean_factory(fn=nf)
            except Exception as inst:
                print('Exception making m3u obj for {}'.format(nf))
            clean_m3us.append(m3u)
        return clean_m3us


    @staticmethod
    def get_pls(name=test_name1):
        return Playlist.query.filter_by(playlist_name=name).first()

    @staticmethod
    def get_plss():
        return Playlist.query.all()

    @staticmethod
    def make_dt(mt:MTrack):
        return Track.make_Track_obj(mt)

    @staticmethod
    def get_all_dtracks():
        dtrks = Track.query.all()
        return dtrks

    @staticmethod
    def add_track_to_pls(trk: Track, pl: Playlist):
        if Track.db_trk_exists(trk):
            try:
                pl.tracks.append(trk)
                db.session.commit()
            except Exception:
                print(' Failed to add {} track to {} playlist'.format(trk.artist_title, pl.playlist_name))

    @staticmethod
    def add_tracks_to_pls(trks: [], pl: Playlist):
        for t in trks:
            if Track.db_trk_exists(t):
                try:
                    pl.tracks.append(t)
                except Exception:
                    print(' Failed to add {} track to {} playlist'.format(t.artist_title, pl.playlist_name))
        try:
            db.session.commit()
        except Exception:
            print('submit fails for added tracks to {} playlist'.format(pl.playlist_name))

    @staticmethod
    def add_single_track(trk: Track, com=True, pls=None):
        if isinstance(trk, Track):
            try:
                db.session.add(trk)
                print('added track: ' + str(trk))
                if pls and isinstance(pls, Playlist):
                    pls.tracks.append(trk)
                if com:
                    db.session.commit()
            except Exception as inst:
                print(str(inst))
        else:
            print('Not an instance of Track')

    # def add_single_mtrk(self, trk: MTrack, com=True, pls=None):
    #     if isinstance(trk, MTrack):
    #         dtrk = Track.make_Track_obj(trk)
    #         self.add_single_track(dtrk, com, pls)

    # def add_tracks(self, trks:[], pls=None):
    #     if len(trks) > 0 & isinstance(trks[0], Track):
    #         for t in trks:
    #             self.add_single_track(t, com=False, pls=pls)
    #         try:
    #             db.session.commit()
    #         except Exception as inst:
    #             print(str(inst))
    #
    #     else:
    #         print('Empty list of tracks, or list of non Track objs. ')

    # def add_mtracks(self, trks:[]):
    #     ttracks = []
    #     if len(trks) > 0 & isinstance(trks[0], MTrack):
    #         for t in trks:
    #             ttracks.append(Track.make_Track_obj(t))
    #
    #         self.add_tracks(ttracks)

    @staticmethod
    def delete_all_tracks():
        trks = Track.query.all()
        for t in trks:
            db.session.delete(t)
        db.session.commit()

    @staticmethod
    def add_playlist(m3u:M3UList):

        # Create Playlist obj from M3UList obj, and Insert Playlist into DB if it does not already exist

        pl = Playlist.make_playlist_obj(m3u)
        if not Playlist.db_pl_exists(pl):
            try:
                Playlist.add_playlist(pl)

            except Exception as inst:
                print(str(inst))
        else:
            print('Playlist {} already exists in DB'.format(pl.playlist_name))

        # Insert tracks from m3u into DB if they do not already exist
        addable_tracks = []
        for mt in m3u.tracks:
            dt = Track.make_Track_obj(mt)
            if not Track.db_trk_exists(dt):
                try:
                    Track.add_track(t=dt, com=False)
                    addable_tracks.append(dt)
                except Exception:
                    raise Exception('add {} track fails'.format(dt.artist_title))
            else:
                print('Track {} already exists in DB'.format(dt.artist_title))
                addable_tracks.append(dt)
        db.session.commit()
    #     add tracks to db playlist
        npl = Playlist.query.filter_by(playlist_name=pl.playlist_name).first()
        for dt in addable_tracks:
            npl.add_track(dt,com=False)
        db.session.commit()

    @staticmethod
    def delete_playlist(pls:Playlist):
        try:
            db.session.delete(pls)
            db.session.commit()
        except Exception as inst:
            print(inst)


    @staticmethod
    def get_audio_files_from_dir(param):
        dirr = Config.MEDIA_SRC_DIRS[param]
        # tot=0
        media_fils = []
        # other = []
        dirrs = []
        # suffs = []
        # non_med_suffs = []
        suffixes = ['.mp3', '.mp4', '.n4a', '.flac', '.m4v', 'wmv']

        for root, dirs, files in os.walk(dirr, topdown=False):
            for name in files:
                f = os.path.join(root,name)
                pp = PurePath(f)
                if pp.suffix in suffixes:
                    # suffs.append(pp.suffix)
                    media_fils.append(f)
                # else:
                #     non_med_suffs.append(pp.suffix)
            for d in dirs:
                dd = os.path.join(root,d)
                dirrs.append(dd)

            # # fl = dirr + '\\' + f
            # fl = os.path.join(root,dir,f)
            # pp = PurePath(fl)
            # if pp.suffix in suffixes:
            #     tot += 1
            #     # if not tot % 10:
            #     #     # print('tot = {} {}'.format(tot,fl))
            #
            #     # print(' file is {}'.format(fl))
            #     media_fils.append(fl)
            # else:
            #     other_fils.append(fl)
            # try:
            #     m3u = M3UList.m3u_clean_factory(fn=fl,nf=True)
            #     DB_MT_Test.add_playlist(m3u)
            # except Exception as inst:
            #     print('failed to create m3u for file {}, \n Exception: {}'.format(fl, inst))
        return media_fils,dirrs

    @staticmethod
    def add_tracks_from_dir(param):

        count_added = 0
        count_tot = 0
        exts = ['.mp3', '.m4a', '.flac','.m4v','.wmv']
        for root, dirs, files in os.walk(Config.MEDIA_SRC_DIRS[param], topdown=True):
            for name in files:
                nname = PurePath(os.path.join(root,name))
                suf = nname.suffix
                if suf in exts:

                    print('loading file as Track into db: {}'.format(os.path.join(root, name)))
                    mt = MTrack.mtrack_factory(os.path.join(root, name))
                    if not mt:
                        print('MTrack {}  is None'.format(str(nname)))
                        continue

                    t = Track.make_Track_obj(mt)
                    if not t:

                        print('Track {}  is None'.format(str(nname)))
                        continue
                    try:
                        if not  Track.db_trk_exists(t):
                            Track.add_track(t,com=True)
                            count_added += 1
                            count_tot += 1
                        else:
                            count_tot += 1

                    except Exception  as inst:
                        print(inst)
                        print('rolling back and commit after failing db add {}'.format(inst))
                        db.session.rollback()
                        db.session.commit()
                        raise inst


        return count_tot,count_added


    @staticmethod
    def slugify_media_file(f, slug_dic: dict):

        from slugify import slugify
        suffixes = ['.mp3', '.mp4', '.n4a', '.flac', '.m4v', 'wmv']
        pp = PurePath(f)
        if os.path.exists(f) and pp.suffix in suffixes:
            of = str(pp)
            ssf = slugify(pp.stem) + pp.suffix
            sf = str(pp.parent) + '\\' + ssf
            try:
                os.rename(of,sf)
                slug_dic[of] = sf
                return sf

            except Exception as inst:
                print('EXCEPTION: fail to rename old file  {}, \nto slugified file  {}, \nerror: {}'.format(of,sf,inst))
                return None

        else:
            print('File {} does not exist, or is not a media file.'.format(f))
            app.logger.info('File {} does not exist, or is not a media file.'.format(f))
            return None

    @staticmethod
    def slugify_dir(fq_dir):
        suffixes = ['.mp3', '.mp4', '.n4a', '.flac', '.m4v', 'wmv']
        slug_dict = {'dir': fq_dir}
        if os.path.exists(fq_dir):
            files = os.listdir(fq_dir)
            for f in files:
                of = fq_dir + '\\' + f
                pp = PurePath(of)
                if pp.stem in suffixes:
                    sf = DB_MT_Test.slugify_media_file(of,slug_dict)
                    if not sf:
                        slug_dict[of] = '**NO SLUG**'
            return slug_dict
        else:
            print('directory path {} does not exist.'.format(fq_dir))
            return slug_dict






    @staticmethod
    def run(param='youtube3'):
        fls, dirs  = DB_MT_Test.get_audio_files_from_dir(param)
        root_dir =  Config.MEDIA_SRC_DIRS[param]
        d1 = dirs[0]
        print()
        sdict = DB_MT_Test.slugify_dir(d1)























