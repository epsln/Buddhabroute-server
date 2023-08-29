#! /usr/bin/env python3
import time
import configparser, argparse
import logging
import sys
from os import makedirs, getcwd
from os.path import join
from pathlib import Path

import numpy as np

from flask import Flask, request, redirect, send_file
from concurrent.futures import ThreadPoolExecutor
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler


from fractal import FractalManager

app = Flask(__name__)
logger = logging.getLogger("__name__")

def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="description")
    parser.add_argument(
        "--debug",
        help="set the log level to DEBUG",
        action="store_true",
    )
    return parser.parse_args()

def configure_logger(debug, dryrun=False, log_prefix=None):
    """Configure the logger."""
    log_dir = Path.home() / f"{Path(__file__).stem}_LOG"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{time.strftime('%Y%m%d')}.log"
    log_format = ( 
        f"%(asctime)s{' - DRYRUN' if dryrun else ''} - %(levelname)s - {log_prefix if log_prefix else ''}%(message)s"
    )   
    logging.basicConfig(
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
        handlers=[logging.StreamHandler(), logging.FileHandler(log_file)],
        force=True,
    )   
    if debug:
        logger.setLevel(logging.DEBUG)
    logging.getLogger("sh").setLevel(logging.WARNING)

def parse_configuration(data_model):
    """Check and parse config file."""
    #cfg_file = Path.home() / f".{Path(__file__).stem}.cfg"
    cfg_file = 'configs/server.conf'
    #if not cfg_file.is_file():
    #    logger.error(f'could not find the config file "{cfg_file}"')
    #    sys.exit(1)
    raw_config = configparser.ConfigParser()
    raw_config.read(cfg_file)
    config = {section: dict.fromkeys(data_model[section]) for section in data_model}
    try:
        for section in config:
            for item in config[section]:
                config[section][item] = raw_config.get(section, item)
    except (configparser.NoSectionError, configparser.NoOptionError) as err:
        logger.error(f"Invalid configuration: {err}")
        sys.exit(1)
    return config

@app.route('/status', methods=['GET'])
def check_app_status():
    return "App server running"

@app.route('/checkpoint', methods=['POST'])
def upload_checkpoint():
    """API endpoint to upload computed checkpoint by screensaver clients"""
    logger.debug(f'Request : {request.form}')
    if 'uuid' not in request.json: #TODO: validate json against a format
        logger.debug(f'invalid request : No uuid !')
        return redirect('/', code=303)

    histogram = np.frombuffer(base64.b64decode(request.json['histogram']),dtype=np.float64)
    size = (int(request.json['shape'][0]), int(request.json['shape'][1]))
    histogram = np.reshape(histogram, size)

    #TODO: Change filename + create a saving method in case we need some processing e.g. quarantines
    np.save(join(fractal_mgr.input_dir, str(time.time())), histogram)
    if request.json['nickname'] is not "None":
        username = request.json['nickname']
    else:
        username = ""
    return {"message": f"Thanks ! {username} "}

if __name__ == '__main__':
    args = get_args()
    print(f'Debug : {args.debug}')
    configure_logger(args.debug)
    config_data_model = {
        "server" : ['loglevel', 'worker'],
        "subdirs" : ['checkpointdir', 'fractal_outputdir', 'checkpoint_outputdir']
    }
    config = parse_configuration(config_data_model)
    logger.debug(f'{config}')

    logger.debug(f'Creating subdirs')
    for subdir in config['subdirs']:
        try:
            makedirs(config['subdirs'][subdir], exist_ok = True)
            logger.debug(f'''subdir { subdir }: { config['subdirs'][subdir] } created''')
        except FileExistsError as e:
            logger.debug(f'''subdir { subdir }: { config['subdirs'][subdir] } already exists''')
            pass
        

    executor = ThreadPoolExecutor(
        int(config['server']['worker'])
    )
    fractal_mgr = FractalManager(
        input_dir = config['subdirs']['checkpointdir'], 
        fractal_output_dir = config['subdirs']['fractal_outputdir'], 
        checkpoint_output_dir = config['subdirs']['checkpoint_outputdir'], 
        output_size = (7105, 4960)
    )
    last_compute_time = time.time()

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=fractal_mgr.compute_histograms, trigger="interval", seconds=30)
    scheduler.start()

    app.run(debug=args.debug, port=8000)
