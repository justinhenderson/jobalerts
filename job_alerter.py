#!/usr/bin/env python3
"""
Job Alert System - Monitors Indeed for new job postings and sends SMS alerts
"""

import requests
from bs4 import BeautifulSoup
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

# Twilio credentials (set as environment variables)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# File to track seen jobs
SEEN_JOBS_FILE = "seen_jobs.json"

# Indeed search base URL
INDEED_BASE_URL = "https://www.indeed.com/jobs"


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


def search_indeed(job_title):
    """
    Search Indeed for jobs matching the title.
    Returns list of job dictionaries with: id, title, company, location, url
    """
    params = {
        'q': job_title,
        'l': 'United States',
        'sc': '0kf:attr(DSQF7);',  # Remote filter
        'fromage': '1',  # Last 24 hours
        'sort': 'date'  # Sort by date
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(INDEED_BASE_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        jobs = []
        
        # Find all job cards on the page
        job_cards = soup.find_all('div', class_='job_seen_beacon')
        
        for card in job_cards[:10]:  # Limit to first 10 results per search
            try:
                # Extract job ID from the card
                job_id = card.get('data-jk')
                if not job_id:
                    continue
                
                # Extract job title
                title_elem = card.find('h2', class_='jobTitle')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                else:
                    title = "Unknown Title"
                
                # Extract company name
                company_elem = card.find('span', {'data-testid': 'company-name'})
                company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
                
                # Extract location
                location_elem = card.find('div', {'data-testid': 'text-location'})
                location = location_elem.get_text(strip=True) if location_elem else "Remote"
                
                # Build job URL
                job_url = f"https://www.indeed.com/viewjob?jk={job_id}"
                
                jobs.append({
                    'id': job_id,
                    'title': title,
                    'company': company,
                    'location': location,
                    'url': job_url,
                    'search_term': job_title
                })
                
            except Exception as e:
                print(f"Error parsing job card: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"Error searching Indeed for '{job_title}': {e}")
        return []


def send_sms_alert(job):
    """Send SMS alert via Twilio for a new job posting"""
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        print("⚠️  Twilio credentials not set. Skipping SMS.")
        print(f"Would have sent alert for: {job['title']} at {job['company']}")
        return False
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message_body = f"""🚨 NEW JOB ALERT!

{job['title']}
{job['company']}
{job['location']}

{job['url']}

message_body = f"""🚨 NEW JOB ALERT!

{job['title']}
{job['company']}
{job['location']}

{job['url']}

Found via: {job['search_term']}
"""
        
    except Exception as e:
        print(f"❌ Error sending SMS: {e}")
        return False


def main():
    """Main function to check for new jobs and send alerts"""
    print(f"\n{'='*60}")
    print(f"Job Alert System - Running at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Load previously seen jobs
    seen_jobs = load_seen_jobs()
    print(f"📋 Currently tracking {len(seen_jobs)} seen jobs")
    
    new_jobs_found = []
    
    # Search for each job title
    for title in JOB_TITLES:
        print(f"\n🔍 Searching for: {title}")
        jobs = search_indeed(title)
        print(f"   Found {len(jobs)} results")
        
        # Check for new jobs
        for job in jobs:
            if job['id'] not in seen_jobs:
                print(f"   🆕 NEW: {job['title']} at {job['company']}")
                new_jobs_found.append(job)
                seen_jobs.add(job['id'])
        
        # Be nice to Indeed's servers
        time.sleep(2)
    
    # Send alerts for new jobs
    if new_jobs_found:
        print(f"\n📱 Sending alerts for {len(new_jobs_found)} new job(s)...\n")
        for job in new_jobs_found:
            send_sms_alert(job)
            time.sleep(1)  # Space out SMS sending
    else:
        print("\n✨ No new jobs found this cycle")
    
    # Save updated seen jobs
    save_seen_jobs(seen_jobs)
    print(f"\n💾 Saved {len(seen_jobs)} total tracked jobs")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
```

4. Scroll down, click **"Commit changes"**

---

### **File 2: requirements.txt**

1. Click **"Add file"** → **"Create new file"** again
2. Name it: `requirements.txt`
3. Paste:
```
requests==2.31.0
beautifulsoup4==4.12.3
twilio==9.0.4
