from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/stu'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 模型定义
class Student(db.Model):
    __tablename__ = 'student'
    sno = db.Column(db.String(7), primary_key=True)
    sname = db.Column(db.String(20), nullable=False)
    ssex = db.Column(db.String(2))
    sage = db.Column(db.SmallInteger)
    sdept = db.Column(db.String(20))

class Course(db.Model):
    __tablename__ = 'course'
    cno = db.Column(db.String(6), primary_key=True)
    cname = db.Column(db.String(20), nullable=False)
    ccredit = db.Column(db.SmallInteger)
    cpno = db.Column(db.String(6), db.ForeignKey('course.cno'))  # 先修课

class Teacher(db.Model):
    __tablename__ = 't'
    tno = db.Column(db.String(7), primary_key=True)
    tname = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(20))

class SC(db.Model):
    __tablename__ = 'sc'
    sno = db.Column(db.String(7), db.ForeignKey('student.sno'), primary_key=True)
    cno = db.Column(db.String(6), db.ForeignKey('course.cno'), primary_key=True)
    grade = db.Column(db.SmallInteger)

class Teaching(db.Model):
    __tablename__ = 'teaching'
    tno = db.Column(db.String(7), db.ForeignKey('t.tno'), primary_key=True)
    cno = db.Column(db.String(6), db.ForeignKey('course.cno'), primary_key=True)

class Schedule(db.Model):
    __tablename__ = 'schedule'
    id = db.Column(db.Integer, primary_key=True)
    cno = db.Column(db.String(6), db.ForeignKey('course.cno'), nullable=False)
    tno = db.Column(db.String(7), db.ForeignKey('t.tno'), nullable=False)
    classroom = db.Column(db.String(20), nullable=False)
    day_of_week = db.Column(db.SmallInteger, nullable=False)  # 1-7表示周一到周日
    time_slot = db.Column(db.SmallInteger, nullable=False)  # 1-12表示第1-12节课
    duration = db.Column(db.SmallInteger, default=2)  # 课程持续节数，默认2节
    
    __table_args__ = (
        db.Index('idx_teacher_time', 'tno', 'day_of_week', 'time_slot'),
        db.Index('idx_classroom_time', 'classroom', 'day_of_week', 'time_slot'),
        db.Index('idx_course_time', 'cno', 'day_of_week', 'time_slot')
    )

# 冲突检测工具函数
def check_conflicts(cno, tno, classroom, day, slot, duration):
    """统一冲突检测函数"""
    conflicts = {
        'teacher': check_teacher_conflict(tno, day, slot, duration),
        'classroom': check_classroom_conflict(classroom, day, slot, duration),
        'course': check_course_conflict(cno, day, slot, duration),
        'student': check_student_conflict(cno, day, slot, duration),
        'prerequisite': check_prerequisite_conflict(cno)
    }
    return conflicts



def check_teacher_conflict(tno, day, slot, duration):
    """检测教师时间冲突"""
    conflicting = Schedule.query.filter(
        Schedule.tno == tno,
        Schedule.day_of_week == day,
        Schedule.time_slot <= slot + duration - 1,
        Schedule.time_slot + Schedule.duration - 1 >= slot
    ).all()
    return [f"{c.day_of_week}周{c.time_slot}节" for c in conflicting]

def check_classroom_conflict(classroom, day, slot, duration):
    """检测教室冲突"""
    conflicting = Schedule.query.filter(
        Schedule.classroom == classroom,
        Schedule.day_of_week == day,
        Schedule.time_slot <= slot + duration - 1,
        Schedule.time_slot + Schedule.duration - 1 >= slot
    ).all()
    return [f"{c.day_of_week}周{c.time_slot}节" for c in conflicting]

def check_course_conflict(cno, day, slot, duration):
    """检测课程本身是否已安排"""
    conflicting = Schedule.query.filter_by(cno=cno).all()
    return [f"{c.day_of_week}周{c.time_slot}节" for c in conflicting]

def check_student_conflict(cno, day, slot, duration):
    """更完善的学生时间冲突检测"""
    # 获取所有选修该课程的学生
    students = db.session.query(SC.sno).filter(SC.cno == cno).all()
    student_ids = [s[0] for s in students]
    
    if not student_ids:
        return []
    
    # 检查这些学生在相同时段是否有其他课程
    conflicting = db.session.query(
        Student.sno, 
        Student.sname, 
        Course.cname,
        Schedule.day_of_week,
        Schedule.time_slot
    ).join(SC, Student.sno == SC.sno)\
     .join(Schedule, SC.cno == Schedule.cno)\
     .join(Course, Schedule.cno == Course.cno)\
     .filter(
        Student.sno.in_(student_ids),
        Schedule.day_of_week == day,
        Schedule.time_slot <= slot + duration - 1,
        Schedule.time_slot + Schedule.duration - 1 >= slot,
        Schedule.cno != cno
    ).all()
    
    return [f"{s.sname}({s.sno}) 的 {s.cname} 课程 {s.day_of_week}周{s.time_slot}节" for s in conflicting]

def check_prerequisite_conflict(cno):
    """检测先修课程冲突"""
    course = Course.query.get(cno)
    if not course or not course.cpno:
        return []
    
    students_without_prereq = db.session.query(Student.sno, Student.sname).join(
        SC, Student.sno == SC.sno
    ).filter(
        SC.cno == cno
    ).except_(
        db.session.query(Student.sno, Student.sname).join(
            SC, Student.sno == SC.sno
        ).filter(SC.cno == course.cpno)
    ).all()
    
    return [f"{s.sno} {s.sname}" for s in students_without_prereq]

def generate_heatmap_data(schedule):
    """生成热力图数据"""
    heatmap = [[0 for _ in range(12)] for _ in range(7)]  # 7天 x 12节课
    
    for s in schedule:
        for i in range(s.duration):
            if s.time_slot + i - 1 < 12:  # 确保不超过12节课
                heatmap[s.day_of_week - 1][s.time_slot + i - 1] += 1
    
    return heatmap


# 路由定义
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/conflict-check', methods=['GET', 'POST'])
def conflict_check():
    if request.method == 'POST':
        conflicts = check_conflicts(
            request.form['cno'],
            request.form['tno'],
            request.form['classroom'],
            int(request.form['day_of_week']),
            int(request.form['time_slot']),
            int(request.form.get('duration', 2))
        )
        return render_template('conflict_result.html', conflicts=conflicts)
    
    courses = Course.query.all()
    teachers = Teacher.query.all()
    return render_template('conflict_check.html', courses=courses, teachers=teachers)

@app.route('/student-query', methods=['GET', 'POST'])
def student_query():
    if request.method == 'POST':
        sno = request.form['sno']
        student = Student.query.get(sno)
        if not student:
            flash('未找到该学生')
            return redirect(url_for('student_query'))
        
        schedule = db.session.query(
            Schedule, Course.cname
        ).join(
            SC, Schedule.cno == SC.cno
        ).join(
            Course, Schedule.cno == Course.cno
        ).filter(
            SC.sno == sno
        ).all()
        
        heatmap_data = generate_heatmap_data([s[0] for s in schedule])
        
        return render_template('student_query_result.html', 
                             student=student, 
                             schedule=schedule,
                             heatmap_data=heatmap_data)
    
    return render_template('student_query.html')

# 原有路由保持不变（students, scores, courses, teachers, teaching等）
# ... [保留原有的所有路由] ...
@app.route('/students')
def students():
    students = Student.query.all()
    return render_template('students.html', students=students)

@app.route('/scores')
def score_management():
    # 获取所有选课记录并关联学生和课程信息
    scs = db.session.query(
        SC, 
        Student.sname, 
        Course.cname
    ).join(Student, SC.sno == Student.sno)\
     .join(Course, SC.cno == Course.cno)\
     .all()
    students = Student.query.all()  # 获取所有学生
    courses = Course.query.all()    # 获取所有课程
    return render_template('scores.html', scs=scs, students=students, courses=courses)

@app.route('/score/edit', methods=['GET', 'POST'])
def edit_score():
    if request.method == 'POST':
        sno = request.form['sno']
        cno = request.form['cno']
        new_grade = request.form['grade']
        sc = SC.query.filter_by(sno=sno, cno=cno).first()
        if sc:
            sc.grade = new_grade
            try:
                db.session.commit()
                flash('成绩修改成功')
            except Exception:
                db.session.rollback()
                flash('成绩修改失败')
    return redirect(url_for('score_management'))

@app.route('/score/add', methods=['POST'])
def add_score():
    sno = request.form['student']
    cno = request.form['course']
    grade = request.form['grade']
    new_sc = SC(sno=sno, cno=cno, grade=grade)
    db.session.add(new_sc)
    try:
        db.session.commit()
        flash('添加成绩成功')
    except Exception:
        db.session.rollback()
        flash('添加成绩失败，可能已存在或数据有误')
    return redirect(url_for('score_management'))

@app.route('/score/delete', methods=['POST'])
def delete_score():
    sno = request.form['sno']
    cno = request.form['cno']
    sc = SC.query.filter_by(sno=sno, cno=cno).first()
    if sc:
        db.session.delete(sc)
        try:
            db.session.commit()
            flash('删除成功')
        except Exception:
            db.session.rollback()
            flash('删除失败')
    return redirect(url_for('score_management'))

@app.route('/student/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        sno = request.form['sno']
        sname = request.form['sname']
        ssex = request.form.get('ssex')
        sage = request.form.get('sage')
        sdept = request.form.get('sdept')
        # 类型转换和简单校验
        try:
            sage_int = int(sage) if sage else None
        except ValueError:
            sage_int = None
        new_student = Student(
            sno=sno,
            sname=sname,
            ssex=ssex,
            sage=sage_int,
            sdept=sdept
        )
        db.session.add(new_student)
        try:
            db.session.commit()
            flash('添加成功')
        except Exception:
            db.session.rollback()
            flash('添加失败，学号重复或数据有误')
        return redirect(url_for('students'))
    return render_template('student_form.html')

@app.route('/student/edit/<sno>', methods=['GET', 'POST'])
def edit_student(sno):
    student = Student.query.get(sno)
    if not student:
        flash('未找到该学生')
        return redirect(url_for('students'))
    if request.method == 'POST':
        student.sname = request.form['sname']
        student.ssex = request.form.get('ssex')
        sage = request.form.get('sage')
        try:
            student.sage = int(sage) if sage else None
        except ValueError:
            student.sage = None
        student.sdept = request.form.get('sdept')
        try:
            db.session.commit()
            flash('修改成功')
        except Exception:
            db.session.rollback()
            flash('修改失败')
        return redirect(url_for('students'))
    return render_template('student_form.html', student=student)

@app.route('/student/delete/<sno>')
def delete_student(sno):
    student = Student.query.get(sno)
    if student:
        db.session.delete(student)
        try:
            db.session.commit()
            flash('删除成功')
        except Exception:
            db.session.rollback()
            flash('删除失败，可能有关联数据')
    return redirect(url_for('students'))

@app.route('/student/<sno>/courses', methods=['GET', 'POST'])
def student_courses(sno):
    student = Student.query.get(sno)
    if not student:
        flash('未找到该学生')
        return redirect(url_for('students'))
    sc_list = SC.query.filter_by(sno=sno).all()
    courses = []
    for sc in sc_list:
        course = Course.query.get(sc.cno)
        courses.append({
            'cno': sc.cno,
            'cname': course.cname if course else '未知课程',
            'grade': sc.grade
        })
    if request.method == 'POST':
        for c in courses:
            grade_key = f'grade_{c["cno"]}'
            if grade_key in request.form:
                try:
                    new_grade = int(request.form[grade_key])
                    sc_record = SC.query.filter_by(sno=sno, cno=c['cno']).first()
                    if sc_record:
                        sc_record.grade = new_grade
                except ValueError:
                    flash(f'成绩需为整数: {c["cname"]}')
        try:
            db.session.commit()
            flash('成绩修改成功')
        except Exception:
            db.session.rollback()
            flash('成绩修改失败')
        return redirect(url_for('student_courses', sno=sno))
    return render_template('student_courses.html', student=student, courses=courses)

@app.route('/courses')
def courses():
    courses = Course.query.all()
    return render_template('courses.html', courses=courses)

@app.route('/course/add', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        cno = request.form['cno']
        cname = request.form['cname']
        ccredit = request.form.get('ccredit')
        cpno = request.form.get('cpno')
        try:
            ccredit_int = int(ccredit) if ccredit else None
        except ValueError:
            ccredit_int = None
        new_course = Course(cno=cno, cname=cname, ccredit=ccredit_int, cpno=cpno or None)
        db.session.add(new_course)
        try:
            db.session.commit()
            flash('添加成功')
        except Exception:
            db.session.rollback()
            flash('添加失败，课程号重复或数据有误')
        return redirect(url_for('courses'))
    return render_template('course_form.html')

@app.route('/course/edit/<cno>', methods=['GET', 'POST'])
def edit_course(cno):
    course = Course.query.get(cno)
    if not course:
        flash('未找到该课程')
        return redirect(url_for('courses'))
    if request.method == 'POST':
        course.cname = request.form['cname']
        ccredit = request.form.get('ccredit')
        cpno = request.form.get('cpno')
        try:
            course.ccredit = int(ccredit) if ccredit else None
        except ValueError:
            course.ccredit = None
        course.cpno = cpno or None
        try:
            db.session.commit()
            flash('修改成功')
        except Exception:
            db.session.rollback()
            flash('修改失败')
        return redirect(url_for('courses'))
    return render_template('course_form.html', course=course)

@app.route('/course/delete/<cno>')
def delete_course(cno):
    course = Course.query.get(cno)
    if course:
        db.session.delete(course)
        try:
            db.session.commit()
            flash('删除成功')
        except Exception:
            db.session.rollback()
            flash('删除失败，可能有关联数据')
    return redirect(url_for('courses'))

@app.route('/teachers')
def teachers():
    teachers = Teacher.query.all()
    return render_template('teachers.html', teachers=teachers)

@app.route('/teacher/add', methods=['GET', 'POST'])
def add_teacher():
    if request.method == 'POST':
        tno = request.form['tno']
        tname = request.form['tname']
        title = request.form['title']
        new_teacher = Teacher(tno=tno, tname=tname, title=title)
        db.session.add(new_teacher)
        try:
            db.session.commit()
            flash('添加成功')
        except Exception:
            db.session.rollback()
            flash('添加失败，工号重复或数据有误')
        return redirect(url_for('teachers'))
    return render_template('teacher_form.html')

@app.route('/teacher/edit/<tno>', methods=['GET', 'POST'])
def edit_teacher(tno):
    teacher = Teacher.query.get(tno)
    if not teacher:
        flash('未找到该教师')
        return redirect(url_for('teachers'))
    if request.method == 'POST':
        teacher.tname = request.form['tname']
        teacher.title = request.form['title']
        try:
            db.session.commit()
            flash('修改成功')
        except Exception:
            db.session.rollback()
            flash('修改失败')
        return redirect(url_for('teachers'))
    return render_template('teacher_form.html', teacher=teacher)

@app.route('/teacher/delete/<tno>')
def delete_teacher(tno):
    teacher = Teacher.query.get(tno)
    if teacher:
        db.session.delete(teacher)
        try:
            db.session.commit()
            flash('删除成功')
        except Exception:
            db.session.rollback()
            flash('删除失败，可能有关联数据')
    return redirect(url_for('teachers'))

@app.route('/teaching')
def teaching():
    teachings = db.session.query(
        Teaching, Teacher.tname, Course.cname
    ).join(Teacher, Teaching.tno == Teacher.tno)\
     .join(Course, Teaching.cno == Course.cno)\
     .all()
    teachers = Teacher.query.all()
    courses = Course.query.all()
    return render_template('teaching.html', teachings=teachings, teachers=teachers, courses=courses)

@app.route('/teaching/add', methods=['POST'])
def add_teaching():
    tno = request.form['teacher']
    cno = request.form['course']
    # 检查教师是否存在
    teacher = Teacher.query.get(tno)
    course = Course.query.get(cno)
    if not teacher:
        flash('教师不存在，无法安排授课')
        return redirect(url_for('teaching'))
    if not course:
        flash('课程不存在，无法安排授课')
        return redirect(url_for('teaching'))
    new_teaching = Teaching(tno=tno, cno=cno)
    db.session.add(new_teaching)
    try:
        db.session.commit()
        flash('添加授课安排成功')
    except Exception:
        db.session.rollback()
        flash('添加授课安排失败，可能是外键约束或重复安排')
    return redirect(url_for('teaching'))

@app.route('/teaching/delete', methods=['POST'])
def delete_teaching():
    tno = request.form['tno']
    cno = request.form['cno']
    teaching = Teaching.query.filter_by(tno=tno, cno=cno).first()
    if teaching:
        db.session.delete(teaching)
        try:
            db.session.commit()
            flash('删除成功')
        except Exception:
            db.session.rollback()
            flash('删除失败')
    return redirect(url_for('teaching'))

@app.route('/schedule')
def schedule_management():
    schedules = db.session.query(
        Schedule, 
        Course.cname, 
        Teacher.tname
    ).join(Course, Schedule.cno == Course.cno)\
     .join(Teacher, Schedule.tno == Teacher.tno)\
     .all()
    courses = Course.query.all()
    teachers = Teacher.query.all()
    classrooms = ['A101', 'A102', 'A201', 'A202', 'B101', 'B102']  # 示例教室列表
    return render_template('schedule.html', 
                         schedules=schedules,
                         courses=courses,
                         teachers=teachers,
                         classrooms=classrooms)

@app.route('/schedule/add', methods=['POST'])
def add_schedule():
    cno = request.form['course']
    tno = request.form['teacher']
    classroom = request.form['classroom']
    day_of_week = int(request.form['day_of_week'])
    time_slot = int(request.form['time_slot'])
    duration = int(request.form.get('duration', 2))
    
    # 检查冲突
    conflicts = check_conflicts(cno, tno, classroom, day_of_week, time_slot, duration)
    has_conflict = any(conflicts.values())
    
    if has_conflict:
        flash('存在冲突，无法添加排课')
        return redirect(url_for('schedule_management'))
    
    new_schedule = Schedule(
        cno=cno,
        tno=tno,
        classroom=classroom,
        day_of_week=day_of_week,
        time_slot=time_slot,
        duration=duration
    )
    db.session.add(new_schedule)
    try:
        db.session.commit()
        flash('排课添加成功')
    except Exception:
        db.session.rollback()
        flash('排课添加失败')
    return redirect(url_for('schedule_management'))

@app.route('/schedule/delete/<int:id>')
def delete_schedule(id):
    schedule = Schedule.query.get(id)
    if schedule:
        db.session.delete(schedule)
        try:
            db.session.commit()
            flash('排课删除成功')
        except Exception:
            db.session.rollback()
            flash('排课删除失败')
    return redirect(url_for('schedule_management'))

@app.route('/init-schedule')
def init_schedule():
    """随机初始化排课数据"""
    from random import choice, randint
    
    # 清空现有排课
    Schedule.query.delete()
    
    # 获取所有课程和教师
    courses = Course.query.all()
    teachers = Teacher.query.all()
    classrooms = ['A101', 'A102', 'A201', 'A202', 'B101', 'B102']
    
    # 为每门课程随机安排时间和教室
    for course in courses:
        # 随机选择一个教师教授这门课
        teacher = choice(teachers)
        
        # 随机安排时间
        day = randint(1, 5)  # 周一到周五
        time_slot = randint(1, 10)  # 第1-10节课
        duration = 2  # 默认2节课
        
        # 随机选择教室
        classroom = choice(classrooms)
        
        # 创建排课记录
        schedule = Schedule(
            cno=course.cno,
            tno=teacher.tno,
            classroom=classroom,
            day_of_week=day,
            time_slot=time_slot,
            duration=duration
        )
        db.session.add(schedule)
    
    try:
        db.session.commit()
        flash('排课数据初始化成功')
    except Exception:
        db.session.rollback()
        flash('排课数据初始化失败')
    
    return redirect(url_for('schedule_management'))

@app.route('/course-selection', methods=['GET', 'POST'])
def course_selection():
    if request.method == 'POST':
        sno = request.form['sno']
        cno = request.form['cno']
        
        # 检查是否已选过该课程（使用no_autoflush避免提前触发）
        with db.session.no_autoflush:
            existing = db.session.query(SC).filter_by(sno=sno, cno=cno).first()
            if existing:
                flash(f'选课失败：该学生已选修过{cno}课程', 'warning')
                return redirect(url_for('course_selection'))
        
        # 获取其他表单数据
        classroom = request.form['classroom']
        day_of_week = int(request.form['day_of_week'])
        time_slot = int(request.form['time_slot'])
        duration = int(request.form.get('duration', 2))
        
        # 检查冲突（保持原有逻辑）
        conflicts = check_conflicts(cno, None, classroom, day_of_week, time_slot, duration)
        
        try:
            # 开始事务
            with db.session.begin_nested():
                # 添加选课记录
                new_sc = SC(sno=sno, cno=cno, grade=None)
                db.session.add(new_sc)
                
                # 添加课程安排
                teaching = Teaching.query.filter_by(cno=cno).first()
                if teaching:
                    new_schedule = Schedule(
                        cno=cno,
                        tno=teaching.tno,
                        classroom=classroom,
                        day_of_week=day_of_week,
                        time_slot=time_slot,
                        duration=duration
                    )
                    db.session.add(new_schedule)
            
            db.session.commit()
            flash('选课成功', 'success')
            
        except IntegrityError as e:
            db.session.rollback()
            if "Duplicate entry" in str(e.orig):
                flash(f'选课失败：该学生已选修过{cno}课程', 'danger')
            else:
                flash(f'数据库错误：{str(e)}', 'danger')
                
        except Exception as e:
            db.session.rollback()
            flash(f'选课失败：{str(e)}', 'danger')
        
        return redirect(url_for('course_selection'))
    
    # GET请求处理保持不变
    students = Student.query.all()
    courses = Course.query.all()
    return render_template('course_selection.html', students=students, courses=courses)


@app.route('/course-selection-check', methods=['GET', 'POST'])
def course_selection_check():
    if request.method == 'POST':
        cno = request.form['cno']
        classroom = request.form['classroom']
        day = int(request.form['day_of_week'])
        slot = int(request.form['time_slot'])
        duration = int(request.form.get('duration', 2))
        
        conflicts = check_conflicts(cno, None, classroom, day, slot, duration)
        return render_template('conflict_result.html', conflicts=conflicts)
    
    courses = Course.query.all()
    return render_template('conflict_check.html', courses=courses, teachers=[])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 创建所有表
    import sys
    try:
        app.run(debug=True)
    except SystemExit as e:
        # 避免 VSCode 调试时 SystemExit 异常影响调试体验
        if e.code != 0:
            raise
        sys.exit(0)
