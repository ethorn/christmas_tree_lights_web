import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from time import sleep
from rq import Queue, Worker
import requests
from redis import Redis
from rq.command import send_stop_job_command
from rq.registry import StartedJobRegistry
from rq.suspension import suspend
import sqlite3

# TODO: A play function (start the python script)
# TODO: A queue system? Let the scripts run for X time before next one?
# TODO: https://stackoverflow.com/questions/62432369/flask-how-to-terminate-a-python-subprocess
# TODO: https://python-rq.org/docs/scheduling/

# TODO: provide arguments when starting the app to run in debug env file or not
load_dotenv(".env.debug")


def report_failure(job, connection, type, value, traceback):
    pass

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_files_from_db():
    conn = get_db_connection()
    files = conn.execute('SELECT * FROM christmas_files').fetchall()
    conn.close()
    return files


# Tell RQ what Redis connection to use
redis_conn = Redis()
q = Queue('christmasLightsQueue', connection=redis_conn)  # no args implies the default queue


UPLOAD_FOLDER = '../uploads'
ALLOWED_EXTENSIONS = {'py'}

template_dir = os.path.abspath('../frontend')
app = Flask(__name__, template_folder=template_dir)

app.config.from_mapping(
        SECRET_KEY='dev',
        #DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        UPLOAD_FOLDER=UPLOAD_FOLDER
    )



@app.route("/")
def index():
    return render_template('app.html')

@app.route("/upload", methods=['POST', 'GET'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('after_upload', filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

@app.route("/after_upload/<filename>")
def after_upload(filename=""):
    return "hej " + filename




def run_file(file=None):
    # Run the file.. which could, or could not, loop forever
    pass




@app.route("/file_list")
def file_list():
    # return file list from database as JSON
    pass

# CONTROLS
# What do I need a database for?
    # UPLOADED-TABLE: to keep track of uploaded files: name, by who, when, Rating, how many times it was played
    # PLAYLIST-TABLE: to keep track of the queue (actually do I need this? or just use rq?)
    # (MAYBE LATER) PLAYED-TABLE: 
    # DB: SQLite

# Frontend lists the uploaded files from UPLOADED-TABLE, every one has the buttons:
    # PlayNow (play it now, stop current one if there is one running)
        # place the job at_front
        # stop current job
    # Enqueue (place in queue)
        # place job in queue

# The queue/playlist (bottom bar with queue popup)
    # Shows currently playing with some animation
    # queue icon: Lists the current queue in a popup
    # play/stop on the same button (this just stops, but does not remove the current item)
        # Suspend worker
            # If there is currently a job running: this will work ok
            # If there is not currently a job running: then it will suspend after running the next job
                # Fix by: check first if there is a job running, and don't do anything if not
        # Add current job at_front in queue (get from database)
        # Stop current job
    # Prev (MAYBE IMPLEMENT LATER)
        # stop current job
        # Add the last item from PLAYED-TABLE to at_front in queue
    # Next
        # Stop current job
            # First check if there is a job running, if not, do nothnig
    # Clear list
        # Clear all jobs in queue



# DO I NEED A PLAYLIST DATABASE TABLE?
    # No. From the frontend I can just request the current job list (with descriptions), 
    # and then make a request for the metadata for these from the database
    # But, the performance would maybe be better if a PLAYLIST-TABLE is kept updated?
        # this also makes the playlist durable, i guess
        # but also makes it more complex.
        # I can do this if the performance becomes bad
    # PLAYLIST TABLE
        # id
        # name
        # queued at
        # ..
        # job id
    # can just keep this ordered as the job queue, and just get the whole table..


# OPTIONS WHEN ADDING JOBS:
    # depends_on=(job)
    # job_timeout=(maximum runtime before it is forced to "fail")
    # ttl=(max time a job is in queue)
    # at_front=True
    # on_success=
    # on_failure=
    # description="asd"

@app.route("/playNow", methods=["GET"]) #TODO: GET or just "file" argument
def playNow(file="test.py"):
    # Place this job as the first one in queue
    # TODO
    if isinstance(file, str):
        job = q.enqueue(
            run_file, 
            args=(file,), 
            description=file, 
            at_front=True,
            on_failure=report_failure,
            on_success=success,
            job_timeout=999999
            ) 

    # Stop current running job
    registry = StartedJobRegistry(connection=redis_conn)
    running_job_ids = registry.get_job_ids()
    current_job = running_job_ids[0] # with one running worker
    send_stop_job_command(redis_conn, current_job)

    return "something"

@app.route("/play")
def play():
    # resume
    pass

@app.route("/stop")
def stop():
    # IF there is currently a job running:
        # get current job id / file name
        # enqueue filerun(filename) at_front of queue
        # suspend IF not already suspended
        # stop current job
    pass

@app.route("/next")
def next():
    # stop current job
    pass

@app.route("/enqueue")
def enqueue():
    # Add to queue
    pass

@app.route("/clear")
def clear():
    # clear the whole queue
    pass

def success():
    pass

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS