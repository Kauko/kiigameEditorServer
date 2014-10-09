import os
from flask import Flask, request, send_from_directory, abort, jsonify
from werkzeug import secure_filename

VERBOSE = True
UPLOAD_FOLDER = 'static/uploads'
# .html files should be removed from the allowed extensions at some point
# due to security concerns. The uploaded .html files are very basic,
# so we can just create it programmatically
ALLOWED_EXTENSIONS = set(
    ['js', 'md', 'json', 'mp3',
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'html'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# TURN DEBUG OFF IN PRODUCTION !!
app.debug = True


@app.route('/hello_world')
def hello_world():
    return 'Hello World!'

@app.route('/')
def front_page():
    return 'Welcome to the kiigame Server!'


def allowed_file(filename):
    if '.' not in filename:
        return True
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
def upload_file():
        if request.method == 'POST':
            success = False
            fails = {'failed_uploads': []}

            for full_path in request.files:
                file = request.files[full_path]
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    folder = full_path.replace(filename, '')
                    upload_folder = os.path.join(
                        app.config['UPLOAD_FOLDER'], folder)
                    if not os.path.exists(upload_folder):
                        if VERBOSE:
                            print("Server :: Creating FOLDER " + upload_folder)
                        os.makedirs(upload_folder)
                    final_path = os.path.join(upload_folder, filename)
                    if VERBOSE:
                        print("Server :: SAVING file to " + final_path)
                    file.save(final_path)
                    if VERBOSE and False:
                        print('Server :: Saved file to ' + final_path)
                    success = True
                else:
                    if VERBOSE:
                        print('Server :: Detected a ' +
                              'file that has a FORBIDDEN extension ' +
                              file.filename)
                    fails['failed_uploads'].append(full_path)

            if success and len(fails['failed_uploads']) == 0:
                return 'Uploaded the game'
            elif success:
                return jsonify(fails)
            else:
                abort(503)

        return

        '''
            for folder in request.files:
                for file in request.files[folder]:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        upload_folder = os.path.join(
                            app.config['UPLOAD_FOLDER'], folder)
                        if not os.path.exists(upload_folder):
                            os.makedirs(upload_folder)
                        final_path = os.path.join(upload_folder, filename)
                        file.save(final_path)
                        if VERBOSE:
                            print("Server :: Saved file to " + final_path)
                        success = True
                    else:
                        if VERBOSE:
                            print("Server :: " +
                                  "Detected a file that has a " +
                                  "forbidden extension: " +
                                  file.filename)
                        fails['failed_uploads'].append(folder + file.filename)

            if success and len(fails['failed_uploads']) == 0:
                return 'Uploaded the game'
            elif success:
                return jsonify(fails)
            else:
                abort(503)
        return'''


# This is from an example, probably not needed
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    print("Server :: uploaded_file " + filename)
    return send_from_directory(
        app.config['UPLOAD_FOLDER'] + '/gamedata/latkazombit', 'kiigame.html')

if __name__ == '__main__':
    app.run()
