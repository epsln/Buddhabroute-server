#! /usr/bin/env python3
import time
from os import mkdir, getcwd
from os.path import join

from apscheduler.schedulers.background import BackgroundScheduler
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, redirect, send_file, render_template
import numpy as np
import base64
from werkzeug.utils import secure_filename

from fractal import FractalManager

executor = ThreadPoolExecutor(4)
app = Flask(__name__)
fractal_mgr = FractalManager("~/.cache/buddhabroute-server-checkpoints/", "static/", (7105, 4960))
last_compute_time = time.time()
scheduler = BackgroundScheduler()
scheduler.add_job(func=fractal_mgr.compute_histograms, trigger="interval", seconds=  30)
scheduler.start()


@app.route('/checkpoint', methods=['PUT', 'POST'])
def upload_checkpoint():
    if 'uuid' not in request.json:
        return redirect('/', code=303)
    histogram = np.frombuffer(base64.b64decode(request.json['histogram']),dtype=np.float64)
    size = (int(request.json['shape'][0]), int(request.json['shape'][1]))
    histogram = np.reshape(histogram, size)
    np.save(join(fractal_mgr.input_dir, str(time.time())), histogram)
    if request.json['nickname'] is not "None":
        username = request.json['nickname']
    else:
        username = ""
    return {"message": f"Thanks ! {username} "}

@app.route('/', methods=['GET'])
def show_fractal():
    return render_template('index.html')

@app.route('/about', methods=['GET'])
def show_about():
    return render_template('about.html')

# launch app
if __name__ == '__main__':
    app.run()
