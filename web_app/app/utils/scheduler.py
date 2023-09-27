from web_app.app.database.data_models import RawBenchmarkSubscores, OverallNormalizedScore
from web_app.app.database.init_db import init_db, SessionLocal
from web_app.app.logger_config import setup_logger
import os
import json
import re
import schedule
import time
import glob
import subprocess
from threading import Thread
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from configparser import ConfigParser
from decouple import config as decouple_config

logger = setup_logger()
ANSIBLE_INVENTORY_FILE_PATH = decouple_config("ANSIBLE_INVENTORY_FILE_PATH", cast=str)
NORMALIZED_BENCHMARK_OUTPUT_FILES_PATH = decouple_config("NORMALIZED_BENCHMARK_OUTPUT_FILES_PATH", cast=str)
COMBINED_PASTEL_BENCHMARK_RESULTS_FILE_PATH = decouple_config("COMBINED_PASTEL_BENCHMARK_RESULTS_FILE_PATH", cast=str)
PLAYBOOK_RUN_INTERVAL_IN_MINUTES = decouple_config("PLAYBOOK_RUN_INTERVAL_IN_MINUTES", cast=int) 


def parse_inventory(file_path):
    logger.info(f"Parsing inventory file at {file_path}.")    
    config = ConfigParser(allow_no_value=True)
    config.read(file_path)
    return {k: v.get('ansible_host') for k, v in config['all'].items()}

def read_and_massage_json(file_path):
    logger.info(f"Reading and massaging JSON file at {file_path}.")    
    with open(file_path, 'r') as f:
        content = f.read().strip()
        content = re.sub(r'(\w+): {', r'"\1": {', content)
        content = '{' + content + '}'
    return json.loads(content)

def ingest_data(db: Session, raw_data, overall_data, datetime_now, host_to_ip):
    for hostname, scores in raw_data.items():
        raw_entry = RawBenchmarkSubscores(
            datetime=datetime_now,
            hostname=hostname,
            IP_address=host_to_ip.get(hostname, 'UNKNOWN'),
            **scores
        )
        db.add(raw_entry)

        overall_entry = OverallNormalizedScore(
            datetime=datetime_now,
            hostname=hostname,
            IP_address=host_to_ip.get(hostname, 'UNKNOWN'),
            overall_score=overall_data[hostname]
        )
        db.add(overall_entry)

def job():
    logger.info("Scheduler job started.")    
    logger.info("Now running ansible playbook...")    
    process = subprocess.Popen(
        ["ansible-playbook", "-v", "-i", ANSIBLE_INVENTORY_FILE_PATH, "benchmark-playbook.yml"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    for line in iter(process.stdout.readline, ''):
        logger.info(line.strip())
    process.stdout.close()
    process.wait()            
    logger.info("Ansible playbook run completed.")
    init_db()
    datetime_now = datetime.now()
    logger.info("Massaging raw data into valid JSON.")
    raw_data = read_and_massage_json(COMBINED_PASTEL_BENCHMARK_RESULTS_FILE_PATH)
    logger.info("Parsing inventory file.")
    host_to_ip = parse_inventory(ANSIBLE_INVENTORY_FILE_PATH)
    logger.info("Reading overall data from JSON file.")
    latest_overall_file = max(glob.glob(f'{NORMALIZED_BENCHMARK_OUTPUT_FILES_PATH}/*.json'), key=os.path.getctime)
    overall_data = json.load(open(latest_overall_file))
    logger.info("Ingesting data into the database.")
    db = SessionLocal()
    ingest_data(db, raw_data, overall_data, datetime_now, host_to_ip)
    db.commit()
    logger.info("Data ingestion completed.")
    logger.info("Scheduled job completed!")    

def should_run_job(file_paths):
    now = datetime.now()
    for file_path in file_paths:
        try:
            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - modified_time > timedelta(hours=1):
                return True
        except FileNotFoundError:
            logger.warning(f"File {file_path} not found.")
            continue
    return False

def start_scheduler():
    logger.info("Scheduler started.")    
    schedule.every(PLAYBOOK_RUN_INTERVAL_IN_MINUTES).minutes.do(job)
    files_to_check = [
        ANSIBLE_INVENTORY_FILE_PATH,
        COMBINED_PASTEL_BENCHMARK_RESULTS_FILE_PATH
    ]
    # Conditionally run the job based on file timestamps
    if should_run_job(files_to_check):
        job()
    schedule.every(PLAYBOOK_RUN_INTERVAL_IN_MINUTES).minutes.do(job)
        
    def run():
        while True:
            logger.info("Checking for pending jobs.")
            schedule.run_pending()
            time.sleep(1)

    # Run the above function in a separate thread
    scheduler_thread = Thread(target=run)
    scheduler_thread.start()
