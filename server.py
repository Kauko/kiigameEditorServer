import os
from flask import (Flask, request, send_from_directory,
                   abort, jsonify, render_template)
from werkzeug import secure_filename

VERBOSE = True
UPLOAD_FOLDER = 'static/uploads'
# Folder where resources that are shared between all games are stored
COMMONS_FOLDER = 'static/commons'
JAVASCRIPT_FOLDER = '/javascript'
ART_FOLDER = '/art'
# .html files should be removed from the allowed extensions at some point
# due to security concerns. The uploaded .html files are very basic,
# so we can just create it programmatically
ALLOWED_EXTENSIONS = set(
    ['md', 'json', 'mp3', 'ogg'
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

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

                # secure_filename makes sure there's no shenanigans
                # like ../../../my_credit_card_number
                filename = secure_filename(file.filename)
                # Get the directory path by removing the filename from
                # the full_path
                folder = full_path.replace(filename, '')
                # Combine it with the upload folder path
                upload_folder = os.path.join(
                    app.config['UPLOAD_FOLDER'], folder)

                if file.filename[-4:] == "html":
                    # If the folder did not exist, we know that
                    # we have to create the game.html too
                    create_game_html(upload_folder,
                                     upload_folder.split('/')[-2:][0])
                elif file and allowed_file(file.filename):
                    # Create the target directories if they don't exist
                    if not os.path.exists(upload_folder):
                        if VERBOSE:
                            print("Server :: Creating FOLDER " + upload_folder)
                        os.makedirs(upload_folder)
                    # File will be saved to this path
                    final_path = os.path.join(upload_folder, filename)
                    file.save(final_path)
                    if VERBOSE:
                        print('Server :: SAVED file to ' + final_path)
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


def create_game_html(path, gamename):
    rendered = render_template('game.html', game_name=gamename)
    if VERBOSE:
        print("Server :: Creating game.html of " + gamename +
              " to: " + path + "game.html")
    with open(path+"game.html", "wb") as f:
        f.write(bytes(rendered, 'UTF-8'))


# This route is not only used for accessing the games,
# it's also used by the games to get their required static content.
# This may not be the best way to do this, but it seems to work..
@app.route('/<game_name>/<path:filename>')
def get_game_files(game_name, filename):
    if filename[-3:] == ".js":
        return get_javascript_files(filename)
    else:
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
        if os.path.isfile(url+str(full_path[-1:][0])):
            return send_from_directory(url, str(full_path[-1:][0]))
        else:
            # If file is not found from the game's folder, try
            # the commons folder as a fallback
            return get_common_files(filename)


# This function is used to return javascript files. Javascript files
# should be located in the commons/javascript/ folder, as they should
# be shared by all games
def get_javascript_files(filename):
    if VERBOSE:
        print("Server :: Trying to find common javascript file " + filename)
    # filename is just a file name, or a <folder>/<filename>.js
    full_path = filename.split('/')
    # If the filename contains a folder, append it to the path
    url = COMMONS_FOLDER + JAVASCRIPT_FOLDER + '/' + '/'.join(full_path[:-1])
    if VERBOSE:
        print("Server :: Returning from: " +
              url + '/' + str(full_path[-1:][0]))
    return send_from_directory(url, str(full_path[-1:][0]))


# This function is used as a fallback to return static assets
# such as images and sound effects. Those files are typically found from
# the game folder, but if for some reason they're not, we can try looking
# for them from the commons/art folder.
# (When using the editor, users should first copy any assets to the
#  games folder, and then point to them with the editor. However, there's
#  nothing enforcing them to do this, so they may point somewhere else. In
#  that case, the assets are not uploaded to the folder. October 2014)
def get_common_files(full_path):
    filename = str(full_path.split('/')[-1:][0])
    print("Server :: WARNING, looking for " +
          filename + " from " + COMMONS_FOLDER + ART_FOLDER)
    for root, dirs, files in os.walk(COMMONS_FOLDER + ART_FOLDER):
        for f in files:
            if f == filename:
                if VERBOSE:
                    print("Server :: Returning " + root + '/' + filename)
                return send_from_directory(root, filename)
    print("Server :: File not found.")
    return False

if __name__ == '__main__':
    app.run()
