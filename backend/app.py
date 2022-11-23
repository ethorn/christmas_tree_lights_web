import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from time import sleep
from rq import Queue, Worker
from redis import Redis
from rq.command import send_stop_job_command
from rq.registry import StartedJobRegistry
from rq.suspension import suspend, resume
import sqlite3

from models import *

# TODO: provide arguments when starting the app to run in debug env file or not
load_dotenv(".env.debug")

# Config
UPLOAD_FOLDER = '../uploads'
ALLOWED_EXTENSIONS = {'py'}
TEMPLATE_DIR = os.path.abspath('../frontend')

# RQ
redis_conn = Redis()
q = Queue('christmasLightsQueue', connection=redis_conn)  # no args implies the default queue

# App setup
app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config.from_mapping(
        SECRET_KEY='dev',
        UPLOAD_FOLDER=UPLOAD_FOLDER
)





# TODO: Se på SOCKET.IO for å oppdatere frontend med updates fra backend



# Routes
@app.route("/")
def index():
    # TODO: Get all data from playlist and files, and pass them on to the template for Jinja
    # TODO: OR, just call these things from the Frontend?
    return render_template('app.html')

@app.route("/security")
def security():
    return render_template('security.html') # TODO

@app.route("/upload", methods=['POST', 'GET'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']

        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename) #TODO: Allow unsecure filenames?
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # TODO: Add the file to the test queue
            return redirect(url_for('after_upload', filename=filename))

    return render_template('upload.html')

@app.route("/after_upload/<filename>")
def after_upload(filename=""):
    # TODO: IF it has not been tested yet, print out: "Waiting for tests to finish..."
        # Check in database I guess
    # TODO: ELSE if finished, print out: "TEST PASSED, Now you can play it. <Go to app.>"
        
    return "hej " + filename

@app.route("/files")
@app.route("/files/<id:int>", methods=['GET', 'DELETE'])
def files(id=None):
    if request.method == "GET" and id is None:
        files = query_all_files() # TODO
        return jsonify(files)
    elif request.method == "GET" and id is int:
        file = query_file(id=id) # TODO
        return jsonify(file)
    elif request.method == "DELETE":
        result = delete_file(id=id) # TODO
        return jsonify(result)

# @app.route("files/<id>/play")
# def play_file():
#     result = resume(connection=redis_conn)
#     return result # True if resumed, False if already resumed I guess
    

# CONTROLS
# What do I need a database for?
    # UPLOADED-TABLE: to keep track of uploaded files: name, by who, when, Rating, how many times it was played
    # PLAYLIST-TABLE: to keep track of the queue (actually do I need this? or just use rq?)

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
    # Next
    # Clear list



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
    # on_success=update_frontend
    # on_failure=update_frontend
    # description="asd"

@app.route("/playlist", methods=["GET", "POST"])
def playlist():
    if request.method == "GET":
        queued_jobs = q.jobs
        playlist = []
        for job in queued_jobs:
            playlist.append(job.meta)
        return jsonify(playlist)

    elif request.method == "POST":
        if isinstance(request.data.file, str):
            # TODO: CHECK IF FILE IS IN FILE LIST IN DATABASE?
            job = q.enqueue(
                run_file, 
                args=(request.data.file,), 
                description=request.data.file, 
                at_front=True,
                on_failure=report_failure, # TODO
                on_success=success, # TODO
                job_timeout=999999 # TODO
                ) 
        # Stop current running job
        registry = StartedJobRegistry(connection=redis_conn)
        running_job_ids = registry.get_job_ids()
        if len(running_job_ids) > 0:
            current_job_id = running_job_ids[0] # with one running worker
            send_stop_job_command(redis_conn, current_job_id)
        return "something" # TODO

@app.route("/playlist/next") # TODO: POST? GET?
def next():
    registry = StartedJobRegistry(connection=redis_conn)
    running_job_ids = registry.get_job_ids()
    if len(running_job_ids) > 0:
        current_job_id = running_job_ids[0] # with one running worker
        send_stop_job_command(redis_conn, current_job_id)
    pass

@app.route("/playlist/enqueue", methods=["POST"]) # TODO: Have it under files OR playlist as POST
def enqueue():
    if request.method == "POST":
        job = q.enqueue(
            run_file, 
            args=(request.data.file,), 
            description=request.data.file, 
            at_front=True,
            on_failure=report_failure,
            on_success=success,
            job_timeout=999999
        ) 
    return jsonify(job)

@app.route("playlist/play", methods=["POST"])
def play():
    if request.method == "POST":
        result = resume(connection=redis_conn)
        return result # True if resumed, False if already resumed I guess

@app.route("playlist/stop", methods=["POST"])
def stop():
    if request.method == "POST":
        registry = StartedJobRegistry(connection=redis_conn)
        running_job_ids = registry.get_job_ids()
        # IF there is currently a job running:
        if len(running_job_ids) > 0:
            # get current job id / file name
            current_job_id = running_job_ids[0] # with one running worker
            # enqueue filerun(filename) at_front of queue
            # TODO: get filename from playlist by filtering by job id?
            # TODO: enqueue
            # job = q.enqueue(
            #         run_file, 
            #         args=(request.data.file,), 
            #         description=request.data.file, 
            #         at_front=True,
            #         on_failure=report_failure,
            #         on_success=success,
            #         job_timeout=999999
            #     ) 
            # suspend IF not already suspended
            suspend(connection=redis_conn)
            # stop current job
            send_stop_job_command(redis_conn, current_job_id)
    pass

@app.route("/playlist/<id>", methods=["DELETE"])
def delete_playlist_item():
    # TODO
    pass

@app.route("/playlist/<id>/play", methods=["POST"])
def play_playlist_item():
    # TODO: Remove everyone before
    # TODO: Abort current job
    # (Now this one should be playing)
    pass

@app.route("/playlist/clear", method=["POST"])
def clear():
    q.empty()
    pass



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)