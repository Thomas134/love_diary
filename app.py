import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# ── 配置 ──────────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///love_diary.db'
)
# Railway PostgreSQL URL 以 postgres:// 开头，SQLAlchemy 要求 postgresql://
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config[
        'SQLALCHEMY_DATABASE_URI'
    ].replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 上传限制

# Cloudinary 配置（从环境变量读取）
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
    api_key=os.environ.get('CLOUDINARY_API_KEY', ''),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET', ''),
)

db = SQLAlchemy(app)


# ── 数据模型 ──────────────────────────────────────────────────────
class DiaryEntry(db.Model):
    """日记条目"""
    __tablename__ = 'diary_entries'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    mood = db.Column(db.String(20), default='happy')       # 心情标签
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cover_image_url = db.Column(db.String(500))            # 封面图 URL（Cloudinary）
    cover_image_public_id = db.Column(db.String(200))      # Cloudinary public_id

    photos = db.relationship('Photo', backref='diary', lazy=True,
                             cascade='all, delete-orphan')

    def __repr__(self):
        return f'<DiaryEntry {self.title}>'


class Photo(db.Model):
    """照片"""
    __tablename__ = 'photos'

    id = db.Column(db.Integer, primary_key=True)
    diary_id = db.Column(db.Integer, db.ForeignKey('diary_entries.id'), nullable=True)
    url = db.Column(db.String(500), nullable=False)
    public_id = db.Column(db.String(200), nullable=False)  # Cloudinary public_id
    caption = db.Column(db.String(200), default='')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Photo {self.public_id}>'


# ── 登录保护装饰器 ────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ── 工具函数 ──────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_to_cloudinary(file, folder='love_diary'):
    """上传文件到 Cloudinary，返回 (url, public_id)"""
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        resource_type='image',
    )
    return result['secure_url'], result['public_id']


def delete_from_cloudinary(public_id: str):
    """从 Cloudinary 删除图片"""
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception:
        pass  # 删除失败不影响主流程


# ── 路由 ──────────────────────────────────────────────────────────

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('diary_list'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('diary_list'))
    if request.method == 'POST':
        password = request.form.get('password', '')
        correct = os.environ.get('SITE_PASSWORD', 'love2024')
        if password == correct:
            session['logged_in'] = True
            session.permanent = True
            flash('欢迎回来 💕', 'success')
            return redirect(url_for('diary_list'))
        else:
            flash('密码错误，再试一次吧', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('login'))


# ── 日记 CRUD ─────────────────────────────────────────────────────

@app.route('/diary')
@login_required
def diary_list():
    entries = DiaryEntry.query.order_by(DiaryEntry.date.desc()).all()
    return render_template('diary_list.html', entries=entries)


@app.route('/diary/new', methods=['GET', 'POST'])
@login_required
def diary_new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        mood = request.form.get('mood', 'happy')
        date_str = request.form.get('date', '')

        if not title or not content:
            flash('标题和内容不能为空', 'error')
            return render_template('diary_form.html', entry=None)

        try:
            entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            entry_date = datetime.utcnow().date()

        entry = DiaryEntry(title=title, content=content, mood=mood, date=entry_date)

        # 封面图上传
        cover_file = request.files.get('cover_image')
        if cover_file and cover_file.filename and allowed_file(cover_file.filename):
            url, public_id = upload_to_cloudinary(cover_file, folder='love_diary/covers')
            entry.cover_image_url = url
            entry.cover_image_public_id = public_id

        db.session.add(entry)
        db.session.commit()
        flash('日记已保存 💖', 'success')
        return redirect(url_for('diary_detail', entry_id=entry.id))

    return render_template('diary_form.html', entry=None)


@app.route('/diary/<int:entry_id>')
@login_required
def diary_detail(entry_id):
    entry = DiaryEntry.query.get_or_404(entry_id)
    return render_template('diary_detail.html', entry=entry)


@app.route('/diary/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
def diary_edit(entry_id):
    entry = DiaryEntry.query.get_or_404(entry_id)
    if request.method == 'POST':
        entry.title = request.form.get('title', '').strip() or entry.title
        entry.content = request.form.get('content', '').strip() or entry.content
        entry.mood = request.form.get('mood', entry.mood)
        date_str = request.form.get('date', '')
        try:
            entry.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

        # 更换封面图
        cover_file = request.files.get('cover_image')
        if cover_file and cover_file.filename and allowed_file(cover_file.filename):
            if entry.cover_image_public_id:
                delete_from_cloudinary(entry.cover_image_public_id)
            url, public_id = upload_to_cloudinary(cover_file, folder='love_diary/covers')
            entry.cover_image_url = url
            entry.cover_image_public_id = public_id

        db.session.commit()
        flash('日记已更新 ✨', 'success')
        return redirect(url_for('diary_detail', entry_id=entry.id))

    return render_template('diary_form.html', entry=entry)


@app.route('/diary/<int:entry_id>/delete', methods=['POST'])
@login_required
def diary_delete(entry_id):
    entry = DiaryEntry.query.get_or_404(entry_id)
    # 删除封面图
    if entry.cover_image_public_id:
        delete_from_cloudinary(entry.cover_image_public_id)
    # 删除关联照片（cascade 会删 DB 记录，这里删 Cloudinary）
    for photo in entry.photos:
        delete_from_cloudinary(photo.public_id)
    db.session.delete(entry)
    db.session.commit()
    flash('日记已删除', 'info')
    return redirect(url_for('diary_list'))


# ── 照片墙 ────────────────────────────────────────────────────────

@app.route('/photos')
@login_required
def photo_wall():
    photos = Photo.query.order_by(Photo.uploaded_at.desc()).all()
    return render_template('photo_wall.html', photos=photos)


@app.route('/photos/upload', methods=['POST'])
@login_required
def photo_upload():
    files = request.files.getlist('photos')
    diary_id = request.form.get('diary_id') or None
    caption = request.form.get('caption', '')

    uploaded = 0
    for f in files:
        if f and f.filename and allowed_file(f.filename):
            url, public_id = upload_to_cloudinary(f, folder='love_diary/photos')
            photo = Photo(
                url=url,
                public_id=public_id,
                caption=caption,
                diary_id=int(diary_id) if diary_id else None,
            )
            db.session.add(photo)
            uploaded += 1

    db.session.commit()
    if uploaded:
        flash(f'成功上传 {uploaded} 张照片 📸', 'success')
    else:
        flash('没有有效的图片文件', 'warning')
    return redirect(request.referrer or url_for('photo_wall'))


@app.route('/photos/<int:photo_id>/delete', methods=['POST'])
@login_required
def photo_delete(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    delete_from_cloudinary(photo.public_id)
    db.session.delete(photo)
    db.session.commit()
    flash('照片已删除', 'info')
    return redirect(request.referrer or url_for('photo_wall'))


# ── 应用启动 ──────────────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
