from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from PIL import Image, ExifTags
import threading
import os
import glob

app = Flask(__name__, '/static')
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

def delete_file_after_delay(filepath, delay):
    def delayed_delete():
        import time
        time.sleep(delay)
        try:
            os.remove(filepath)
            print(f"Arquivo {filepath} deletado com sucesso.")
        except Exception as e:
            print(f"Erro ao deletar o arquivo: {e}")
    threading.Thread(target=delayed_delete).start()


def cleanup_uploads_folder():
    files = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], '*'))
    for f in files:
        try:
            os.remove(f)
        except Exception as e:
            print(f"Erro ao deletar arquivo remanescente: {e}")


def correct_image_orientation(image):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation)
            if orientation_value == 3:
                image = image.rotate(180, expand=True)
            elif orientation_value == 6:
                image = image.rotate(-90, expand=True)
            elif orientation_value == 8:
                image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return image

@app.route('/')
def index():
    cleanup_uploads_folder()
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        user_image = Image.open(filename)

        base_image = Image.open('static/base_image.png')

        base_image = base_image.resize(user_image.size)

        user_image.paste(base_image, (0, 0), base_image)

        user_image.save(filename)

        return redirect(url_for('uploaded_file', filename=file.filename))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return render_template('uploaded.html', filename=filename)


@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(filepath):

        response = send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
        
        delete_file_after_delay(filepath, 2)
        
        return response
    else:
        return redirect(url_for('index'))
    

if __name__ == '__main__':
    app.run()
