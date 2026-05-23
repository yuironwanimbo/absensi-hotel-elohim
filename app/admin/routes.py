from datetime import datetime, time
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Absensi, User, Pengaturan, UserCredential
from functools import wraps
import re
from io import BytesIO

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role not in ['admin', 'hrd']:
            flash('Akses ditolak', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated

def get_default_jam():
    from app import create_app
    p = Pengaturan.query.first()
    if not p:
        p = Pengaturan(); db.session.add(p); db.session.commit()
    return p

# ═════════════════════════════════════════════════════════
#  GET — Dashboard (all tabs in one page)
# ══════════════════════════════════════════════════════════
@bp.route('/')
@login_required
@admin_required
def dashboard():
    today   = datetime.now().date()
    today_label = (['Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu']
                   [datetime.now().weekday()]) + ', ' + \
                   datetime.now().strftime('%d %B %Y')

    absensis   = Absensi.query.filter_by(tanggal=today).all()
    karyawans  = User.query.filter_by(role='karyawan', aktif=True).order_by(User.nama).all()
    settings   = get_default_jam()
    absensis_all = Absensi.query.order_by(Absensi.tanggal.desc()).limit(50).all()

    hadir_count     = sum(1 for a in absensis if a.jam_masuk and not a.jam_pulang)
    pulang_count    = sum(1 for a in absensis if a.jam_pulang)
    terlambat_count = sum(1 for a in absensis if a.status == 'terlambat')
    pct = round(hadir_count / len(karyawans) * 100) if karyawans else 0

    return render_template('admin/dashboard.html',
        today_label=today_label, today=today,
        absensis=absensis, karyawans=karyawans, settings=settings,
        absensis_all=absensis_all,
        hadir_count=hadir_count, pulang_count=pulang_count,
        terlambat_count=terlambat_count, pct=pct, total_karyawan=len(karyawans))

# ═════════════════════════════════════════════════════════
#  POST — Save global settings (jam masuk, jam pulang, GPS)
# ═════════════════════════════════════════════════════════
@bp.route('/settings', methods=['POST'])
@login_required
@admin_required
def save_settings():
    s = get_default_jam()
    s.nama_hotel   = request.form.get('nama_hotel',   s.nama_hotel)
    s.jam_masuk    = request.form.get('jam_masuk',    s.jam_masuk)
    s.jam_pulang   = request.form.get('jam_pulang',   s.jam_pulang)
    s.hotel_lat    = float(request.form.get('hotel_lat',  s.hotel_lat  or 0))
    s.hotel_lng    = float(request.form.get('hotel_lng',  s.hotel_lng  or 0))
    s.radius_meters= int(request.form.get('radius_meters', s.radius_meters or 100))
    s.updated_at   = datetime.utcnow()
    db.session.commit()
    flash('Pengaturan berhasil disimpan', 'success')
    return redirect(url_for('admin.dashboard') + '#tab-settings')

# ═════════════════════════════════════════════════════════
#  POST — Add new karyawan
# ═════════════════════════════════════════════════════════
@bp.route('/karyawan/add', methods=['POST'])
@login_required
@admin_required
def karyawan_add():
    nama   = request.form.get('nama',   '').strip()
    email  = request.form.get('email',  '').strip()
    passwd = request.form.get('password', '').strip()
    role   = request.form.get('role',   'karyawan')
    pin    = request.form.get('pin', '').strip() or None
    jm     = request.form.get('jadwal_masuk', '').strip() or None
    jp     = request.form.get('jadwal_pulang', '').strip() or None

    if not nama or not email or not passwd:
        flash('Nama, email dan password wajib diisi', 'danger')
        return redirect(url_for('admin.dashboard') + '#tab-karyawan')

    if User.query.filter_by(email=email).first():
        flash('Email sudah terdaftar', 'danger')
        return redirect(url_for('admin.dashboard') + '#tab-karyawan')

    u = User(nama=nama, email=email, role=role, pin=pin,
              jadwal_masuk=jm, jadwal_pulang=jp)
    u.set_password(passwd)
    db.session.add(u)
    db.session.flush()
    cred = UserCredential(user_id=u.id, plain_pass=passwd)
    db.session.add(cred)
    db.session.commit()
    flash(f'Karyawan "{nama}" berhasil ditambahkan. Password: {passwd}', 'success')
    return redirect(url_for('admin.dashboard') + '#tab-karyawan')

# ═════════════════════════════════════════════════════════
#  POST — Update karyawan
# ═════════════════════════════════════════════════════════
@bp.route('/karyawan/<int:kid>/update', methods=['POST'])
@login_required
@admin_required
def karyawan_update(kid):
    u = User.query.get_or_404(kid)
    u.nama  = request.form.get('nama',  u.nama).strip()
    u.email = request.form.get('email', u.email).strip()
    u.role  = request.form.get('role',  u.role)
    u.pin   = request.form.get('pin', '').strip() or None
    u.jadwal_masuk  = request.form.get('jadwal_masuk',  u.jadwal_masuk).strip() or None
    u.jadwal_pulang = request.form.get('jadwal_pulang', u.jadwal_pulang).strip() or None
    u.aktif = 'aktif' in request.form
    db.session.commit()
    flash(f'Data "{u.nama}" berhasil diperbarui', 'success')
    return redirect(url_for('admin.dashboard') + '#tab-karyawan')

# ═════════════════════════════════════════════════════════
#  POST — Reset password karyawan
# ════════════════════════════════════════════════════════
@bp.route('/karyawan/<int:kid>/ganti-password', methods=['POST'])
@login_required
@admin_required
def karyawan_ganti_password(kid):
    u = User.query.get_or_404(kid)
    new_pw = request.form.get('new_password', '').strip()
    if len(new_pw) < 4:
        flash('Password minimal 4 karakter', 'danger')
        return redirect(url_for('admin.dashboard') + '#tab-karyawan')
    u.set_password(new_pw)
    db.session.commit()
    flash(f'Password {u.nama} berhasil direset', 'success')
    return redirect(url_for('admin.dashboard') + '#tab-karyawan')

# ═════════════════════════════════════════════════════════
#  POST — Toggle aktif / non-aktif karyawan
# ════════════════════════════════════════════════════════
@bp.route('/karyawan/<int:kid>/toggle', methods=['POST'])
@login_required
@admin_required
def karyawan_toggle(kid):
    if kid == current_user.id:
        return jsonify({'success': False, 'message': 'Tidak bisa menonaktifkan akun sendiri'})
    u = User.query.get_or_404(kid)
    u.aktif = not u.aktif
    db.session.commit()
    return jsonify({'success': True,
                    'message': f'{u.nama} sudah {"diaktifkan" if u.aktif else "dinonaktifkan"}'})

# ═════════════════════════════════════════════════════════
#  POST — Delete karyawan
# ════════════════════════════════════════════════════════
@bp.route('/karyawan/<int:kid>/delete', methods=['POST'])
@login_required
@admin_required
def karyawan_delete(kid):
    if kid == current_user.id:
        flash('Tidak bisa menghapus akun sendiri', 'danger')
        return redirect(url_for('admin.dashboard') + '#tab-karyawan')
    u = User.query.get_or_404(kid)
    if abs(u.nama): flash(f'Karyawan "{u.nama}" berhasil dihapus', 'success')
    db.session.delete(u)
    db.session.commit()
    return redirect(url_for('admin.dashboard') + '#tab-karyawan')

# ═════════════════════════════════════════════════════════
# GET — Get credentials for employee
# ═════════════════════════════════════════════════════════
@bp.route('/karyawan/<int:kid>/credentials', methods=['GET'])
@login_required
@admin_required
def get_credentials(kid):
    u = User.query.get_or_404(kid)
    cred = UserCredential.query.filter_by(user_id=kid).first()
    password = cred.plain_pass if cred else '********'
    return jsonify({'success': True, 'email': u.email, 'password': password})

# ═════════════════════════════════════════════════════════
# POST — Upload foto wajah karyawan
# ═════════════════════════════════════════════════════════
@bp.route('/karyawan/<int:kid>/upload-face', methods=['POST'])
@login_required
@admin_required
def upload_face(kid):
    from flask import current_app
    u = User.query.get_or_404(kid)
    if 'foto' not in request.files:
        return jsonify({'success': False, 'message': 'Tidak ada file'})
    f = request.files['foto']
    if f.filename == '':
        return jsonify({'success': False, 'message': 'File kosong'})
    import os, uuid
    ext = f.filename.rsplit('.', 1)[-1] if '.' in f.filename else 'jpg'
    fname = f"face_{u.id}_{uuid.uuid4().hex[:8]}.{ext}"
    fp = os.path.join(current_app.config['UPLOAD_FOLDER'], fname)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    f.save(fp)
    u.foto_wajah = fname
    db.session.commit()
    return jsonify({'success': True, 'message': 'Foto wajah tersimpan', 'foto': fname})

# ═════════════════════════════════════════════════════════
# POST — Record attendance on behalf of a karyawan
# ═════════════════════════════════════════════════════════
@bp.route('/karyawan/absen', methods=['POST'])
@login_required
@admin_required
def karyawan_absen():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Data tidak valid'})
    karyawan_id = data.get('karyawan_id')
    tipe        = data.get('tipe')
    if not karyawan_id or tipe not in ('masuk', 'pulang'):
        return jsonify({'success': False, 'message': 'Parameter tidak lengkap'})
    target = User.query.get(karyawan_id)
    if not target or not target.aktif:
        return jsonify({'success': False, 'message': 'Karyawan tidak ditemukan'})
    today = datetime.now().date()
    absen = Absensi.query.filter_by(user_id=karyawan_id, tanggal=today).first()
    jam_sekarang  = datetime.now().time()
    jam_masuk_def = time(*map(int, get_default_jam().jam_masuk.split(':')))
    status = 'hadir'
    if jam_sekarang > jam_masuk_def:
        status = 'terlambat'
    if tipe == 'masuk':
        if absen and absen.jam_masuk:
            return jsonify({'success': False,
                            'message': f'{target.nama} sudah absen masuk hari ini'})
        if absen:
            absen.jam_masuk = jam_sekarang
            absen.status    = status
        else:
            absen = Absensi(user_id=karyawan_id, tanggal=today,
                            jam_masuk=jam_sekarang, status=status)
            db.session.add(absen)
        msg = f'Absen masuk berhasil dicatat untuk {target.nama}'
    else:
        if not absen or not absen.jam_masuk:
            return jsonify({'success': False,
                            'message': f'{target.nama} belum absen masuk hari ini'})
        if absen.jam_pulang:
            return jsonify({'success': False,
                            'message': f'{target.nama} sudah absen pulang hari ini'})
        absen.jam_pulang = jam_sekarang
        msg = f'Absen pulang berhasil dicatat untuk {target.nama}'
    db.session.commit()
    return jsonify({'success': True, 'message': msg,
                    'jam_masuk':  absen.jam_masuk.strftime('%H:%M') if absen.jam_masuk else None,
                    'jam_pulang': absen.jam_pulang.strftime('%H:%M') if absen.jam_pulang else None})

# ═════════════════════════════════════════════════════════
#  Legacy sub-pages (still accessible via navbar)
# ════════════════════════════════════════════════════════
@bp.route('/karyawan')
@login_required
@admin_required
def karyawan():
    karyawans = User.query.filter(User.role == 'karyawan').order_by(User.nama).all()
    today     = datetime.now().date()
    today_map = {a.user_id: a
                  for a in Absensi.query.filter_by(tanggal=today).all()}
    return render_template('admin/karyawan.html',
                            karyawans=karyawans, today_absen_map=today_map)

@bp.route('/riwayat')
@login_required
@admin_required
def riwayat():
    absensis = Absensi.query.order_by(Absensi.tanggal.desc()).all()
    return render_template('admin/riwayat.html', absensis=absensis)

@bp.route('/export/pdf')
@login_required
@admin_required
def export_pdf():
    absensis = Absensi.query.order_by(Absensi.tanggal.desc()).all()
    from fpdf import FPDF
    import os
    pdf = FPDF()
    pdf.add_page()
    
    # Add logo
    try:
        # Get the absolute path to the logo file
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'uploads', 'logo.png')
        print(f"Logo path: {logo_path}")  # Debug
        print(f"Logo exists: {os.path.exists(logo_path)}")  # Debug
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=10, y=8, w=20)  # Reduced width to 20 for smaller logo
            print("Logo added to PDF")  # Debug
    except Exception as e:
        # If logo not found or error, continue without it
        print(f"Error adding logo: {e}")  # Debug
        pass
    
    pdf.set_font('Arial', 'B', 16)
    hotel_name = get_default_jam().nama_hotel or 'Hotel'
    pdf.cell(0, 10, 'Laporan Absensi ' + hotel_name, ln=True, align='C')
    pdf.ln(5)  # Add some space after title
    
    pdf.set_font('Arial', 'B', 10)
    for label, w in [('Nama',30),('Tanggal',30),('Masuk',25),('Pulang',25),('Status',30)]:
        pdf.cell(w, 8, label, 1)
    pdf.ln()
    pdf.set_font('Arial', '', 10)
    for a in absensis:
        pdf.cell(30, 8, a.user.nama if a.user else '-', 1)
        pdf.cell(30, 8, str(a.tanggal), 1)
        pdf.cell(25, 8, str(a.jam_masuk) if a.jam_masuk else '-', 1)
        pdf.cell(25, 8, str(a.jam_pulang) if a.jam_pulang else '-', 1)
        pdf.cell(30, 8, a.status, 1)
        pdf.ln()
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return send_file(
        BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='riwayat_absensi.pdf'
    )