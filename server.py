import os
from flask import (Flask, request, send_from_directory,
                   abort, jsonify, render_template)
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


@app.route('/')
def front_page():
    # First create a dict of all game files ( game_name : path/to/kiigame.html)
    games = find_html_files()
    # Send the dict to the template, that will create a simple list of links
    return render_template('index.html', games=games)


# Creates a { game_name: path/to/kiigame.html } dict
def find_html_files():
    ret = {}
    # Walk through the uploads folder
    struct = os.walk(app.config['UPLOAD_FOLDER'])
    for root, dirs, files in struct:
        # Check each file in this folder
        for f in files:
            # If the file is a html file, we should save it
            # If not, we can just move on
            # We split the root because we want it to be just
            # game_name/, not UPLOAD_FOLDER/something/foo/game_name/
            if '.' in f and f.rsplit('.', 1)[1] == 'html':
                ret[root.rsplit('/', 1)[1]] = root.rsplit('/', 1)[1] + '/' + f
    if VERBOSE:
        print('Server :: Got game files:')
        for root in ret:
            print('  * ' + root + ' - ' + ret[root])
    return ret


# Checks that the file has an allowed extensions
# Is mostly a security feature..
def allowed_file(filename):
    if '.' not in filename:
        return True
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# NOTE: Uploading files overwrites existing files, but
# files are never removed. Pretty sure there's no need to
# remove any files ever, but this is just something one should
# keep in mind
@app.route('/upload', methods=['POST'])
def upload_game():
        if request.method == 'POST':
            # The success flag is set to True immediately when at least
            # one file is successfully uploaded
            success = False
            # If any uploads fail they will be added to this array
            fails = {'failed_uploads': []}

            # The request.files is a dict with the following sctructure:
            # { path/to/file.foo : File }
            for full_path in request.files:
                file = request.files[full_path]
                if file and allowed_file(file.filename):
                    # secure_filename makes sure there's no shenanigans
                    # like ../../../my_credit_card_number
                    filename = secure_filename(file.filename)
                    # Get the directory path by removing the filename from
                    # the full_path
                    folder = full_path.replace(filename, '')
                    # Combine it with the upload folder path
                    upload_folder = os.path.join(
                        app.config['UPLOAD_FOLDER'], folder)
                    # Create the target directories if they don't exist
                    if not os.path.exists(upload_folder):
                        if VERBOSE:
                            print("Server :: Creating FOLDER " + upload_folder)
                        os.makedirs(upload_folder)
                    # File will be saved to this path
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


# This route is not only used for accessing the games,
# it's also used by the games to get their required static content.
# This may not be the best way to do this, but it seems to work..
@app.route('/<game_name>/<path:filename>')
def get_game_files(game_name, filename):
    # game_name is a single string, like "latkazombit"
    # filename is a single filename, like "kiigame.html",
    # or it may be a file in a subfolder, like "Kinetic/kinetic.js"
    if VERBOSE and False:
        print(" **** ")
        print("#1 game_name: " + game_name + ", filename: " + filename)
    # filename may contain a subfolder, so we need to split it
    full_path = filename.split('/')
    if VERBOSE and False:
        print('#2 full_path: ' + str(full_path))
    url = (app.config['UPLOAD_FOLDER'] + '/gamedata/' +
           game_name + '/' + '/'.join(full_path[:-1]))
    # If the filename was just a single file, the url will now be
    # <UPLOAD_FOLDER>/gamedata/<game_name>/
    # If it contained a subfolder, like Kinetic/kinetic.js,
    # the url will be:
    # <UPLOAD_FOLDER>/gamedata/<game_name>/Kinetic/
    if VERBOSE and False:
        print('#3 url: ' + url)
        print("#4 Returning file: " + str(full_path[-1:][0]))
    # str(full_path[-1:][0]) always points to the filename
    # This works when there are 0 or n subfolders :)
    return send_from_directory(url, str(full_path[-1:][0]))

if __name__ == '__main__':
    app.run()
