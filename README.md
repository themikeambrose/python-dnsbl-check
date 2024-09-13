# python-dnsbl-check
Simple Python script to check DNSBL status for multiple IPv4 subnets, and send both email and Discord webhook notification with results. Run `python3 /home/example/dnsbl-check.py` in a cron job once a day for example.
- Must have required libraries like "smtplib" and "pydnsbl" installed.
- Checks DNSBL blacklists using "pydnsbl" library.
- Uses SMTP credentials to send emails.
- Sends results of the check when completed (may take a few minutes if you have lots of IPs) to email.
- Optionally, also send results via Discord webhook to a Discord channel.
- Option to exclude certain DNSBL blacklists from being checked. By default UCEPROTECT is excluded since it's not used by email services and often has false listings that require you to pay the person running it to get removed.\
\
**You must use your own local DNS server, DNSBL's block public DNS resolvers like 1.1.1.1, 8.8.8.8, etc.**
