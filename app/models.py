from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    event = db.Column(db.String(200))
    level = db.Column(db.Integer)
    place = db.Column(db.Integer)
    quality = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='projects')

    def __repr__(self):
        return f'<Project {self.name}>'

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', back_populates='group', lazy='dynamic')

    def __repr__(self):
        return f'<Group {self.name}>'

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(300), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False, default='student')
    points = db.Column(db.Integer, default=0)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    is_confirmed =  db.Column(db.Boolean, default=True)

    projects = db.relationship('Project', back_populates='user', lazy='dynamic')

    group = db.relationship('Group', back_populates='users')
    competitions = db.relationship('Competition', back_populates='user', lazy=True, foreign_keys='Competition.user_id')
    weekly_performances = db.relationship('WeeklyPerformance', back_populates='user', lazy=True)
    yearly_performances = db.relationship('YearlyPerformance', back_populates='user', lazy=True)
    transactions = db.relationship('Transaction', back_populates='user', lazy='dynamic', foreign_keys='Transaction.user_id')
    awarded_transactions = db.relationship('Transaction', back_populates='awarded_by', lazy='dynamic', foreign_keys='Transaction.awarded_by_id')
    awarded_competitions = db.relationship('Competition', back_populates='awarded_by', lazy='dynamic', foreign_keys='Competition.awarded_by_id')

    def __repr__(self):
        return f'<User {self.full_name}>'

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    awarded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment = db.Column(db.String(200))

    user = db.relationship("User", back_populates="transactions", foreign_keys=[user_id])
    awarded_by = db.relationship("User", back_populates="awarded_transactions", foreign_keys=[awarded_by_id])

    def __repr__(self):
        return f'<Transaction {self.id}>'

class Competition(db.Model):
    __tablename__ = 'competitions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    level = db.Column(db.Integer)
    project_quality = db.Column(db.Integer)
    place = db.Column(db.Integer)
    communication = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    awarded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="competitions", foreign_keys=[user_id])
    awarded_by = db.relationship("User", back_populates="awarded_competitions", foreign_keys=[awarded_by_id])

    def __repr__(self):
        return f'<Competition {self.name}>'

class WeeklyPerformance(db.Model):
    __tablename__ = 'weekly_performances'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    week = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    week_start = db.Column(db.Date, nullable=False)  # Добавьте эту строку
    academic_performance = db.Column(db.Integer, default=0)
    mentoring = db.Column(db.Integer, default=0)
    teamwork = db.Column(db.Integer, default=0)
    discipline = db.Column(db.Integer, default=0)

    user = db.relationship("User", back_populates="weekly_performances", foreign_keys=[user_id])

    def __repr__(self):
        return f'<WeeklyPerformance {self.id}>'

class YearlyPerformance(db.Model):
    __tablename__ = 'yearly_performances'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)

    user = db.relationship("User", back_populates="yearly_performances", foreign_keys=[user_id])

    def __repr__(self):
        return f'<YearlyPerformance {self.id}>'
    

    