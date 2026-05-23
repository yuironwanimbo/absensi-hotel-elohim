from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()
    
    if not User.query.filter_by(email='admin@hotel.com').first():
        admin = User(
            nama='Admin Hotel',
            email='admin@hotel.com',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
    
    if not User.query.filter_by(email='hrd@hotel.com').first():
        hrd = User(
            nama='HRD Hotel',
            email='hrd@hotel.com',
            role='hrd'
        )
        hrd.set_password('hrd123')
        db.session.add(hrd)
    
    if not User.query.filter_by(email='karyawan@hotel.com').first():
        karyawan = User(
            nama='Karyawan Test',
            email='karyawan@hotel.com',
            role='karyawan'
        )
        karyawan.set_password('karyawan123')
        db.session.add(karyawan)
    
    db.session.commit()
    print('Database initialized!')
    print('Users created:')
    print('  Admin: admin@hotel.com / admin123')
    print('  HRD: hrd@hotel.com / hrd123')
    print('  Karyawan: karyawan@hotel.com / karyawan123')