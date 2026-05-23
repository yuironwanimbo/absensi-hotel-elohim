import os

# Face recognition disabled - using GPS-only attendance
# To enable face recognition, install opencv-python and face_recognition packages
# Note: These require C++ compiler on Windows

def enroll_face(user_id, output_path='app/static/uploads/user_faces'):
    os.makedirs(output_path, exist_ok=True)
    print(f"Face enrollment disabled. Please manually upload face photo to {output_path}/{user_id}_face.jpg")

def verify_face(user_id):
    return True, "Face verification skipped (GPS-only mode)"

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python face_utils.py enroll <user_id> | verify <user_id>")
    elif sys.argv[1] == 'enroll':
        enroll_face(sys.argv[2])
    elif sys.argv[1] == 'verify':
        success, msg = verify_face(sys.argv[2])
        print(msg)