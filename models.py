from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestampdate = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    note_type = db.Column(db.String(20), nullable=False, default='text')
    note_content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.String(100), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('notes', lazy=True))

    def __repr__(self):
        return f"Note('{self.note_content}')"

class User(UserMixin, db.Model):
    id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    profile_pic = db.Column(db.String(100), nullable=False)

    @staticmethod
    def get(user_id):
        user = User.query.get(user_id)
        if not user:
            return None
        return user

    @staticmethod
    def create(id_, name, email, profile_pic):
        user = User(id=id_, name=name, email=email, profile_pic=profile_pic)
        db.session.add(user)
        db.session.commit()
