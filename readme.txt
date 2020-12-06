Program to backup files to offsite locations

- NOTE - rsync may be easier and safer for this. But I enjoyed making this and it will still be a good way for different machines to regularly update each other on what their current IP is

CURRENT BEST WORKING STATE:
Transmitter class takes host, port, list of days to back up and time range in a tuple and then runs scheduled backups
Client and server now send manifests to decide which files to send.
All actions are logged to a dated logfile and stored in a log directory

sendthis directories gitignored
use sendthis folders to send files, dont include test files in git commits


To do
- Add scheduler function to receiver
- Add ability to send files if modified date is changed
- Delete manifest files when done with them...not massively important though
- SECURITY - add function to shut down file transfer if a file that is not on the manifest is detected
- A warning must then be sent ie Telegram bot integration and/or email
    - Warning 1 is sent
    - Script will attempt to delete unknown file
    - Second warning message will be sent if script seems to be successful in deleting it
    - Separate thread can detect an emergency shutdown message from telegram
- Add file encryption/decryption?
