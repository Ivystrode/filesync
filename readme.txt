Program to backup files to offsite locations

CURRENT BEST WORKING STATE:
compress folder into archive, send and decompress on other end as named folder

Issues:
1. Will then have to either
    a. Delete old backup on/before receipt of new backup archive
    b. Keep both/all backups - check if space is getting too full and then delete older backups
    I like option b.

sendthis directories gitignored
use sendthis folders to send files, dont include test files in git commits

To do
- receive file - check path and file exists and move into there
-- how to check only a certain part of a file path
-- how to check if a file has been modified since it was copied?

- log file
backup/sync will happen at regular intervals. at the beginning of the backup, sender will create a log file and write every action to that log file, title it with the current date, and at the end of the operation send it to the receiver before closing the connection