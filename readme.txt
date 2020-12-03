Program to backup files to offsite locations

- NOTE - rsync may be easier and safer for this. However this may be a way to transmit the IP address of this server to another server and vice versa by sending it in a text file...

CURRENT BEST WORKING STATE:
Transmitter class takes host, port, list of days to back up and time range in a tuple and then runs scheduled backups
Client and server now send manifests to decide which files to send.

sendthis directories gitignored
use sendthis folders to send files, dont include test files in git commits

To do
- Add ability to send files if modified date is changed
- Consider dating each proposed manifest so receiver can check it (and vice versa)
- The manifests could then be stored in a log folder...
- SECURITY - add function to shut down file transfer if a file that is not on the manifest is detected
- A warning must then be sent ie Telegram bot integration and/or email
    - Warning 1 is sent
    - Script will attempt to delete unknown file
    - Second warning message will be sent if script seems to be successful in deleting it
    - Separate thread can detect an emergency shutdown message from telegram

- log file
backup/sync will happen at regular intervals. at the beginning of the backup, sender will create a log file and write every action to that log file, title it with the current date, and at the end of the operation send it to the receiver before closing the connection