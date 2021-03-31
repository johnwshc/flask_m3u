from pathlib import PurePath
from jinja2 import FileSystemLoader, Environment
import pandas as pd
from config import Config
import os
import time
from tinytag import TinyTag, TinyTagException
import sys
from app import app


# ################################################################################
#                           A Radio Station Track                                #
# ################################################################################

class RTrack:
    types = ['track', 'station']
    """RTrack a class modeling a pls or m3u file representation of an
    Internet Radio URL. """
    def __init__(self, url:str, data:dict = {}):
        self.url = url
        self.station_name = data.get('name', None)
        self.station_location = data.get('station_location', None)
        self.site = data.get('site', None)
        self.email = data.get('email', None)
        self.data = data
        self.type = data.get('type', None)


    def get_data(self):
        return self.data

    def get_ser_data(self):
        return pd.Series(self.data)

    def get_simple_m3u_line(self):
        return self.url

    def write_playlist(self, path):
        with open(path + self.station_name + '.m3u', "w+") as f:
            f.write(self.url)

    def __is_equal(self, rtrk):
        return self.url == rtrk.url

    @staticmethod
    def RTrackFactory( lines: list ,url=None, name=None, email=None, site=None, info=None, type=types[1]):
        from urllib.parse import urlparse

        data = {'url':url,'name': name, 'email': email, 'site': site, 'data': info, 'type': type, 'duration':-1}
        # xf_rec_marker = '#EXTINF:'
        if (len(lines) == 1) and lines[0].startswith('http'):
            if  not name:
                data['name'] = urlparse(lines[0]).hostname
            else:
                data['name'] = name
            return RTrack(lines[0],data)

        elif len(lines) == 2 and lines[0].startswith(M3UList.xf_rec_marker):
            ltmp = lines[0].split(':')
            dur_title = ltmp[1].split(',')
            data['duration'] = int(dur_title[0])
            if not name:
                data['name'] = dur_title[1]
            else:
                data['name'] = name

            data['email'] = email
            data['site'] = site
            data['info'] = info
            data['type'] = type

            if lines[1].startswith('http'):
                data['url'] = lines[1]
                return RTrack(lines[1],data)
            else:
                app.logger.info('http  url line 2 required for extended m3u element')
                return None
        else:
            app.logger.info('neither one nor two lines -- not an rtrack')
            return None

    @staticmethod
    def read_internet_m3u(fn):

        if fn.endswith('.m3u'):
            with open(fn) as f:
                lines = f.readlines()
                rtracks = []
                header = lines.pop(0).strip()
                if header == M3UList.xf_descriptor:
                    RTrack.process_rtrack_ext_m3u_lines(lines, rtracks)
                    return rtracks


    @staticmethod
    def process_rtrack_ext_m3u_lines(lines:list, rtracks:list):
        if len(lines) == 0:
            return
        else:
            line_0 = lines.pop(0).strip()
            line_1 = lines.pop(0).strip()
            trk = RTrack.RTrackFactory([line_0,line_1], url=line_1)
            rtracks.append(trk)
            RTrack.process_rtrack_ext_m3u_lines(lines,rtracks)


class RM3UPlaylist:
    def __init__(self, fn=None, trks=[], name=None):

        self.filename = fn
        if name:
            self.name = name
        else:
            if fn:
                pp = PurePath(self.filename)
                self.name = pp.stem
            else:
                app.logger.info('no filename, and no name -- cannot create rm3u playlist')
        if trks:
            self.tracks = trks
        self.tracks = RTrack.read_internet_m3u(fn)
        self.duration = -1
        if not self.name:
            raise Exception('RM3UPlaylist requires name')
        if not fn and not trks:
            raise Exception('RM3UList requires either fn or list of rtracks')
        if fn:
            pass

    def num_tracks(self):
        return len(self.tracks)



class  MTrack:

    @staticmethod
    def Mtrack_from_Track(trk):
        from app.models import Track

        if isinstance(Track,trk):
            return MTrack(trk.filename, artist_title=trk.artist_title)
        return None

    """ An internal class modeling an audio track ID3 tags extracted via TinyTag """

    class TAG_ATTRS:
        def __init__(self, tags:TinyTag=None, comp=None, url=None, at=None, fn=None, duration=0):
            if tags:

                self.album = tags.album  # album as string
                self.albumartist=tags.albumartist   # album artist as string
                self.artist=tags.artist  # artist name as string
                self.bitrate=tags.bitrate   # 'int', bitrate in kBits/s
                self.comment=tags.comment  # file comment as string
                self.composer=comp  # composer as string
                self.disc=tags.disc  # 'int',  disc number
                self.disc_total=tags.disc_total   # the total number of discs
                self.duration=tags.duration  # 'int',duration of the song in seconds
                self.filesize=tags.filesize   # 'string',file size in bytes
                self.genre=tags.genre   # 'string', genre as string
                self.samplerate= tags.samplerate  # int samples per second
                self.title= tags.title  # title of the song
                self.track= tags.track  # track number as string
                self.track_total= tags.track_total  # total number of tracks as string
                self.year= tags.year  # year or data as string
                self.url= url   # string from internet link
                self.artist_title=at  # string for m3u ext format track line one.
                self.filename= fn

            else: # create minimal attrs
                self.album = None  # album as string
                self.albumartist = None  # album artist as string
                self.artist = None  # artist name as string
                self.bitrate = None  # 'int', bitrate in kBits/s
                self.comment = None  # file comment as string
                self.composer = comp  # composer as string
                self.disc = 0  # 'int',  disc number
                self.disc_total = None  # the total number of discs
                self.duration = duration  # 'int',duration of the song in seconds
                self.filesize = 0  # 'string',file size in bytes
                self.genre = None  # 'string', genre as string
                self.samplerate = 0  # int samples per second
                self.title =  None # title of the song
                self.track = None  # track number as string
                self.track_total = None  # total number of tracks as string
                self.year =None  # year or data as string
                self.url = url  # string from internet link
                self.artist_title = at  # string for m3u ext format track line one.
                self.filename = fn

    # cols = ['duration', 'artist', 'title', 'file']

    @staticmethod
    def mtrack_factory(fn=None, artist_title=None):
        duration = 0
        tags = None

        if os.path.exists(fn):
            try:
                tags = TinyTag.get(fn)
                if tags:
                    duration = tags.duration
                    if not duration:
                        raise Exception('no duration in {}', format(fn))
                    if not artist_title:
                        if tags.artist:
                            if tags.title:
                                artist_title = tags.artist + ' - ' + tags.title

                            else:
                                artist_title = tags.artist + ' - ' + PurePath(fn).stem
                        else:
                            artist_title =  PurePath(fn).stem

                    return MTrack(duration=duration, fn=fn, artist_title=artist_title, tags=tags)
                else:
                    app.logger.info('no tags for {}'.format(fn))
                    return None
            except Exception as inst:
                print('Tiny Tag: get tags fails for {}: {}'.format(fn,inst))
                return None
                # raise Exception('file {} no tags'.format(fn))
        else:
            print('File {} does not exist or not readable'.format(fn))
            return None

    def __init__(self, duration=0, fn=None, url=None, artist_title=None, tags=None):

        self.duration = int(duration)
        self.url = url
        self.fn = fn
        self.artist_title = artist_title
        self.tags = tags
        if not self.tags:
            raise Exception('No Tags on file {}'.format(self.fn))

        self.tg_attrs = MTrack.TAG_ATTRS(tags, at=self.artist_title,fn=self.fn, url=self.url, duration=self.duration, comp=None)

        self.artist_title = artist_title
        if not self.artist_title:
            raise Exception('no artist_title for {}'.format(self.fn))



    # def generate_avatar(self):
    #     return avatars.default(size="s")

    def set_ID3_tags(self,fn):
         self.tags = TinyTag.get(fn)

    def is_equal(self, mtrk):
        if isinstance(mtrk, MTrack):
            # print('are these titles equal? {} and {}'.format(self.artist_title, mtrk.artist_title))
            # print('are these filenames equal? {} amd {}'.format(self.fn, mtrk.fn))
            if (self.fn == mtrk.fn) or  (self.artist_title == mtrk.artist_title):
                return True
            else:
                return False

    def __str__(self):
        return 'duration:' + str(self.duration) + ', artist_title: ' + str(self.artist_title) + \
               ', file: ' + str(self.fn)

    def get_row(self):
        return [self.duration, self.artist_title, self.fn]

    def get_dict(self):
        return {'duration': self.duration, 'artist_title': self.artist_title, 'file': self.fn}

    def get_ser(self):
        return pd.Series(self.get_dict())

    def get_duration_str(self):
        mins, secs = divmod(self.duration, 60 )
        return '(' + str(mins) + ':' + str(secs) + ')'

    # ###################################################################################
    #                            M3UList Class                                          #
    # ###################################################################################


class M3UList:
    """ A class parsing and modeling the extended m3u playlist file."""

    types = ['EXT', 'SIMPLE']
    xf_descriptor = '#EXTM3U'
    xf_rec_marker = '#EXTINF:'
    xf_desc = '#D:'
    sf_comment = '# '
    http_marker = 'http'
    dirty_dir = Config.M3U_DIRS['dirty']
    clean_dir = Config.M3U_DIRS['clean']

    #  M3UList static methods

    @staticmethod
    def get_lines(f: str):
        # print('getting line from {}'.format(f))

        try:
            with open(f) as m3u:
                return m3u.readlines()
        except Exception:
            print('file {} not opened')
            raise

    @staticmethod
    def get_type(lines: list):
        if lines[0] == M3UList.xf_descriptor:
            return M3UList.types[0]
        else:
            return M3UList.types[1]

    @staticmethod
    def parse_m3ue2(line: str):
        __doc__ = """returns a tuple (path -- relative or absolute [or None if 
            file is in current directory as m3u] ,file)"""

        # print('in parse_m3ue2: ', line)
        if line.startswith('http'):
            return None, line

        else:  # a windows path
            ss = line.split('\\')
            pp = PurePath('\\\\'.join(ss))
            # path = pp.parent
            file = str(pp)
            return None, file

    @staticmethod
    def parse_m3ue1(line: str):
        """ Returns a tuple (duration,title)
            for line one of EXT M3U format. """

        ref, rest = line.split(':', maxsplit=1)
        lss = rest.split(',', maxsplit=1)
        duration = int(lss[0])
        artist_title = lss[1]
        if ' - ' in artist_title:
            artist, title = lss[1].split(' - ', maxsplit=1)
        else:
            if '.mp3' in artist_title:
                title = '.'.join(artist_title.split('.')[0:-1])
                artist = ''
            else:
                title = artist_title
                artist = None
        return duration, artist_title

    @staticmethod
    def parse_m3u_path(line: str):
        __doc__ = ''' From second line in  M#U EXT Format, returns a tuple (path -- 
            relative or absolute [or None if 
            file is in current directory as m3u] ,file or url)'''

        # print('in parse_m3ue2: ', line)
        if line.startswith('http'):
            return None, line

        else:  # a windows path
            ss = line.split('\\')
            pp = PurePath('\\\\'.join(ss))
            # path = pp.parent
            file = str(pp)
            return None, file

    @staticmethod
    def write_m3u(fn, txt):
        w_file = fn
        with open(w_file, "w+") as f:
            f.write(txt)

    @staticmethod
    def shuffle_tracks(m3u_orig): # return a new M3UList,with  shuffled list of MTrack objs
        import copy, random
        """return a new M3UList,with  shuffled list of MTrack objs"""
        ntrks = copy.deepcopy(m3u_orig.tracks)
        random.shuffle(ntrks)
        return M3UList.m3u_clean_factory(tl=ntrks,name=m3u_orig.name)

    @staticmethod
    def m3u_clean_factory(fn=None, st=None, tl=None, name=None, store_lib='prod', nf=True):
        clean=False
        print(' in m3u clean factory: {}'.format(fn))
        if os.path.exists(fn):
            # source is m3u file, check for clean. If dirty,put in clean dir, fresh file.
            if not store_lib:
                store_keys = Config.PLAYLIST_SRC_DIRS.keys()
                print('a recognized storage label is required for m3u file cleaning.')
                print('Recognized labels include: {}'.format(store_keys))
                raise Exception('no store_lib param provided.')

            dpth = PurePath(fn)

            fnc = Config.PLAYLIST_SRC_DIRS[store_lib] + str(dpth.stem) + str(dpth.suffix)
            print('destination file is {}'.format(fnc))
            if not name:
                name = dpth.stem

            m3u = M3UList(m3u_fn=fn,name=name)
            # print('created m3u')
            # print('num tracs after create: {}'.format(len(m3u.tracks)))
            # for t in m3u.tracks:
            #     print(t.artist_title)

            if M3UList.has_duplicates(m3u.tracks[0], m3u.tracks[1:]):
                print('m3u has duplicates')
                no_dup_trks, dup_tracks = M3UList.remove_duplicates(m3u.tracks)
                m3u.tracks = no_dup_trks
                m3u.trk_cnt = len(m3u.tracks)
                m3u.fn = fnc
                m3u.ppth = None
                m3u.lines = None
                m3u.type = None
                m3u.name = name  # name param mandatory with string or list inputs.

                m3u.list_of_trks = [mt.get_row() for mt in m3u.tracks]

                m3u.seconds = int(pd.Series([int(x.duration) for x in m3u.tracks]).sum())
                m3u.duration = M3UList.PlaylistDuration(m3u.seconds, m3u.trk_cnt)

                m3u.description = {'name': m3u.name, 'file_name': m3u.fn,
                                    'total_seconds': m3u.seconds, 'avg_trk': m3u.duration.average_track_duration,
                                    'hours': m3u.duration.hours, 'minutes': m3u.duration.minutes, 'seconds':
                                        m3u.duration.seconds}
                print('num tracks after dups removed: {}'.format(len(m3u.tracks)))
                stat = m3u.has_duplicates(m3u.tracks[0], m3u.tracks[1:])
                print('m3u  has dups now? after remove {}'.format(stat))

            # print('file {} is clean, writing to clean dir,  if needed,  and returning m3u object'.format(m3u.fn))

            if nf:

                txt = m3u.ext_to_m3u(m3u.tracks)
                # write clean file to clean dir
                M3UList.write_m3u(fnc, txt)
                #  remove old file
                # os.remove(m3u.fn)
                m3u.fn = fnc

                return m3u


        elif st:
            if not name:
                raise Exception('M3UList obj initialized from String,or MTrack list,  must have name param')
            else:
                m3u = M3UList(st=st,name=name)
                return m3u

        elif tl: # source is MTrack list
            if not name:
                raise Exception('M3UList obj initialized from String,or MTrack list,  must have name param')
            else:
                return M3UList(tl=tl,name=name)

        else:
            raise Exception(' unknown error, missing params')

    #  instance init

    def __init__(self, m3u_fn=None, st=None, tl=None, name=None):

        # m3u_fn, if not None,  is complete path

        if tl: # this  a list of MTrack objects
            print("this is a list of MTrack objects")
            self.fn = None
            self.ppth = None
            self.lines = None
            self.type = None
            self.name = name  # name param mandatory with string or list inputs.
            self.tracks = tl

            self.list_of_trks = [mt.get_row() for mt in self.tracks]
            self.trk_cnt = len(self.tracks)
            # self.clean = self.is_clean()
            # seconds track durations to minutes in playlist object.
            self.seconds = int(pd.Series([int(x.duration) for x in self.tracks]).sum())
            self.duration = M3UList.PlaylistDuration(self.seconds, self.trk_cnt)

            self.description = {'name': self.name, 'file_name': self.fn,
                                'total_seconds': self.seconds, 'avg_trk': self.duration.average_track_duration,
                                'hours': self.duration.hours, 'minutes': self.duration.minutes, 'seconds':
                                    self.duration.seconds}

        else:

            # print('it\'s a file {}'.format(m3u_fn))

            if st:  # m3u file as string

                # name param mandatory with string or list inputs.
                # save as file in dirty dir

                self.fn = os.getcwd() + '\\pls\\clean\\{name}.m3u'

                with open(self.fn, "w+") as f:
                    f.write(st)

            elif m3u_fn:
                self.fn = m3u_fn

            self.ppth = PurePath(self.fn)

            self.lines = M3UList.get_lines(self.fn)
            self.type = M3UList.get_type(self.lines)
            if self.type == M3UList.types[1]:
                pass
            # self.src = 'LOCAL'
            self.name = name
            if name is None:
                self.name = PurePath(self.fn).stem
            else:
                self.name = name

            self.compact_file()

            self.comments = []
            # self.mt = None
            self.tracks = self.process_lines()
            if self.has_dead():
                print('m3u has dead tracks')
                print('num tracks before scraping dead: {}'.format(len(self.tracks)))
                self.tracks = [x for x in self.tracks if x]
                print('num tracks after dead scrape: {}'.format(len(self.tracks)))

            self.trk_cnt = len(self.tracks)

            # self.clean = self.is_clean()
            # seconds track durations to minutes in playlist object.
            self.seconds = int(pd.Series([int(x.duration) for x in self.tracks]).sum())
            self.duration = M3UList.PlaylistDuration(self.seconds, self.trk_cnt)
            average_track_secs = int(self.seconds / self.trk_cnt)
            mins, secs = divmod(average_track_secs, 60)

            # description: dictionary with name and file_name vals. Also, duration is a dictionary with hours, minutes
            # , seconds keys
            #  avg trk is a list  [avg_mins, avg secs]

            self.description =  {'name': self.name, 'file_name': self.fn ,
                                'total_seconds': self.seconds, 'avg_trk': self.duration.average_track_duration,
                                'hours': self.duration.hours, 'minutes': self.duration.minutes, 'seconds':
                                self.duration.seconds}

    # instance methods

    class PlaylistDuration:
        def __init__(self, secs, trk_cnt):
            self.track_count = trk_cnt
            self.total_seconds = secs
            self.hours, self.remainder = divmod(secs, 3600)
            self.minutes, self.seconds = divmod(self.remainder, 60)
            self.average_track_duration = int(self.total_seconds / self.track_count)

        def get_avg_hrs(self):
            mins,  secs  = divmod(self.average_track_duration , 60)

            return mins, secs

        def __str__(self):
            mystr = f'track count: {self.track_count}, total seconds: {self.total_seconds}, hours: {self.hours}, ' \
                    f'minutes: {self.minutes}, avg_dur: {self.average_track_duration}'
            return mystr

    # def is_clean(self):
    #     dups = True
    #     dead =  True
    #
    #     if (not self.has_duplicates()):
    #             return True
    #     else:
    #         return False

    def has_dead(self):
        for t in self.tracks:
            if not t:
                return True
        return False


    def compact_file(self):

        self.lines = [line for line in self.lines if line != '\n']
        self.lines = [l.strip() for l in self.lines]

    # def get_artists(self):
    #     """ Return list of artists in playlist. """
    #
    #     return set(list(dict.fromkeys([x.artist for x in self.tracks if x.artist])))

    class strTrack:
        def __init__(self,l1=None, l2=None):
            self.line1 = None
            self.line2 = None

    def process_lines(self):
        """ Parse lines of M3U extended Track format . """
        line_count = 0

        # parse m3u #EXTINF lines, 2 per track
        line_trks  = []
        st = M3UList.strTrack()
        for line in self.lines:
            if line == '\n' or line.startswith(M3UList.xf_descriptor):
                continue
            else:
                if line.startswith(M3UList.xf_rec_marker) and (line_count % 2 == 0):  # line 1 in m3u ext track format.
                    st.line1 = line
                    line_count += 1

                else:  # line 2 in m3u ext track format.

                    if (line_count % 2) != 0:

                        st.line2 = line
                        # print('track artist_title',self.mt.artist_title)
                        line_count += 1
                        line_trks.append(st)
                        st = M3UList.strTrack()

                    else:
                        print("Do not recognize: " + line)
                        continue
        trks = []

        for tr in line_trks:

            url = None
            tags = None
            duration, artist_title = M3UList.parse_m3ue1(tr.line1)
            path, file  = M3UList.parse_m3ue2(tr.line2)
            # print('path {} and file {} and duration {} and artist_title {}'.format(path, file, duration, artist_title))
            if path is None and file.startswith('http'):
                url = file
                fn=None
            else:
                if path is not None:
                   fn  = str(path + file)

                else:
                    fn  = file
                    url = None

            # print('process_lines: init MTrack: fn={}, at={}'.format(fn,artist_title))
            # check if file exists
            if os.path.exists(fn):
                trk = MTrack.mtrack_factory(fn=fn, artist_title=artist_title)
                if  trk:
                    trks.append(trk)
                else:
                    app.logger.info('Track from {} in playlist {} is None'.format(fn, self.name))
                    trks.append(None)
                    print('track file {} is None from factory'.format(fn))

            else:
                app.logger.info('file {} in playlist {} does not exist or is unreadable.'.format(fn,self.name))
                trk = None
                print('file {} does not exist or is unreadable.'.format(fn))
                trks.append(trk)
            # except Exception as inst:
            #     print('Create MTrack {} fails with exception: {}'.format(fn, inst))
            #     return None

        return trks

    @staticmethod
    def has_duplicates(trk, trks):
        # print('in has_duplicates: trk is {}, trks[0] is {}'.format(trk.artist_title, trks[0].artist_title))
        # print('num tracks: {}'.format(len(trks)))
        if len(trks) == 1:
            # print('in has_duplicates: trk is {}, trks[0] is {}'.format(trk.artist_title, trks[0].artist_title))
            if trk.is_equal(trks[0]):
                return True
            else:
                return False

        for t in trks:
            if trk.is_equal(t):
                return True
            else:
                return M3UList.has_duplicates(trks[0], trks[1:])

    @staticmethod
    def remove_duplicates(trks, no_dups=[], dups=[]):
        if len(trks) == 1:
            no_dups.append(trks[0])
            return no_dups,dups
        else:
            t = trks[0]
            trs = trks[1:]
            for tr in trs:
                if t.is_equal(tr):
                    dups.append(t)
                    return M3UList.remove_duplicates(trs, no_dups, dups)
            no_dups.append(t)
            return M3UList.remove_duplicates(trs, no_dups, dups)

        # for df in dups:
        #     app.logger.info('track {} is a duplicate in {} playlist'.format(df.artist_title, self.name))

    @staticmethod
    def ext_to_m3u(mlist: list):
        slines = [M3UList.xf_descriptor]
        # insert header
        for trk in mlist:
            artist_title = trk.artist_title

            l1 = M3UList.xf_rec_marker + str(trk.duration) + ',' + artist_title
            # print('line one: ' + l1)
            url_file = trk.fn

            l2 = url_file
            slines.append(l1)
            slines.append(l2)
        return '\n'.join(slines)

    @staticmethod
    def simple_to_m3u(mlist):
        simple_lines = []
        for trk in mlist:
            if trk.url is None:
                simple_lines.append(trk.file)
            else:
                simple_lines.append(trk.url)

        return '\n'.join(simple_lines)

    @staticmethod
    def render_from_template(directory, template_name, **kwargs):
        loader = FileSystemLoader(directory)
        env = Environment(loader=loader)
        template = env.get_template(template_name)
        return template.render(**kwargs)

    def to_html(self):
        import pandas as pd
        cols = ['duration', 'artist_title']
        data = []

        directory = 'c:\\python_apps\\flask_m3u\\app\\templates'

        for trk in self.tracks:
            r = trk.get_row()[0:2]
            data.append(r)

        df = pd.DataFrame(data=data, columns=cols)

        s = M3UList.render_from_template(directory, 'playlist.html',
                                         table=df.to_html(), title=self.name)

        ss = s[9:-16]

        return df, ss, s


class Playlists:

    def convert(n):
        return time.strftime("%H:%M:%S", time.gmtime(n))

        # Driver program

    def __init__(self, clean=True):

        self.clean_dir = Config.M3U_DIRS['clean']
        self.dirty_dir = Config.M3U_DIRS['dirty']

        if not clean:
            arr = os.listdir(self.dirty_dir)
            self.pls = [M3UList.m3u_clean_factory(self.dirty_dir + f) for f in arr]

        else:

            arr = os.listdir(self.clean_dir)
            self.pls = [M3UList.m3u_clean_factory(self.clean_dir + f) for f in arr]

        self.num_lists = len(self.pls)
        self.max_lists = 200
        self.page_max = 20
        ser = pd.Series([x.duration for x in self.pls])
        self.total_duration = ser.sum()
        self.pretty_duration = Playlists.convert(self.total_duration)
        self.mean_duration = Playlists.convert(ser.mean())
        self.std_deviation = Playlists.convert(ser.std())


class Utils:


    @staticmethod
    def test_db_add():
        from app import db
        from app.models import Track
        fn = os.getcwd() + '\\pls\\clean\\al kooper.m3u'
        m3u = M3UList.m3u_clean_factory(fn,name='Al Kooper')
        mtrks = m3u.tracks
        print('mum mtracks: ', len(mtrks))
        Track.add_tracks(mtrks)
        print('printing db Track table')
        tz = Track.query.all()
        print('num db tracks: ', len(tz))
        for t in tz:
            print(t.artist_title)

    @staticmethod
    def test_db_delete():
        from app import db
        from app.models import Track

#         find all
        try:
            trks = Track.query.all()
            for trk in trks:
                db.session.delete(trk)
            db.session.commit()
        except Exception as inst:
            print('Error deleting tracks: {}'.format(inst))







