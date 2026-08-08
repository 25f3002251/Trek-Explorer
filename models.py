from flask_sqlalchemy import SQLAlchemy
db=SQLAlchemy()

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(100),unique=True,nullable=False)
    password=db.Column(db.String(255),nullable=False)
    role=db.Column(db.String(20),nullable=False)
    approved=db.Column(db.Boolean,default=False)
    blacklisted=db.Column(db.Boolean,default=False)

class Trek(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    location=db.Column(db.String(100),nullable=False)
    difficulty=db.Column(db.String(20),nullable=False)
    duration=db.Column(db.Integer,nullable=False)
    available_slots=db.Column(db.Integer,nullable=False)
    status=db.Column(db.String(20),nullable=False)
    start_date=db.Column(db.Date)
    end_date=db.Column(db.Date)
    staff_id=db.Column(db.Integer, db.ForeignKey("user.id"))

class Booking(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("user.id"))
    trek_id=db.Column(db.Integer, db.ForeignKey("trek.id"))
    booking_date=db.Column(db.Date)
    status=db.Column(db.String(20))
    