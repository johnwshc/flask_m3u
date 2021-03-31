from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Command, Server, Shell
from flask_migrate import Migrate, MigrateCommand
from app import app
from app.m3u import M3UList, Playlists, MTrack, Utils
from app.models import User, Track, Playlist
from app.models import Track
from app import models
from app import db
from config import Config
from flask_alchemydumps import AlchemyDumps

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

manager.add_command("runserver", Server())


# manager.add_command('alchemydumps', AlchemyDumps)

class Hello(Command):
    """prints hello world"""

    def run(self):
        print ("hello world")

manager.add_command('hello', Hello)

@manager.command
def db_add_dir(dir):
    print(dir)
    trk_files = Config.dir_to_filelist(dir)
    # mtrks = Config.ffiles_to_tracks(trk_files)
    #
    # try:
    #      Track.add_tracks(mtrks)
    # except Exception as inst:
    #     print(inst)

    for t in trk_files:
        print(t)

if __name__ == '__main__':
    manager.run()


    # $ python manage.py --help
    # usage: manage.py [-h] {shell,db,runserver} ...
    #
    # positional arguments:
    #   {shell,db,runserver}
    #     shell               Runs a Python shell inside Flask application context.
    #     db                  Perform database migrations
    #     runserver           Runs the Flask development server i.e. app.run()
    #
    # optional arguments:
    #   -h, --help            show this help message and exit

    #  python manage.py db --help
    # usage: Perform database migrations

    # positional arguments:
    #   {upgrade,migrate,current,stamp,init,downgrade,history,revision}
    #     upgrade             Upgrade to a later version
    #     migrate             Alias for 'revision --autogenerate'
    #     current             Display the current revision for each database.
    #     stamp               'stamp' the revision table with the given revision;
    #                         dont run any migrations
    #     init                Generates a new migration
    #     downgrade           Revert to a previous version
    #     history             List changeset scripts in chronological order.
    #     revision            Create a new revision file.
    #
    # optional arguments:
    #   -h, --help            show this help message and exit
