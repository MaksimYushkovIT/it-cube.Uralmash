from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user, current_user
from app import db
from app.models import User, Group, Transaction, WeeklyPerformance, Project
from werkzeug.security import check_password_hash
from sqlalchemy import func, desc
from datetime import datetime, timedelta

bp = Blueprint('main', __name__)

# Ваши маршруты

@bp.route('/')
def home():
    return redirect(url_for('main.login'))

@bp.route("/register", methods=["GET", "POST"])
def register():
    groups = Group.query.all()
    if request.method == "POST":
        username = request.form["username"]
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        
        group_id = request.form.get("group_id") if role == "student" else None

        # Хеширование пароля с использованием werkzeug.security
        hashed_password = generate_password_hash(password)

        is_confirmed = True if role == "student" else False

        user = User(username=username, full_name=full_name, email=email, password_hash=hashed_password, role=role, is_confirmed=is_confirmed)
        
        if role == "student" and group_id:
            user.group_id = group_id

        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна. Теперь вы можете войти.', 'success')
        return redirect(url_for("main.login"))
    return render_template("register.html", groups=groups)


@bp.route('/award', methods=['GET', 'POST'])
@login_required
def award():
    if request.method == 'POST':
        award_type = request.form.get('award_type')
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)

        if award_type == 'competition':
            competition = Competition(
                name=request.form.get('competition_name'),
                level=int(request.form.get('level')),
                project_quality=int(request.form.get('project_quality')),
                place=int(request.form.get('place')),
                communication=int(request.form.get('communication')),
                user_id=user_id,
                awarded_by_id=current_user.id
            )
            db.session.add(competition)
            points = competition.level + competition.project_quality + competition.place + competition.communication
            user.points += points

        elif award_type == 'weekly':
            week_start = datetime.strptime (request.form.get('week_start'), '%Y-%m-%d')
            weekly_performance = WeeklyPerformance(
                user_id=user_id,
                week_start=week_start,
                academic_performance=int(request.form.get('academic_performance')),
                mentoring=int(request.form.get('mentoring')),
                teamwork=int(request.form.get('teamwork')),
                discipline=int(request.form.get('discipline')),
                awarded_by_id=current_user.id
            )
            db.session.add(weekly_performance)
            points = weekly_performance.academic_performance + weekly_performance.mentoring + weekly_performance.teamwork + weekly_performance.discipline
            user.points += points

        elif award_type == 'yearly':
            year = int(request.form.get('year'))
            yearly_performance = YearlyPerformance(
                user_id=user_id,
                year=year,
                projects_score=int(request.form.get('projects_score')),
                tech_dictation_score=int(request.form.get('tech_dictation_score')),
                initial_monitoring_score=int(request.form.get('initial_monitoring_score')),
                intermediate_certification_score=int(request.form.get('intermediate_certification_score')),
                final_certification_score=int(request.form.get('final_certification_score')),
                awarded_by_id=current_user.id
            )
            db.session.add(yearly_performance)
            points = yearly_performance.projects_score + yearly_performance.tech_dictation_score + yearly_performance.initial_monitoring_score + yearly_performance.intermediate_certification_score + yearly_performance.final_certification_score
            user.points += points

        db.session.commit()
        flash('Награда успешно добавлена', 'success')
        return redirect(url_for('users'))

    return render_template('award.html', users=User.query.all())

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.top_users'))  # Изменено здесь
        flash("Неправильное имя пользователя или пароль.", "error")
    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы успешно вышли из системы.", "success")
    return redirect(url_for("main.login"))

from flask_login import login_required, current_user

@bp.route("/points")
@login_required
def points():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template("points.html", current_user=current_user, transactions=transactions)
    
@bp.route("/add_points", methods=["POST"])
def add_points():
    if "user_id" in session:
        user_id = session["user_id"]
        user = User.query.get(user_id)
        points = int(request.form["points"])
        reason = request.form["reason"]
        transaction = Transaction(user_id=user_id, points=points, reason=reason)
        db.session.add(transaction)
        db.session.commit()
        return redirect(url_for("points"))
    else:
        return redirect(url_for("main.login"))
    

@bp.route("/top_users")
def top_users():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    top_users = User.query.order_by(User.points.desc()).paginate(page=page, per_page=per_page)
    
    if current_user.is_authenticated:
        user_rank = db.session.query(func.count(User.id) + 1).filter(User.points > current_user.points).scalar()
    
    return render_template("top_users.html", top_users=top_users, user_rank=user_rank)
    

@bp.route("/reward_punish", methods=["GET", "POST"])
@login_required
def reward_punish():
    if current_user.role not in ['teacher', 'admin']:
        flash("У вас нет доступа к этой странице.", "error")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        selected_students = request.form.getlist("selected_students")
        competition_name = request.form.get("competition_name")
        project_name = request.form.get("project_name")
        level = int(request.form.get("level"))
        quality = int(request.form.get("quality"))
        place = int(request.form.get("place"))
        comment = request.form.get("comment")

        total_points = level + quality + place

        for student_id in selected_students:
            student = User.query.get(student_id)
            if student and student.role == 'student':
                student.points += total_points
                competition = Competition(
                    name=competition_name,
                    level=level,
                    project_quality=quality,
                    place=place,
                    user_id=student.id,
                    awarded_by_id=current_user.id
                )
                db.session.add(competition)
                
                transaction = Transaction(
                    user_id=student.id,
                    points=total_points,
                    transaction_type='reward',
                    reason=f"Участие в конкурсе: {competition_name}",
                    comment=comment,
                    awarded_by_id=current_user.id
                )
                db.session.add(transaction)

        db.session.commit()
        flash(f"Награждение выполнено успешно. Начислено {total_points} баллов.", "success")
        return redirect(url_for("main.reward_punish"))

    groups = Group.query.all()
    students = User.query.filter_by(role='student').all()
    
    return render_template(
        "reward_punish.html",
        groups=groups,
        students=students,
        current_user=current_user
    )
    
@bp.route('/users')
@login_required
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

@bp.route('/update_weekly_performance', methods=['POST'])
@login_required
def update_weekly_performance():
    data = request.json
    student_id = data.get('student_id')
    week_start = datetime.strptime(data.get('week_start'), '%Y-%m-%d').date()
    academic_performance = data.get('academic_performance')
    mentoring = data.get('mentoring')
    teamwork = data.get('teamwork')
    discipline = data.get('discipline')

    weekly_perf = WeeklyPerformance.query.filter_by(
        user_id=student_id,
        week_start=week_start
    ).first()

    if weekly_perf:
        weekly_perf.academic_performance = academic_performance
        weekly_perf.mentoring = mentoring
        weekly_perf.teamwork = teamwork
        weekly_perf.discipline = discipline

        # Вычисляем общее количество баллов
        total_points = academic_performance + mentoring + teamwork + discipline
        weekly_perf.points = total_points

        # Обновляем общее количество баллов пользователя
        user = User.query.get(student_id)
        if user:
            user.points += total_points

        db.session.commit()

        return jsonify({"success": True, "new_points": user.points if user else None})
    else:
        return jsonify({"error": "Weekly performance record not found"}), 404

@bp.route('/weekly_performance', methods=['GET', 'POST'])
@login_required
def weekly_performance():
    if current_user.role not in ['teacher', 'admin']:
        flash("У вас нет доступа к этой странице.", "error")
        return redirect(url_for('main.index'))

    selected_date = request.args.get('date')
    if selected_date:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d')
    else:
        selected_date = datetime.now()

    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_end = week_start + timedelta(days=6)

    groups = Group.query.all()
    selected_group_id = request.args.get('group_id', type=int)

    if selected_group_id:
        students = User.query.filter_by(role='student', group_id=selected_group_id).all()
    else:
        students = User.query.filter_by(role='student').all()

    student_performances = []

    for student in students:
        weekly_perf = WeeklyPerformance.query.filter_by(
            user_id=student.id,
            week_start=week_start.date()
        ).first()

        if not weekly_perf:
            weekly_perf = WeeklyPerformance(
                user_id=student.id,
                week_start=week_start.date(),
                week=week_start.isocalendar()[1],
                year=week_start.year,
                points=0,
                academic_performance=0,
                mentoring=0,
                teamwork=0,
                discipline=0
            )
            db.session.add(weekly_perf)
        
        student_performances.append((student, weekly_perf))
    
    db.session.commit()

    if request.method == 'POST':
        action = request.form.get('action')
        student_id = request.form.get('student_id')
        points = int(request.form.get('points'))
        reason = request.form.get('reason')

        student = User.query.get(student_id)
        if not student:
            return jsonify({"error": "Студент не найден"}), 404

        if action == 'reward':
            student.points += points
            transaction_type = 'reward'
        elif action == 'penalty':
            student.points -= points
            transaction_type = 'penalty'
        else:
            return jsonify({"error": "Неверное действие"}), 400

        transaction = Transaction(
            user_id=student.id,
            points=points if action == 'reward' else -points,
            reason=reason,
            transaction_type=transaction_type,
            awarded_by_id=current_user.id
        )
        db.session.add(transaction)
        db.session.commit()

        return jsonify({"success": True, "new_points": student.points})

    return render_template(
        'weekly_performance.html',
        student_performances=student_performances,
        week_start=week_start,
        week_end=week_end,
        current_user=current_user,
        groups=groups,
        selected_group_id=selected_group_id
    )
@bp.route("/confirm_users", methods=["GET", "POST"])
@login_required
def confirm_users():
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash("У вас нет доступа к этой странице.", "error")
        return redirect(url_for("main.login"))

    if request.method == "POST":
        user_id = request.form["user_id"]
        user = User.query.get(user_id)
        if user:
            user.is_confirmed = True
            db.session.commit()
            return redirect(url_for("main.confirm_users"))

    unconfirmed_users = User.query.filter_by(is_confirmed=False).all()
    return render_template("confirm_users.html", users=unconfirmed_users)


@bp.route("/transactions", methods=["GET"])
@login_required
def transactions():
    # Удалите эту строку:
    # current_user = current_user

    if current_user.role not in ['teacher', 'admin']:
        flash("У вас нет доступа к этой странице.", "error")
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    per_page = 20  # Количество транзакций на странице

    transactions = Transaction.query.order_by(desc(Transaction.created_at)).paginate(page=page, per_page=per_page)

    return render_template("transactions.html", transactions=transactions)


@bp.route("/award_points", methods=["GET", "POST"])
@login_required
def award_points():
    if current_user.role not in ['teacher', 'admin']:
        flash("У вас нет доступа к этой странице.", "error")
        return redirect(url_for('index'))

    if request.method == "POST":
        user_id = request.form.get('user_id')
        points = int(request.form.get('points'))
        reason = request.form.get('reason')
        transaction_type = request.form.get('transaction_type')

        user = User.query.get(user_id)
        if user:
            if transaction_type == 'award':
                user.points += points
            elif transaction_type == 'penalty':
                user.points -= points

            transaction = Transaction(user_id=user.id, points=points, 
                                      transaction_type=transaction_type, reason=reason)
            db.session.add(transaction)
            db.session.commit()

            flash(f"{'Начислено' if transaction_type == 'award' else 'Списано'} {points} очков пользователю {user.full_name}", "success")
        else:
            flash("Пользователь не найден", "error")

        return redirect(url_for('award_points'))

    users = User.query.filter(User.role == 'student').all()
    return render_template("award_points.html", users=users)

@bp.route("/manage_users")
@login_required
def manage_users():
    current_user = current_user
    if not g.current_user or g.current_user.role != 'admin':
        flash("У вас нет доступа к этой странице.", "error")
        return redirect(url_for('main.points'))

    users = User.query.filter(User.role != 'admin').all()
    return render_template("manage_users.html", users=users)

@bp.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if g.current_user.role != 'admin':
        flash("У вас нет прав для выполнения этого действия.", "error")
        return redirect(url_for('index'))

    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash("Нельзя удалить администратора.", "error")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"Пользователь {user.full_name} был успешно удален.", "success")

    return redirect(url_for('manage_users'))

@bp.route('/user/<int:user_id>/awards')
@login_required
def user_awards(user_id):
    user = User.query.get(user_id)
    competitions = Competition.query.filter_by(user_id=user_id).all()
    weekly_performances = WeeklyPerformance.query.filter_by(user_id=user_id).all()
    yearly_performances = YearlyPerformance.query.filter_by(user_id=user_id).all()
    return render_template('user_awards.html', user=user, competitions=competitions, weekly_performances=weekly_performances, yearly_performances=yearly_performances)