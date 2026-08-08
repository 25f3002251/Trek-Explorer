from flask import Flask, render_template, request, redirect, session
from models import db, User, Trek, Booking
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
from sqlalchemy import or_
app = Flask(__name__)
app.secret_key="trekking_app_2026"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trekking.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
def create_admin():
    admin = User.query.filter_by(role="admin").first()
    if admin is None:
        admin = User(
            name="Administrator",
            email="admin@trek.com",
            password=generate_password_hash("admin123"),
            role="admin",
            approved=True,
            blacklisted=False
        )
        db.session.add(admin)
        db.session.commit()
        
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    email = request.form["email"]
    password = request.form["password"]
    user=User.query.filter_by(email=email).first()
    if user is None:
        return render_template("login.html",error="Invalid email or password")
    if check_password_hash(user.password,password):
        if user.blacklisted:
            return render_template("login.html",error="Your account has been blacklisted.")
        if user.role == "staff" and not user.approved:
            return render_template("login.html",error="Your account is awaiting admin approval.")
        session["user_id"]=user.id
        session["role"]=user.role
        if user.role == "admin":
            return redirect("/admin")
        elif user.role == "staff":
            return redirect("/staff")
        return redirect("/user")
    return render_template("login.html",error="Invalid email or password")

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role=request.form["role"]
        if role == "user":
            approved = True
        else:
            approved = False
        user = User(name=name,
                    email=email,
                    password=generate_password_hash(password),
                    role=role,
                    approved=approved,
                    blacklisted=False
                )
        existing_user=User.query.filter_by(email=email).first()
        if existing_user:
            return render_template("register.html",error="Email already registered.")
        db.session.add(user)
        db.session.commit()
        if role=="staff":
            return render_template("login.html",message ="Registration successful. Your account is awaiting admin approval.")
        return render_template("login.html",message="Registration successful. Please log in.")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "admin":
        return "Access Denied"
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role="user").count()
    total_staff = User.query.filter_by(role="staff").count()
    total_bookings = Booking.query.count()
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
    users = {}
    treks = {}
    for booking in recent_bookings:
        users[booking.user_id] = User.query.get(booking.user_id)
        treks[booking.trek_id] = Trek.query.get(booking.trek_id)
    return render_template("admin_dashboard.html",total_treks=total_treks,total_users=total_users,total_staff=total_staff,total_bookings=total_bookings,recent_bookings=recent_bookings,users=users,treks=treks)

@app.route("/admin/add_trek",methods=["GET","POST"])
def add_trek():
    if "user_id" not in session : 
        return redirect("/login")
    if session["role"]!="admin":
        return "Access Denied"
    if request.method == "POST":
        start_date=datetime.strptime(request.form["start_date"],"%Y-%m-%d").date()
        duration=int(request.form["duration"])
        end_date = start_date + timedelta(days=duration-1)
        trek=Trek(
            name=request.form["name"],
            location=request.form["location"],
            difficulty=request.form["difficulty"],
            duration=duration,
            available_slots=int(request.form["slots"]),
            start_date=start_date,
            end_date=end_date,
            status=request.form["status"]
        )
        db.session.add(trek)
        db.session.commit()
        return redirect("/admin")
    return render_template("add_trek.html")

@app.route("/admin/treks")
def view_treks():
    if "user_id" not in session:
        return redirect("login")
    if session["role"]!="admin":
        return "Access Denied"
    search = request.args.get("search","").strip()
    if search == "":
        treks=Trek.query.all()
    else:
        treks = Trek.query.filter(or_(Trek.name.ilike(f"%{search}%"),Trek.location.ilike(f"%{search}%"),Trek.difficulty.ilike(f"%{search}%"),Trek.status.ilike(f"%{search}%"))).all()
    return render_template("view_treks.html",treks=treks)

@app.route("/admin/edit_trek/<int:trek_id>",methods=["GET","POSt"])
def edit_trek(trek_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "admin":
        return "Access Denied"
    trek = Trek.query.get(trek_id)
    if trek is None:
        return render_template("error.html",message="Trek Not Found",back_url="/admin/treks")
    if request.method == "POST":
        trek.name = request.form["name"]
        trek.location = request.form["location"]
        trek.difficulty = request.form["difficulty"]
        trek.status = request.form["status"]
        duration = int(request.form["duration"])
        trek.available_slots = int(request.form["slots"])
        start_date=datetime.strptime(request.form["start_date"],"%Y-%m-%d").date()
        end_date = start_date + timedelta(days=duration-1)
        if trek.staff_id is not None:
            assigned_treks = Trek.query.filter_by(staff_id=trek.staff_id).all()
            for other_trek in assigned_treks:
                if other_trek.id==trek.id:
                    continue
                if(other_trek.start_date <= end_date and other_trek.end_date >= start_date):
                    return render_template("error.html",message="The staff member currently assigned is already assigned to another trek during those dates.",back_url=f"/admin/edit_trek/{trek.id}")
        trek.duration=duration
        trek.start_date=start_date
        trek.end_date=end_date
        db.session.commit()
        return redirect("/admin/treks")
    return render_template("edit_trek.html",trek=trek)

@app.route("/admin/delete_trek/<int:trek_id>",methods=["GET","POST"])
def delete_trek(trek_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "admin":
        return "Access Denied"
    trek = Trek.query.get(trek_id)
    if trek is None:
        return render_template("error.html",message="Trek not found",back_url="/admin/treks")
    if request.method == "POST":
        db.session.delete(trek)
        db.session.commit()
        return redirect("/admin/treks")
    return render_template("delete_trek.html",trek=trek)

@app.route("/admin/assign_staff/<int:trek_id>",methods=["GET","POST"])
def assign_staff(trek_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "admin":
        return "Access Denied"
    trek = Trek.query.get(trek_id)
    if trek is None:
        return render_template("error.html",message="Trek not found",back_url="/admin/treks")
    staff_members = User.query.filter_by(role="staff",approved=True,blacklisted=False).all()
    if trek.staff_id == None:
        current_staff = None
        current_mail = None
    else:
        current = User.query.filter_by(id=trek.staff_id).first()
        current_staff = current.name
        current_mail = current.email
    if request.method == "POST":
        staff = request.form["staff"]
        if staff == "":
            trek.staff_id = None
            db.session.commit()
            return redirect("/admin/treks")
        else:
            staff_id=int(staff)
            assigned_treks = Trek.query.filter_by(staff_id=staff_id).all()
            for other_trek in assigned_treks:
                if other_trek.id == trek.id:
                    continue
                if(other_trek.start_date <= trek.end_date and other_trek.end_date >= trek.start_date):
                    return render_template("error.html",message="This staff member is already assigned to another trek during those dates.",back_url=f"/admin/assign_staff/{trek.id}")
            trek.staff_id=staff_id
            db.session.commit()
            return redirect("/admin/treks")     
                     
    return render_template("assign_staff.html",trek=trek,staff_members=staff_members,current_staff=current_staff,current_mail=current_mail)

@app.route("/admin/pending_staff")
def pending_staff():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"]!="admin":
        return "Access Denied"
    status = request.args.get("status","pending")
    search = request.args.get("search", "").strip()
    if status == "pending":
        staff_members = User.query.filter_by(role="staff",approved=False,blacklisted=False).all()
    elif status == "approved":
        staff_members = User.query.filter_by(role="staff",approved=True,blacklisted=False).all()
    elif status == "blacklisted":
        staff_members = User.query.filter_by(role="staff",blacklisted=True).all()
    else:
        staff_members = []
    if search:
        staff_members = [staff for staff in staff_members if search.lower() in staff.name.lower() or search.lower() in staff.email.lower()]
    pending_count=User.query.filter_by(role="staff",approved=False,blacklisted=False).count()
    approved_count=User.query.filter_by(role="staff",approved=True,blacklisted=False).count()
    blacklisted_count=User.query.filter_by(role="staff",blacklisted=True).count()
    return render_template("pending_staff.html",staff=staff_members,search=search,status=status,pending_count=pending_count,approved_count=approved_count,blacklisted_count=blacklisted_count)

@app.route("/admin/history")
def admin_history():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "admin":
        return "Access Denied"
    treks = Trek.query.filter_by(status="Completed").all()
    staff = {}
    participant_count = {}
    for trek in treks:
        if trek.staff_id:
            staff[trek.id] = User.query.get(trek.staff_id)
            participant_count[trek.id] = Booking.query.filter_by(trek_id=trek.id,status="Completed").count()
    return render_template("admin_history.html",treks=treks,staff=staff,participant_count=participant_count)

@app.route("/admin/history/<int:trek_id>")
def admin_history_trek(trek_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "admin":
        return "Access Denied"
    trek = Trek.query.get(trek_id)
    if trek is None:
        return render_template("error.html",message="Trek not found.",back_url="/admin/history")
    staff = None
    if trek.staff_id:
        staff = User.query.get(trek.staff_id)
    bookings = Booking.query.filter_by(trek_id=trek.id,status="Completed").all()
    users = {}
    for booking in bookings:
        users[booking.user_id] = User.query.get(booking.user_id)
    bookcount=len(bookings)
    return render_template("admin_history_trek.html",trek=trek,staff=staff,bookings=bookings,users=users,bookcount=bookcount)

@app.route("/admin/approve_staff/<int:user_id>")
def approve_staff(user_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"]!="admin":
        return "Access Denied"
    staff = User.query.get(user_id)
    if staff is None:
        return render_template("error.html",message="Staff member not found",back_url="/admin/pending_staff")
    if staff.role != "staff":
        return render_template("error.html",message="Invalid User",back_url="/admin/pending_staff")
    if staff.approved:
        return render_template("error.html",message="Staff member is already approved",back_url="/admin/pending_staff")
    staff.approved = True
    db.session.commit()
    return redirect("/admin/pending_staff")

@app.route("/admin/reject_staff/<int:user_id>",methods=["GET","POST"])
def reject_staff(user_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "admin":
        return "Access Denied"
    staff = User.query.get(user_id)
    if staff is None:
        return render_template("error.html",message="Staff member not found",back_url="/admin/pending_staff")
    if staff.role != "staff":
        return render_template("error.html",message="Invalid User",back_url="/admin/pending_staff")
    if staff.approved:
        return render_template("error.html",message="Approved staff cannot be rejected",back_url="/admin/pending_staff")
    if request.method == "POST":
        db.session.delete(staff)
        db.session.commit()
        return redirect("/admin/pending_staff")
    return render_template("reject_staff.html",staff=staff)

@app.route("/admin/blacklist_staff/<int:user_id>",methods=["GET","POST"])
def blacklist_staff(user_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"]!="admin":
        return "Access Denied"
    staff = User.query.get(user_id)
    assigned = Trek.query.filter_by(staff_id=staff.id).first()
    if staff is None:
        return render_template("error.html",message="Staff member not found",back_url="/admin/pending_staff?status=approved")
    if staff.role != "staff":
        return render_template("error.html",message="Invalid User",back_url="/admin/pending_staff?status=approved")
    if staff.blacklisted:
        return render_template("error.html",message="Staff member is already blacklisted",back_url="/admin/pending_staff?status=approved")
    if assigned:
        return render_template("error.html",message="This staff member is currently assigned to a trek. Remove them from the trek first to blacklist.",back_url="/admin/pending_staff?status=approved")
    if request.method == "POST":
        staff.blacklisted=True
        db.session.commit()
        return redirect("/admin/pending_staff?status=approved")
    return render_template("blacklist_staff.html",staff=staff,blacklist=True)

@app.route("/admin/unblacklist_staff/<int:user_id>",methods=["GET","POST"])
def unblacklist_staff(user_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"]!="admin":
        return "Access Denied"
    staff = User.query.get(user_id)
    if staff is None:
        return render_template("error.html",message="Staff member not found",back_url="/admin/pending_staff?status=blacklisted")
    if staff.role != "staff":
        return render_template("error.html",message="Invalid User",back_url="/admin/pending_staff?status=blacklisted")
    if not staff.blacklisted:
        return render_template("error.html",message="Staff member is not blacklisted",back_url="/admin/pending_staff?status=blacklisted")
    if request.method == "POST":
        staff.blacklisted=False
        db.session.commit()
        return redirect("/admin/pending_staff?status=blacklisted")
    return render_template("blacklist_staff.html",staff=staff,blacklist=False)

@app.route("/admin/users")
def admin_users():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "admin":
        return "Access Denied"
    search = request.args.get("search", "").strip()
    users = User.query.filter_by(role="user").all()
    if search:
        users = [user for user in users if search.lower() in user.name.lower() or search.lower() in user.email.lower()]
    return render_template("admin_users.html",users=users,search=search)

@app.route("/admin/toggle_user/<int:user_id>")
def toggle_user(user_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "admin":
        return "Access Denied"
    user = User.query.get(user_id)
    if user is None:
        return render_template("error.html",message="User not found.",back_url="/admin/users")
    if user.role != "user":
        return render_template("error.html",message="Invalid user.",back_url="/admin/users")
    user.blacklisted = not user.blacklisted
    db.session.commit()
    return redirect("/admin/users")

@app.route("/staff")
def staff_dashboard():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"]!="staff":
        return "Access Denied"
    staff_id = session["user_id"]
    treks=Trek.query.filter_by(staff_id=staff_id).all()
    assigned_treks=len(treks)
    open_treks=Trek.query.filter_by(staff_id=staff_id,status="Open").count()
    total_participants=0
    participant_count={}
    for trek in treks:
        count = Booking.query.filter(Booking.trek_id == trek.id,Booking.status.in_(["Booked", "Completed"])).count()
        total_participants += count
        participant_count[trek.id]=count
    return render_template("staff_dashboard.html",treks=treks,assigned_treks=assigned_treks,open_treks=open_treks,total_participants=total_participants,participant_count=participant_count)

@app.route("/staff/trek/<int:trek_id>")
def staff_trek(trek_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"]!="staff":
        return "Access Denied"
    trek=Trek.query.get(trek_id)
    if trek is None:
        return render_template("error.html",message="Trek not found",back_url="/staff")
    if trek.staff_id != session["user_id"]:
        return render_template("error.html",message="You are not assigned to this trek.",back_url="/staff")
    staff = User.query.get(trek.staff_id)
    bookings = Booking.query.filter(Booking.trek_id == trek.id,Booking.status.in_(["Booked", "Completed"])).all()
    users={}
    for booking in bookings:
        users[booking.user_id]=User.query.get(booking.user_id)
    participant_count=len(bookings)
    available = (trek.available_slots)-(participant_count)
    bookings = bookings[:5]
    return render_template("staff_trek.html",trek=trek,staff=staff,bookings=bookings,available=available,participant_count=participant_count,users=users)

@app.route("/staff/start_trek/<int:trek_id>")
def start_trek(trek_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"]!="staff":
        return "Access Denied"
    trek=Trek.query.get(trek_id)
    if trek is None:
        return render_template("error.html",message="Trek not found",back_url="/staff")
    if trek.staff_id != session["user_id"]:
        return render_template("error.html",message="You are not assigned to this trek.",back_url="/staff")
    if trek.status not in ["Open","Full"]:
        return render_template("error.html",message="This trek has already started or has been completed.",back_url=f"/staff/trek/{trek.id}")
    today=date.today()
    if today < trek.start_date:
        return render_template("error.html",message="This trek cannot be started before its start date.",back_url=f"/staff/trek/{trek.id}")
    if today > trek.end_date:
        return render_template("error.html",message="This trek has already passed its end date.",back_url=f"/staff/trek/{trek.id}")
    trek.status = "Ongoing"
    db.session.commit()
    return redirect(f"/staff/trek/{trek.id}")

@app.route("/staff/complete_trek/<int:trek_id>")
def complete_trek(trek_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"]!="staff":
        return "Access Denied"
    trek=Trek.query.get(trek_id)
    if trek is None:
        return render_template("error.html",message="Trek not found",back_url="/staff")
    if trek.staff_id != session["user_id"]:
        return render_template("error.html",message="You are not assigned to this trek.",back_url="/staff")
    if trek.status not in ["Ongoing","Open","Full"]:
        return render_template("error.html",message="This trek cant be marked as completed.",back_url=f"/staff/trek/{trek.id}")
    today=date.today()
    if today < trek.end_date:
        return render_template("error.html",message="This trek cannot be completed before its end date.",back_url=f"/staff/trek/{trek.id}")
    trek.status = "Completed"
    bookings=Booking.query.filter_by(trek_id=trek.id,status="Booked").all()
    for booking in bookings:
        booking.status="Completed"
    db.session.commit()
    return redirect(f"/staff/trek/{trek.id}")

@app.route("/staff/trek/<int:trek_id>/participants")
def staff_participants(trek_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"]!="staff":
        return "Access Denied"
    trek=Trek.query.get(trek_id)
    if trek is None:
        return render_template("error.html",message="Trek not found",back_url="/staff")
    if trek.staff_id != session["user_id"]:
        return render_template("error.html",message="You are not assigned to this trek.",back_url="/staff")
    bookings = Booking.query.filter(Booking.trek_id == trek.id,Booking.status.in_(["Booked", "Completed"])).all()
    users={}
    for booking in bookings:
        users[booking.user_id]=User.query.get(booking.user_id)
    return render_template("staff_participants.html",trek=trek,bookings=bookings,users=users)
    
@app.route("/user")
def user_dashboard():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "user":
        return "Access Denied"
    user = User.query.get(session["user_id"])
    location = request.args.get("location", "").strip()
    difficulty = request.args.get("difficulty", "")
    available_treks = Trek.query.filter_by(status="Open").all()
    if location:
        available_treks = [trek for trek in available_treks if location.lower() in trek.location.lower()]
    if difficulty:
        available_treks = [trek for trek in available_treks if trek.difficulty == difficulty]
    blocked_trek_ids = [booking.trek_id for booking in Booking.query.filter_by(user_id=session["user_id"]).all() if booking.status in ["Booked", "Completed"]]
    available_treks = [trek for trek in available_treks if trek.id not in blocked_trek_ids]
    my_bookings = Booking.query.filter_by(user_id=session["user_id"]).all()
    my_bookings = [booking for booking in my_bookings if booking.status == "Booked"]
    available_preview = available_treks[:5]
    booking_preview = my_bookings[:5]
    available_slots = {}
    for trek in available_preview:
        booked = Booking.query.filter_by(trek_id=trek.id,status="Booked").count()
        available_slots[trek.id] = trek.available_slots - booked
    treks = {}
    for booking in booking_preview:
        treks[booking.trek_id] = Trek.query.get(booking.trek_id)
    return render_template("user_dashboard.html",user=user,location=location,difficulty=difficulty,available_treks=available_preview,my_bookings=booking_preview,available_slots=available_slots,treks=treks)

@app.route("/user/treks")
def browse_treks():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"]!="user":
        return "Access Denied"
    location = request.args.get("location","").strip()
    difficulty = request.args.get("difficulty","")
    available_treks = Trek.query.filter_by(status="Open").all()
    blocked_trek_ids = [booking.trek_id for booking in Booking.query.filter_by(user_id=session["user_id"]).all() if booking.status in ["Booked", "Completed"]]
    available_treks = [trek for trek in available_treks if trek.id not in blocked_trek_ids]
    if location:
        available_treks = [trek for trek in available_treks if location.lower() in trek.location.lower()]
    if difficulty:
        available_treks = [trek for trek in available_treks if trek.difficulty == difficulty]
    available_slots = {}
    for trek in available_treks:
        booked = Booking.query.filter_by(trek_id=trek.id,status="Booked").count()
        available_slots[trek.id] = (trek.available_slots - booked)
    return render_template("user_treks.html",available_treks=available_treks,available_slots=available_slots,location=location,difficulty=difficulty)

@app.route("/user/trek/<int:trek_id>")
def user_trek(trek_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"]!="user":
        return "Access Denied"
    trek = Trek.query.get(trek_id)
    if trek is None:
        return render_template("error.html",message="Trek not found.",back_url="/user")
    if trek.staff_id is not None:
        staff = User.query.get(trek.staff_id)
    else:
        staff = None
    booked = Booking.query.filter_by(trek_id=trek.id,status="Booked").count()
    available_slots = trek.available_slots - booked
    booking = Booking.query.filter_by(user_id=session["user_id"],trek_id=trek.id,status="Booked").first()
    if booking is None:
        booking = Booking.query.filter_by(user_id=session["user_id"],trek_id=trek.id,status="Completed").first()
    if booking is None:
        booking = Booking.query.filter_by(user_id=session["user_id"],trek_id=trek.id,status="Cancelled").first()
    percentage = 0
    if trek.available_slots > 0:
        percentage = (booked / trek.available_slots) * 100
    return render_template("user_trek_details.html",booked=booked,trek=trek,staff=staff,available_slots=available_slots,booking=booking,percentage=percentage)

@app.route("/user/book/<int:trek_id>", methods=["POST"])
def book_trek(trek_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "user":
        return "Access Denied"
    trek = Trek.query.get(trek_id)
    if trek is None:
        return render_template("error.html",message="Trek not found.",back_url="/user")
    if trek.status != "Open":
        return render_template("error.html",message="This trek is not open for booking.",back_url=f"/user/trek/{trek.id}")
    if trek.staff_id is None:
        return render_template("error.html",message="No staff member has been assigned to this trek yet.",back_url=f"/user/trek/{trek.id}")
    existing_booking = Booking.query.filter_by(user_id=session["user_id"],trek_id=trek.id).first()
    if existing_booking is not None: 
        if existing_booking.status == "Booked":
            return render_template("error.html",message="You have already booked this trek.",back_url=f"/user/trek/{trek.id}")
        elif existing_booking.status == "Completed":
            return render_template("error.html",message="You have already completed this trek.",back_url=f"/user/trek/{trek.id}")
        elif existing_booking.status == "Cancelled":
            existing_booking.status = "Booked"
            existing_booking.booking_date = date.today()
            db.session.flush()
            booked = Booking.query.filter_by(trek_id=trek.id,status="Booked").count()
            if booked >= trek.available_slots:
                    trek.status = "Full"
            db.session.commit()
            return redirect(f"/user/trek/{trek.id}")
    booked = Booking.query.filter_by(trek_id=trek.id,status="Booked").count()
    if booked >= trek.available_slots:
        trek.status = "Full"
        db.session.commit()
        return render_template("error.html",message="Sorry, this trek is already full.",back_url="/user")
    booking = Booking( user_id=session["user_id"],trek_id=trek.id,booking_date=date.today(),status="Booked")
    db.session.add(booking)
    db.session.commit()
    booked = Booking.query.filter_by(trek_id=trek.id,status="Booked").count()
    if booked >= trek.available_slots:
        trek.status = "Full"
    db.session.commit()
    return redirect(f"/user/trek/{trek.id}")

@app.route("/user/cancel/<int:booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "user":
        return "Access Denied"
    booking = Booking.query.get(booking_id)
    if booking is None:
        return render_template("error.html",message="Booking not found.",back_url="/user")
    if booking.user_id != session["user_id"]:
        return render_template("error.html",message="You cannot cancel someone else's booking.",back_url="/user")
    if booking.status != "Booked":
        return render_template("error.html",message="This booking cannot be cancelled.",back_url=f"/user/trek/{booking.trek_id}")
    trek = Trek.query.get(booking.trek_id)
    if trek.start_date <= date.today():
        return render_template("error.html",message="Bookings cannot be cancelled after the trek has started.",back_url=f"/user/trek/{trek.id}")
    booking.status = "Cancelled"
    if trek.status == "Full":
        trek.status = "Open"
    db.session.commit()
    return redirect(f"/user/trek/{trek.id}")

@app.route("/user/bookings")
def user_bookings():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "user":
        return "Access Denied"
    bookings = Booking.query.filter_by(user_id=session["user_id"]).all()
    bookings = [booking for booking in bookings if booking.status == "Booked"]
    treks = {}
    for booking in bookings:
        treks[booking.trek_id] = Trek.query.get(booking.trek_id)
    return render_template("user_bookings.html",bookings=bookings,treks=treks)

@app.route("/user/history")
def user_history():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "user":
        return "Access Denied"
    history = Booking.query.filter_by(user_id=session["user_id"],status="Completed").all()
    treks = {}
    for booking in history:
        treks[booking.trek_id] = Trek.query.get(booking.trek_id)
    return render_template("user_history.html",history=history,treks=treks)

@app.route("/admin/bookings")
def admin_bookings():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "admin":
        return "Access Denied"
    status = request.args.get("status", "")
    bookings = Booking.query.all()
    if status != "":
        bookings = [booking for booking in bookings if booking.status == status]
    users = {}
    treks = {}
    for booking in bookings:
        users[booking.user_id] = User.query.get(booking.user_id)
        treks[booking.trek_id] = Trek.query.get(booking.trek_id)
    return render_template("admin_bookings.html",bookings=bookings,users=users,treks=treks,status=status)

@app.route("/user/profile", methods=["GET", "POST"])
def user_profile():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "user":
        return "Access Denied"
    user = User.query.get(session["user_id"])
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        existing = User.query.filter_by(email=email).first()
        if existing is not None and existing.id != user.id:
            return render_template("user_profile.html",user=user,error="Email is already registered.")
        user.name = name
        user.email = email
        if password != "":
            user.password = generate_password_hash(password)
        db.session.commit()
        return render_template("user_profile.html",user=user,success="Profile updated successfully.")
    return render_template("user_profile.html", user=user)

if __name__ == "__main__" :
    with app.app_context():
        db.create_all()
        create_admin()
    app.run()
