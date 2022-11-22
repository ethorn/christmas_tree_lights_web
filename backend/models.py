def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_files_from_db():
    conn = get_db_connection()
    files = conn.execute('SELECT * FROM christmas_files').fetchall()
    conn.close()
    return files

def query_all_uploaded_files():
    # TODO
    pass




def run_file(file=None):
    # Run the file.. which could, or could not, loop forever
    pass

def success():
    pass

def report_failure(job, connection, type, value, traceback):
    pass

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
