Program to backup files to offsite locations

- NOTE - rsync may be easier and safer for this. However this may be a way to transmit the IP address of this server to another server and vice versa by sending it in a text file...

CURRENT BEST WORKING STATE:
using os walker multisend3 can send to multireceive dir with subdirs and files in each dir

sendthis directories gitignored
use sendthis folders to send files, dont include test files in git commits

To do
- Create manifest proposal file and send to receiver
- Receiver checks manifest to see if files exist and if the modified date in the proposal file is later than the backed up file
- If yes to either of the above, receiver adds the file to the confirmed manifest
- When complete, receiver sends the confirmed manifest back to the sender
- Sender then locates the requested files on the confirmed manifest and sends them to the receiver
- New and modified files are therefore backed up!
- Consider dating each proposed manifest so receiver can check it (and vice versa)
- The manifests could then be stored in a log folder...

- log file
backup/sync will happen at regular intervals. at the beginning of the backup, sender will create a log file and write every action to that log file, title it with the current date, and at the end of the operation send it to the receiver before closing the connection