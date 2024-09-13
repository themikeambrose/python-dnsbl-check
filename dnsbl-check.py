import asyncio
import pydnsbl
import logging
from netaddr import IPNetwork
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import requests
import traceback

# SMTP email settings
sender_email = "noreply@yourdomain.com"
receiver_email = "email_to_send_to"
smtp_server = "mail.yourdomain.com"
smtp_port = 587
smtp_username = "smtp_username"
smtp_password = "smtp_pass"

# Discord webhook settings (optional)
discord_webhook_url = "https://discord.com/api/webhooks/your_webhook_url_here"  # Replace with your webhook URL
send_discord_notification = True  # Set to False if you don't want to send Discord notifications

ip_list = ['192.168.0.0/24', '192.168.1.0/24', '192.168.2.0/24']

# Blacklist to exclude from checking. Just added to exclude UCEPROTECT extortion scam blacklist by deafult.
exclude_blacklist = 'dnsbl-3.uceprotect.net'

# Ensure the logs directory exists
if not os.path.exists('logs'):
    os.makedirs('logs')

# Set up logging to file and console for better diagnostics
logging.basicConfig(filename=os.path.join('logs', f'blacklist_check_{datetime.now().strftime("%Y%m%d")}.log'), 
                    level=logging.DEBUG,  # Changed to DEBUG for more verbosity
                    format='%(asctime)s %(levelname)s %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logging.getLogger('').addHandler(console)

def send_email_notification(blacklisted_ips):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = 'Blacklisted IP Alert'
        body = '\n'.join([f"IP {ip} is blacklisted on: {', '.join(detected_by)}" for ip, detected_by in blacklisted_ips])
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # secure the connection
        server.login(smtp_username, smtp_password)  # login with mail_id and password
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        logging.info("Email notification sent successfully.")
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        logging.error(traceback.format_exc())

def send_discord_notification(blacklisted_ips):
    if not send_discord_notification or not discord_webhook_url:
        logging.info("Discord notification disabled or webhook URL missing.")
        return  # Exit if Discord notifications are disabled or webhook URL is missing
    
    try:
        content = "\n".join([f"IP {ip} is blacklisted on: {', '.join(detected_by)}" for ip, detected_by in blacklisted_ips])
        data = {
            "content": f"**Blacklisted IP Alert**\n{content}"
        }
        response = requests.post(discord_webhook_url, json=data)

        if response.status_code == 204:
            logging.info("Discord notification sent successfully.")
        else:
            logging.error(f"Failed to send Discord notification. Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        logging.error(f"Error sending Discord notification: {str(e)}")
        logging.error(traceback.format_exc())

async def check_single_ip(ip_checker, single_ip, blacklisted_ips):
    try:
        result = await ip_checker.check_async(str(single_ip))
        if result.blacklisted:
            # Filter out the results from the excluded blacklist
            detected_by = [bl for bl in result.detected_by if bl != exclude_blacklist]
            if detected_by:  # Only add if there are other blacklists detected
                message = f"IP {single_ip} is blacklisted on: {', '.join(detected_by)}"
                logging.info(message)
                blacklisted_ips.append((str(single_ip), detected_by))
            else:
                message = f"IP {single_ip} is not blacklisted on any lists (excluding {exclude_blacklist})."
                logging.info(message)
        else:
            message = f"IP {single_ip} is not blacklisted."
            logging.info(message)
    except Exception as e:
        logging.error(f"Error checking IP {single_ip}: {str(e)}")
        logging.error(traceback.format_exc())

async def check_ip_blacklist(ip_list):
    try:
        ip_checker = pydnsbl.DNSBLIpChecker()
        blacklisted_ips = []

        tasks = []
        for ip in ip_list:
            for single_ip in IPNetwork(ip):
                tasks.append(check_single_ip(ip_checker, single_ip, blacklisted_ips))
        await asyncio.gather(*tasks)

        # If we found any blacklisted IPs, send notifications
        if blacklisted_ips:
            send_email_notification(blacklisted_ips)
            send_discord_notification(blacklisted_ips)
    except Exception as e:
        logging.error(f"Error in check_ip_blacklist: {str(e)}")
        logging.error(traceback.format_exc())

# Run the asynchronous function with better error reporting
try:
    asyncio.run(check_ip_blacklist(ip_list))
except Exception as e:
    logging.error(f"Error in running asyncio: {str(e)}")
    logging.error(traceback.format_exc())
