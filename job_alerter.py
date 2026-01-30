#!/usr/bin/env python3
"""
Job Alert System - Monitors job boards for new postings and sends SMS alerts
"""

import requests
import json
import os
from datetime import datetime
from twilio.rest import Client
import time

# Configuration
PHONE_NUMBER = "+17046657523"

JOB_TITLES = [
    "Chief of Staff",
    "Head of Business Operations",
    "Director of Strategy Operations",
    "Director of Operations",
    "Director of Customer Operations"
]

# API credentials (set as environment variables)
JSEARCH_API_KEY = os.environ.get('JSEARCH_API_KEY')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# File to track seen jobs
SEEN_JOBS_FILE = "seen_jobs.json"

# JSearch API endpoint
JSEARCH_API_URL = "https://jsearch.p.rapidapi.com/search"


def load_seen_jobs():
    """Load the set of previously seen job IDs"""
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('job_ids', []))
    return set()


def save_seen_jobs(job_ids):
    """Save the set of seen job IDs to file"""
    with open(SEEN_JOBS_FILE, 'w') as f:
        json.dump({
            'job_ids': list(job_ids),
            'last_updated': datetime.now().isoformat()
        }, f, indent=2)


def search_jobs(job_title):
    """
    Search for jobs using JSearch API
    Returns list of job dictionaries
    """
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    params = {
    "query": f"{job_title}",
    "page": "1",
    "num_pages": "1",
    "date_posted": "today",
    "remote_jobs_only": "true"
    "job_publishers": "Indeed,LinkedIn"
    }
    
    try:
        response = requests.get(JSEARCH_API_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        jobs = []
        
        if data.get('status') == 'OK' and 'data' in data:
            for job_data in data['data'][:10]:
                jobs.append({
                    'id': job_data.get('job_id'),
                    'title': job_data.get('job_title', 'Unknown Title'),
                    'company': job_data.get('employer_name', 'Unknown Company'),
                    'location': job_data.get('job_city', 'Remote'),
                    'url': job_data.get('job_apply_link', ''),
                    'search_term': job_title
                })
        
        return jobs
        
    except Exception as e:
        print(f"Error searching for '{job_title}': {e}")
        return []


def send_sms_alert(job):
    """Send SMS alert via Twilio for a new job posting"""
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        print("Twilio credentials not set. Skipping SMS.")
        print(f"Would have sent alert for: {job['title']} at {job['company']}")
        return False
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message_body = f"""NEW JOB ALERT!

{job['title']}
{job['company']}
{job['location']}

{job['url']}

Found via: {job['search_term']}
"""
        
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=PHONE_NUMBER
        )
        
        print(f"SMS sent successfully! SID: {message.sid}")
        return True
        
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False


def main():
    """Main function to check for new jobs and send alerts"""
    print(f"\n{'='*60}")
    print(f"Job Alert System - Running at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    if not JSEARCH_API_KEY:
        print("ERROR: JSEARCH_API_KEY not set!")
        return
    
    seen_jobs = load_seen_jobs()
    print(f"Currently tracking {len(seen_jobs)} seen jobs")
    
    new_jobs_found = []
    
    for title in JOB_TITLES:
        print(f"\nSearching for: {title}")
        jobs = search_jobs(title)
        print(f"   Found {len(jobs)} results")
        
        for job in jobs:
            if job['id'] and job['id'] not in seen_jobs:
                print(f"   NEW: {job['title']} at {job['company']}")
                new_jobs_found.append(job)
                seen_jobs.add(job['id'])
        
        time.sleep(1)
    
    if new_jobs_found:
        print(f"\nSending alerts for {len(new_jobs_found)} new job(s)...\n")
        for job in new_jobs_found:
            send_sms_alert(job)
            time.sleep(1)
    else:
        print("\nNo new jobs found this cycle")
    
    save_seen_jobs(seen_jobs)
    print(f"\nSaved {len(seen_jobs)} total tracked jobs")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
