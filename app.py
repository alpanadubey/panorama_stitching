import os, shutil, cv2, random
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from stitcher import stitch_images

app = Flask(__name__)
app.secret_key = 'alpana_secret_key'
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def clear_folders():
    shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    for f in ['output.jpg', 'matched.jpg']:
        try:
            os.remove(os.path.join(STATIC_FOLDER, f))
        except FileNotFoundError:
            pass

def resize_image(img, max_width=1024):
    if img.shape[1] > max_width:
        scale = max_width / img.shape[1]
        new_size = (int(img.shape[1] * scale), int(img.shape[0] * scale))
        return cv2.resize(img, new_size)
    return img
    
@app.route('/stitch', methods=['GET'])
def stitch_block():
    return redirect(url_for('index'))

@app.route('/')
def index():
    output = session.pop('output', False)
    error = session.pop('error', None)
    return render_template('index.html', output=output, error=error, random=random.random)

@app.route('/stitch', methods=['POST'])
def stitch():
    clear_folders()
    files = [request.files.get(f'image{i}') for i in range(1, 3)]
    descriptor = request.form.get('descriptor', 'sift')
    paths = []

    for f in files:
        if not f:
            session['error'] = "Both images are required."
            return redirect(url_for('index'))
        path = os.path.join(UPLOAD_FOLDER, secure_filename(f.filename))
        f.save(path)
        paths.append(path)

    try:
        img1 = resize_image(cv2.imread(paths[0]))
        img2 = resize_image(cv2.imread(paths[1]))
        stitched = stitch_images(img1, img2, descriptor)
        cv2.imwrite('static/output.jpg', stitched)
        session['output'] = True
    except MemoryError:
        session['error'] = "Stitching failed: Server ran out of memory. Try smaller images."
    except Exception as e:
        session['error'] = f"Stitching failed: {str(e)}"

    return redirect(url_for('index'))

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
