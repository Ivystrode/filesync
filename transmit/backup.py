import transmitter

backup = transmitter.Transmitter(
    "PINAS", 
    5001, 
    ['daily'], 
    ("0001", "2359"), 
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