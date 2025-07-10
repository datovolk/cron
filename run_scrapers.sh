#!/bin/bash

cd "$(dirname "$0")"

source venv/bin/activate

python3 job_scraper.py >> logs/cron.log 2>&1
