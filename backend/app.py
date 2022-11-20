import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import subprocess as sp
from time import sleep
from rq import Queue, Worker
import requests
from redis import Redis
from rq.command import send_stop_job_command

# TODO: A play function (start the python script)
# TODO: A queue system? Let the scripts run for X time before next one?
# TODO: https://stackoverflow.com/questions/62432369/flask-how-to-terminate-a-python-subprocess
# TODO: https://python-rq.org/docs/scheduling/

# TODO: provide arguments when starting the app to run in debug env file or not
load_dotenv()


def count_words_at_url(url):
    resp = requests.get(url)
    return len(resp.text.split())

def report_failure(job, connection, type, value, traceback):
    pass


# Tell RQ what Redis connection to use
redis_conn = Redis()
q = Queue('christmasLightsQueue', connection=redis_conn)  # no args implies the default queue

worker = Worker([q], connection=redis_conn, name='foo')

# Delay execution of count_words_at_url('http://nvie.com')
job = q.enqueue(count_words_at_url, 'http://nvie.com', on_failure=report_failure)
print(job.result)   # => None  # Changed to job.return_value() in RQ >= 1.12.0

# Now, wait a while, until the worker is finished
sleep(2)
print(job.result)   # => 889  # Changed to job.return_value() in RQ >= 1.12.0

send_stop_job_command(redis_conn, job_id)


UPLOAD_FOLDER = '../uploads'
ALLOWED_EXTENSIONS = {'py'}

template_dir = os.path.abspath('../frontend')
app = Flask(__name__, template_folder=template_dir)

app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        UPLOAD_FOLDER=UPLOAD_FOLDER
    )



@app.route("/")
def index():
    return render_template('index.html')

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


@app.route("/pyfile", methods=['GET', 'POST'])
def pyfile():
    return "pyfile"

@app.route("/app")
def app_page(name=None):
    return render_template('app.html', name=name)

@app.route("/play")
def play(file="test.py"):

    status = sp.Popen.poll(g_sub_process) # status should be 'None'
    print(status)
    sleep(5)

    g_sub_process = sp.Popen(['python', f'../uploads/{file}']) # runs myPyScript.py 
    status = sp.Popen.poll(g_sub_process) # status should be 'None'
    print(status)
    sleep(5)
    status = sp.Popen.poll(g_sub_process) # status should be 'None'
    print(status)
    sp.Popen.terminate(g_sub_process) # closes the process
    status = sp.Popen.poll(g_sub_process) # status should now be something other than 'None' ('1' in my testing)
    print(status)
    sleep(1)
    status = sp.Popen.poll(g_sub_process) # status should now be something other than 'None' ('1' in my testing)
    print(status)

    return "check terminal"
    




def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS