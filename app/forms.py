from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, HiddenField, FieldList, FormField, IntegerField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length
from app.models import User, Track

from wtforms.form import Form
from wtforms.fields import FieldList, FormField, IntegerField, BooleanField, StringField


from bs4 import BeautifulSoup


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditTrackForm(FlaskForm):
        id = HiddenField('track_id', validators=[DataRequired()])
        album = StringField('Album')
        albumartist = StringField('Album Artist')
        artist = StringField('Artist')
        comment = TextAreaField('Comment', validators=[Length(min=0, max=140)])
        composer = StringField('Composer')
        genre = StringField('Genre')
        title = StringField('Title')
        submit = SubmitField('Update')


    #               tag_attrs = {'album': 'string',  # album as string
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

#  test grid form


class SingleTestForm(FlaskForm):
    string1 = StringField('string', validators=[DataRequired()])
    selectField = SelectField(
        'Are you Happy?',
        choices=[('1', 'Yes'), ('2', 'No')],
        validators=[DataRequired()]
    )


class MultiTestForm(FlaskForm):
    name = StringField('name', render_kw={'readonly': True})
    memories = FieldList(FormField(SingleTestForm), min_entries=2)
    submit = SubmitField('Submit')



class InputGridRecordForm(FlaskForm):
    """A form for entering inputgrid record row data"""
    tid = IntegerField('Track ID', render_kw={'readonly': True})
    select = BooleanField('Add to Playlist', validators=[DataRequired(),])
    # artist_title = StringField('Artist - Title', render_kw={'readonly': True})
    # duration = IntegerField('duration', render_kw={'readonly': True})


class InputGridTableForm(FlaskForm):
    """A form for one or more InputGridRecords"""
    gridtblrecords = FieldList(FormField(InputGridRecordForm), min_entries=1)
    submit = SubmitField('Add selected  to Playlist')