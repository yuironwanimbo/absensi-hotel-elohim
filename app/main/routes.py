import os
import math
import base64
import json
from datetime import datetime, time
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Absensi, User, Pengaturan

bp = Blueprint('main', __name__)

def _parse_jam(val, default):
    try: parts = list(map(int, (val or '').split(':'))); return time(parts[0], parts[1] if len(parts) > 1 else 0)
    except: return default

def _get_jam():
    p = Pengaturan.query.first()
    if not p: return time(8,0), time(17,0)
    return _parse_jam(p.jam_masuk, time(8,0)), _parse_jam(p.jam_pulang, time(17,0))

_get_jam.cache = {}
def _get_jam_cached():
    if '_jam' not in _get_jam.cache:
        _get_jam.cache['_jam'] = _get_jam()
    return _get_jam.cache['_jam']

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

@bp.route('/')
@login_required
def index():
    today = datetime.now().date()
    absen = Absensi.query.filter_by(user_id=current_user.id, tanggal=today).first()
    today_label = (['Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu']
                   [datetime.now().weekday()]) + ', ' + \
                   datetime.now().strftime('%d %B %Y')
    return render_template('main/index.html', absen=absen, today_label=today_label)

@bp.route('/absen/masuk', methods=['POST'])
@login_required
def absen_masuk():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Data tidak valid'})
    
    lat = data.get('latitude')
    lng = data.get('longitude')
    foto_base64 = data.get('foto')
    
    hotel_lat = current_app.config['HOTEL_LAT']
    hotel_lng = current_app.config['HOTEL_LNG']
    radius = current_app.config['RADIUS_METERS']
    
    if lat is not None and lng is not None:
        distance = haversine_distance(float(lat), float(lng), hotel_lat, hotel_lng)
        if distance > radius:
            return jsonify({'success': False, 'message': f'Anda terlalu jauh dari hotel ({int(distance)}m). Radius maksimal {radius}m'})
    
    today = datetime.now().date()
    absen = Absensi.query.filter_by(user_id=current_user.id, tanggal=today).first()
    
    if absen and absen.jam_masuk:
        return jsonify({'success': False, 'message': 'Anda sudah absen masuk hari ini'})
    
    jam_sekarang = datetime.now().time()
    p = Pengaturan.query.first()
    jm = _parse_jam(p.jam_masuk  if p else None, time(8,0))
    jp = _parse_jam(p.jam_pulang if p else None, time(17,0))
    jam_masuk_hotel = jm
    
    status = 'hadir'
    if jam_sekarang > jam_masuk_hotel:
        status = 'terlambat'
    
    if absen:
        absen.jam_masuk = jam_sekarang
        absen.status = status
        absen.latitude = lat
        absen.longitude = lng
    else:
        absen = Absensi(
            user_id=current_user.id,
            jam_masuk=jam_sekarang,
            status=status,
            latitude=lat,
            longitude=lng
        )
        db.session.add(absen)
    
    if foto_base64:
        foto_data = base64.b64decode(foto_base64.split(',')[1])
        filename = f"masuk_{current_user.id}_{today.strftime('%Y%m%d')}.jpg"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        with open(upload_path, 'wb') as f:
            f.write(foto_data)
        absen.foto_masuk = filename
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Absen masuk berhasil!', 'status': status})

@bp.route('/absen/pulang', methods=['POST'])
@login_required
def absen_pulang():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Data tidak valid'})
    
    lat = data.get('latitude')
    lng = data.get('longitude')
    foto_base64 = data.get('foto')
    
    today = datetime.now().date()
    absen = Absensi.query.filter_by(user_id=current_user.id, tanggal=today).first()
    
    if not absen or not absen.jam_masuk:
        return jsonify({'success': False, 'message': 'Anda belum absen masuk hari ini'})
    
    if absen.jam_pulang:
        return jsonify({'success': False, 'message': 'Anda sudah absen pulang hari ini'})
    
    absen.jam_pulang = datetime.now().time()
    if lat is not None and lng is not None:
        absen.latitude = lat
        absen.longitude = lng
    
    if foto_base64:
        foto_data = base64.b64decode(foto_base64.split(',')[1])
        filename = f"pulang_{current_user.id}_{today.strftime('%Y%m%d')}.jpg"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        with open(upload_path, 'wb') as f:
            f.write(foto_data)
        absen.foto_pulang = filename
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Absen pulang berhasil!'})