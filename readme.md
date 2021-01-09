***Program to backup files to offsite locations***

- NOTE - rsync may be easier and safer for this. But I enjoyed making this and it will still be a good way for different machines to regularly update each other on what their current IP is for example

CURRENT BEST WORKING STATE:
1. Instantiate a Transmitter class on the client with:
    - Server IP (destination for backed up files)
    - Destination port (default 5001)
    - Days (as an array) to back up files on
    - A time window (tuple) telling it what time to do the backup
    - The directory you want to back up

2. Instantiate a Receiver class on the server with:
    - Address to listen on (default 0.0.0.0)
    - Port to open for files (default 5001)
    - Days (as an array) to run the receiver on
    - A time window (tuple) to run the receiver, on the specified days
    - A target directory to send received files/sync and update received files with

3. Client machine then sends a list of all files in the directory to the server - the 'Client Manifest'
4. Server then compares the client manifest to the files it currently holds
5. The server compares the client manifest with the files in the backup directory - if it doesn't have them, or if it does but the last modified time is earlier than the client's version, it adds this file to the 'Server Manifest'
6. Server sends the server manifest back to the client
7. Client sends all files listed on the server manifest to the server
8. When all files are sent, the client sends a command to the server to terminate the connection
9. Both client and server log every action and save it to a dated log file



To do
- VPN - auto connect to VPN just before/at beginning of backup window, use subprocess to activate ovpn?
- Also put transmitter on server/NAS to regularly "downlink" files.
    - When we have multiple computers all backing up to the directory on the NAS, the downlink transmitter will regularly update the clients!
    
- SECURITY - add function to shut down file transfer if a file that is not on the manifest is detected
- A warning must then be sent ie Telegram bot integration and/or email
    - Warning 1 is sent
    - Script will attempt to delete unknown file
    - Second warning message will be sent if script seems to be successful in deleting it
    - Separate thread can detect an emergency shutdown message from telegram
