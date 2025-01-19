from flask import Flask, jsonify, render_template, request, session
import os
from werkzeug.utils import secure_filename
import sqlite3
import threading
import tobii_research as tr

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Necessary for session handling
app.config['UPLOAD_FOLDER'] = 'static/uploads/'


# Global variable to store the eye tracker object and control the data streaming
my_eyetracker = None
is_streaming = False
gaze_data = None
global_data = {"username": None}
lock = threading.Lock()

def init_eyetracker():
    global my_eyetracker
    eyetrackers = tr.find_all_eyetrackers()
    if eyetrackers:
        my_eyetracker = eyetrackers[0]
        print("Eye tracker initialized:", my_eyetracker)
    else:
        print("No eye tracker found.")


if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET', 'POST'])
def upload_images():
    if request.method == 'POST':
        # Get the username from the form
        username = request.form['username'].capitalize()
        session['username'] = username  # Store username in session

        # Store the username in the global storage
        with lock:
            global_data["username"] = username

        image1 = request.files['image1']
        image2 = request.files['image2']

        if image1 and image2:
            image1_filename = secure_filename(image1.filename)
            image2_filename = secure_filename(image2.filename)

            image1.save(os.path.join(app.config['UPLOAD_FOLDER'], image1_filename))
            image2.save(os.path.join(app.config['UPLOAD_FOLDER'], image2_filename))

            return render_template('display_images.html', image1=image1_filename, image2=image2_filename, username=username)

    return render_template('index.html')

@app.route('/logout', methods=['POST'])
def logout():
    stop_eyetracker()
    session.clear()
    with lock:
        global_data["username"] = None  # Clear the username from global storage
    return render_template('index.html')


def init_db():
    conn = sqlite3.connect('areas_of_interest.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS paths
                 (id INTEGER PRIMARY KEY,
                  username TEXT,
                  path TEXT)''')
    conn.commit()
    conn.close()

def create_user_table(username):
    conn = sqlite3.connect('areas_of_interest.db')
    c = conn.cursor()

    table_name = f"box_pairs_{username}"
    c.execute(f'''CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY,
                    code_left INTEGER,
                    code_top INTEGER,
                    code_width INTEGER,
                    code_height INTEGER,
                    graph_left INTEGER,
                    graph_top INTEGER,
                    graph_width INTEGER,
                    graph_height INTEGER
                  )''')
    conn.commit()
    conn.close()

# Insert specific values into a user's table
def insert_specific_values(username, specific_values):
    conn = sqlite3.connect('areas_of_interest.db')
    c = conn.cursor()
    table_name = f"box_pairs_{username}"
    c.execute(f"DELETE FROM {table_name}")
    for record in specific_values:
        c.execute(f'''INSERT INTO {table_name}
                      (code_left, code_top, code_width, code_height,
                       graph_left, graph_top, graph_width, graph_height)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', record)
    conn.commit()
    conn.close()

# Values for code1 (user1 up to user10 AND user21 up to user30)
values_first = [
    (158, 91, 162, 107, 182, 143, 86, 51),
    (198, 214, 473, 88, 180, 208, 97, 51),
    (260, 311, 164, 32, 181, 275, 90, 53),
    (203, 376, 119, 35, 182, 343, 94, 52),
    (244, 430, 105, 32, 89, 414, 88, 49),
    (244, 524, 113, 37, 281, 416, 88, 50),
    (201, 594, 377, 59, 192, 481, 79, 46),
    (205, 665, 108, 35, 192, 543, 91, 55),
    (358, 666, 108, 35, 191, 612, 91, 56),
    (243, 721, 100, 49, 189, 684, 102, 56),
    (246, 837, 101, 55, 373, 607, 112, 56),
    (164, 916, 602, 117, 187, 757, 115, 56)
]

# Values for code2 (user11 up to user20 AND user31 up to user40)
values_second = [
    (158, 91, 439, 177, 176, 145, 91, 46),
    (202, 283, 134, 36, 177, 207, 93, 54),
    (244, 339, 106, 50, 98, 284, 81, 55),
    (247, 458, 101, 49, 252, 286, 81, 52),
    (200, 554, 460, 71, 173, 358, 94, 56),
    (258, 645, 114, 39, 176, 435, 94, 55),
    (200, 695, 114, 31, 180, 514, 88, 54),
    (356, 696, 111, 35, 187, 593, 94, 55),
    (240, 744, 121, 34, 178, 668, 89, 52),
    (241, 843, 129, 42, 350, 588, 118, 58),
    (164, 905, 545, 135, 181, 741, 100, 65)
]

# Insert data for users User1 up to User10 (code1)
for i in range(1, 11):
    username = f"User{i}"
    create_user_table(username)
    insert_specific_values(username, values_first)

# Insert data for users User11 up to User20 (code2)
for i in range(41, 43):
    username = f"User{i}"
    create_user_table(username)
    insert_specific_values(username, values_second)

# Insert data for users User21 up to User30 (code1)
for i in range(43, 45):
    username = f"User{i}"
    create_user_table(username)
    insert_specific_values(username, values_first)

# Insert data for users User31 up to User40 (code2)
for i in range(45, 47):
    username = f"User{i}"
    create_user_table(username)
    insert_specific_values(username, values_second)

def create_gaze_matches_table(username):
    conn = sqlite3.connect('areas_of_interest.db')
    c = conn.cursor()

    table_name = f"gaze_matches_{username}"
    c.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            gaze_x INTEGER NOT NULL,
            gaze_y INTEGER NOT NULL,
            matched_box_id INTEGER,
            matched_box_type TEXT,
            box_left INTEGER,
            box_top INTEGER,
            box_width INTEGER,
            box_height INTEGER
        )
    ''')
    conn.commit()
    conn.close()



@app.route('/save_box_pair', methods=['POST'])
def save_box_pair():
    data = request.json
    code_box = data.get('codeBox')
    graph_box = data.get('graphBox')
    username = session.get('username') 

    if not username or not code_box or not graph_box:
        return jsonify({"status": "error", "message": "Incomplete data received"}), 400

    create_user_table(username)
    table_name = f"box_pairs_{username}"

    try:
        print("Received code_box:", code_box)
        print("Received graph_box:", graph_box)

        # Extract and convert values to integers
        code_left = int(code_box['left'])
        code_top = int(code_box['top'])
        code_width = int(code_box['width'])
        code_height = int(code_box['height'])

        graph_left = int(graph_box['left'])
        graph_top = int(graph_box['top'])
        graph_width = int(graph_box['width'])
        graph_height = int(graph_box['height'])

        conn = sqlite3.connect('areas_of_interest.db')
        c = conn.cursor()

        c.execute(f"""
            INSERT INTO {table_name}
            (code_left, code_top, code_width, code_height, graph_left, graph_top, graph_width, graph_height)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (code_left, code_top, code_width, code_height, graph_left, graph_top, graph_width, graph_height))

        conn.commit()
        conn.close()

        print("Box pair saved successfully.")
        return jsonify({"status": "success"})

    except Exception as e:
        print("Error saving box pair:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_coordinates_for_path', methods=['POST'])
def get_coordinates_for_path():
    data = request.json
    path = data.get('path')  # Path string, e.g., "1-2-3-4"
    username = session.get('username') 

    if not path or not username:
        return jsonify({'status': 'error', 'message': 'No path or user provided'}), 400

    # Convert path into list of IDs (e.g., "1-2-3-4" becomes [1, 2, 3, 4])
    node_ids = [int(node) for node in path.split('-')]
    table_name = f"box_pairs_{username}"

    try:
        conn = sqlite3.connect('areas_of_interest.db')
        c = conn.cursor()

        # Use placeholders to query only the specific IDs we need
        placeholders = ', '.join(['?'] * len(node_ids))
        query = f"""
            SELECT id, code_left, code_top, code_width, code_height,
                   graph_left, graph_top, graph_width, graph_height
            FROM {table_name}
            WHERE id IN ({placeholders})
            ORDER BY id ASC
        """

        c.execute(query, node_ids)
        results = c.fetchall()
        conn.close()

        # Format results for the response
        boxes = [
            {
                'id': row[0],
                'code_left': row[1], 'code_top': row[2],
                'code_width': row[3], 'code_height': row[4],
                'graph_left': row[5], 'graph_top': row[6],
                'graph_width': row[7], 'graph_height': row[8]
            }
            for row in results
        ]
        return jsonify({'status': 'success', 'boxes': boxes})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/save_paths', methods=['POST'])
def save_paths():
    data = request.json
    paths = data.get('paths')
    username = session.get('username')

    if not username or not paths:
        return jsonify({"status": "error", "message": "Incomplete data"}), 400

    try:
        conn = sqlite3.connect('areas_of_interest.db')
        c = conn.cursor()

        # Insert each path for the user
        for path in paths:
            c.execute("INSERT INTO paths (username, path) VALUES (?, ?)", (username, path))

        conn.commit()
        conn.close()

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

EXPORT_FOLDER = 'C:/Users/User/Desktop/metsi/MAIN_1'

@app.route('/export_comments', methods=['POST'])
def export_comments():
    data = request.json
    comments = data.get('comments', [])
    username = session.get('username')

    if not comments:
        return jsonify({'status': 'error', 'message': 'No comments to export'}), 400

    try:
        export_file_path = os.path.join(EXPORT_FOLDER, 'exported_comments.txt')
        with open(export_file_path, 'a') as f:
            f.write(f'Username: {username}\n\n')
            for index, item in enumerate(comments, start=1):
                f.write(f"Path{index}: {item['path']}\nComment: {item['comment']}\n\n")

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/start_eyetracker', methods=['POST'])
def start_eyetracker():
    global is_streaming
    if my_eyetracker and not is_streaming:
        is_streaming = True
        threading.Thread(target=stream_gaze_data).start()
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Eye tracker not initialized or already streaming"}), 400


def gaze_data_callback(new_gaze_data):
    global gaze_data
    left_gaze = new_gaze_data.get('left_gaze_point_on_display_area')
    right_gaze = new_gaze_data.get('right_gaze_point_on_display_area')

    if left_gaze and right_gaze:
        # Compute the average gaze point for both eyes
        avg_x_normalized = (left_gaze[0] + right_gaze[0]) / 2
        avg_y_normalized = (left_gaze[1] + right_gaze[1]) / 2

        # Convert normalized gaze coordinates to pixel coordinates
        avg_x = int(avg_x_normalized * 1920)  # Assuming 1920x1080 screen
        avg_y = int(avg_y_normalized * 1080)

        gaze_data = {"x": avg_x, "y": avg_y}

        print(f"Gaze coordinates: (x={avg_x}, y={avg_y})")

        # Check if the gaze coordinates match any AOI
        matched_boxes = check_gaze_in_aoi(avg_x, avg_y)

        # If matched boxes found, add them to gaze data for visualization
        if matched_boxes:
            print(f"Matched AOIs: {matched_boxes}")
            gaze_data['matched_boxes'] = matched_boxes
        else:
            print("No AOI matched.")
            gaze_data['matched_boxes'] = []


current_user = None

def check_gaze_in_aoi(x, y):
    global matched_boxes, current_user 

    try:
        with lock:
            username = global_data.get("username")
        if not username:
            print("No username found.")
            return []

        # Clear the matched_boxes list for each new gaze coordinate pair
        matched_boxes = []

        if username != current_user:
            current_user = username

        print(f"Username found: {username}")

        # Offsets for code and graph sections
        offsets = {
            "code": {"left": 0, "top": 0},
            "graph": {"left": 960, "top": 0}, 
        }

        conn = sqlite3.connect('areas_of_interest.db')
        c = conn.cursor()
        print("Database connection established.")

        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        print(f"Available tables: {tables}")

        # Prepare the table name for the specific user
        table_name = f"box_pairs_{username}"
        print(f"Using table name: {table_name}")

        # Query to retrieve AOI boxes
        c.execute(f"""
            SELECT id, code_left, code_top, code_width, code_height,
                   graph_left, graph_top, graph_width, graph_height
            FROM {table_name}
        """)
        boxes = c.fetchall()
        print(f"Boxes retrieved from table {table_name}: {boxes}")

        # Check each AOI box
        for box in boxes:
            print(f"Checking box: {box}")
            box_id, code_left, code_top, code_width, code_height, graph_left, graph_top, graph_width, graph_height = box

            # Adjust gaze coordinates relative to code and graph sections
            code_gaze_x = x
            code_gaze_y = y
            graph_gaze_x = x
            graph_gaze_y = y

            # Apply offsets for graph AOI
            graph_left += offsets["graph"]["left"]
            # Check if gaze falls within the code-container AOI
            if (code_gaze_x >= code_left and code_gaze_x <= code_left + code_width and
                code_gaze_y >= code_top and code_gaze_y <= code_top + code_height):
                matched_boxes.append({
                    "id": box_id,
                    "type": "code",
                    "left": code_left,
                    "top": code_top,
                    "width": code_width,
                    "height": code_height
                })
                print(f"Gaze matched a code-container box at: (left={code_left}, top={code_top}).")
                save_gaze_match(conn, username, code_gaze_x, code_gaze_y, box_id, "code", {
                    "left": code_left,
                    "top": code_top,
                    "width": code_width,
                    "height": code_height
                })

            # Check if gaze falls within the graph-container AOI
            if (graph_gaze_x >= graph_left and graph_gaze_x <= graph_left + graph_width and
                graph_gaze_y >= graph_top and graph_gaze_y <= graph_top + graph_height):
                matched_boxes.append({
                    "id": box_id,
                    "type": "graph",
                    "left": graph_left,
                    "top": graph_top,
                    "width": graph_width,
                    "height": graph_height
                })
                print(f"Gaze matched a graph-container box at: (left={graph_left}, top={graph_top}).")
                save_gaze_match(conn, username, graph_gaze_x, graph_gaze_y, box_id, "graph", {
                    "left": graph_left,
                    "top": graph_top,
                    "width": graph_width,
                    "height": graph_height
                })


        conn.close()
        print("Database connection closed.")

        return matched_boxes

    except sqlite3.Error as db_error:
        print(f"Database error: {str(db_error)}")
        return []

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []

def save_gaze_match(conn, username, gaze_x, gaze_y, box_id, box_type, box_coords):
    """Save gaze match data into the user-specific table."""
    try:
        create_gaze_matches_table(username)
        c = conn.cursor()

        table_name = f"gaze_matches_{username}"
        c.execute(f"""
            INSERT INTO {table_name} (gaze_x, gaze_y, matched_box_id, matched_box_type, box_left, box_top, box_width, box_height)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (gaze_x, gaze_y, box_id, box_type, box_coords['left'], box_coords['top'], box_coords['width'], box_coords['height']))
        conn.commit()
        print(f"Saved gaze match for {username}: (x={gaze_x}, y={gaze_y}, box_id={box_id}, type={box_type})")
    except Exception as e:
        print(f"Error saving gaze match: {str(e)}")


@app.route('/get_aoi_by_id', methods=['GET'])
def get_aoi_by_id():
    username = session.get('username')
    if not username:
        return jsonify({'status': 'error', 'message': 'No user logged in'}), 400

    aoi_id = request.args.get('id', type=int)
    if not aoi_id:
        return jsonify({'status': 'error', 'message': 'Invalid or missing AOI ID'}), 400

    table_name = f"box_pairs_{username}"

    try:
        conn = sqlite3.connect('areas_of_interest.db')
        c = conn.cursor()

        # Query to fetch AOI by id
        c.execute(f"""
            SELECT code_left, code_top, code_width, code_height,
                   graph_left, graph_top, graph_width, graph_height
            FROM {table_name}
            WHERE id = ?
        """, (aoi_id,))
        result = c.fetchone()
        conn.close()

        if not result:
            return jsonify({'status': 'error', 'message': 'No AOI found for the given ID'})

        # Adjust graph coordinates to be relative to the container
        graph_container_left = 960
        graph_left_relative = result[4] + graph_container_left

        aoi_data = {
            'code': {
                'box_left': result[0],
                'box_top': result[1],
                'box_width': result[2],
                'box_height': result[3],
            },
            'graph': {
                'box_left': graph_left_relative,
                'box_top': result[5],
                'box_width': result[6],
                'box_height': result[7],
            }
        }
        return jsonify({'status': 'success', 'aoi': aoi_data})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/get_latest_match', methods=['GET'])
def get_latest_match():
    username = session.get('username')
    if not username:
        return jsonify({'status': 'error', 'message': 'No user logged in'}), 400

    table_name = f"gaze_matches_{username}"

    try:
        conn = sqlite3.connect('areas_of_interest.db')
        c = conn.cursor()

        # Get the latest matched_box_id
        query = f"""
            SELECT matched_box_id
            FROM {table_name}
            ORDER BY timestamp DESC
            LIMIT 1
        """
        c.execute(query)
        result = c.fetchone()
        conn.close()

        if not result:
            return jsonify({'status': 'error', 'message': 'No matches found'})

        return jsonify({'status': 'success', 'match': {'matched_box_id': result[0]}})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500



def stream_gaze_data():
    global my_eyetracker
    if my_eyetracker:
        my_eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze_data_callback, as_dictionary=True)

def stop_eyetracker():
    global my_eyetracker, is_streaming
    if my_eyetracker and is_streaming:
        my_eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze_data_callback)
        is_streaming = False
        print("Eye tracker stopped.")

init_eyetracker()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
