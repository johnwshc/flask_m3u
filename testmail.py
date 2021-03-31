from flask_mail import Message
from app import mail
from config import Config



msg = Message('test subject', sender=Config.ADMINS[0], recipients=['your-email@example.com'])
msg.body = 'text body'
msg.html = '<h1>HTML body</h1>'
mail.send(msg)