import os, shutil, cv2, random, smtplib
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from stitcher import stitch_images

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



def clear_folders():
    shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    for f in ['output.jpg', 'matched.jpg']:
        try: os.remove(os.path.join(STATIC_FOLDER, f))
        except FileNotFoundError: pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stitch', methods=['POST'])
def stitch():
    clear_folders()
    files = [request.files.get(f'image{i}') for i in range(1, 3)]
    descriptor = request.form.get('descriptor', 'sift')
    paths = []

    for f in files:
        path = os.path.join(UPLOAD_FOLDER, secure_filename(f.filename))
        f.save(path)
        paths.append(path)

    img1 = cv2.imread(paths[1])
    img2 = cv2.imread(paths[0])
    stitched = stitch_images(img1, img2, descriptor)
    cv2.imwrite('static/output.jpg', stitched)

    return render_template('index.html', output=True, random=random.random)



if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
