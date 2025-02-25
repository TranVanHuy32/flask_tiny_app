from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/delete_multiple', methods=('GET',))
@login_required
def delete_multiple():
    if g.user['role'] != 'admin':
        abort(403)

    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'  # Đã thêm p.id
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/delete_multiple.html', posts=posts)

@bp.route('/delete_multiple', methods=('POST',))  # Route POST để xử lý xóa
@login_required
def delete_multiple_process():  # Tên hàm nên khác với hàm GET để rõ ràng
    if g.user['role'] != 'admin':
        abort(403)

    post_ids = request.form.getlist('post_ids')
    if not post_ids:
        flash('Vui lòng chọn ít nhất một bài viết để xóa.')
        return redirect(url_for('blog.index'))

    db = get_db()
    try:
        for post_id in post_ids:
            db.execute('DELETE FROM post WHERE id = ?', (post_id,))
        db.commit()
        flash('Đã xóa thành công các bài viết đã chọn.')
    except Exception as e:
        # Xử lý lỗi (ví dụ: ghi log)
        db.rollback()
        flash('Đã có lỗi xảy ra khi xóa bài viết. Vui lòng thử lại.')
        return redirect(url_for('blog.index'))  # Vẫn chuyển hướng về trang blog khi có lỗi

    return redirect(url_for('blog.index'))  # Chuyển hướng về trang blog sau khi xóa thành công