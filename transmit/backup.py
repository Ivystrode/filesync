import transmitter

backup = transmitter.Transmitter(
    "192.168.1.88", 
    5001, 
    ['daily'], 
    ("2200", "2359"), 
    "sendthis",
    encrypt=True
)

print("\nTransmitter parameters\n")
print(backup.host)
print(backup.port)
print(backup.backup_day)
print(backup.backup_timerange)
print(backup.backup_dir)
print("----------")

backup.run_scheduler()