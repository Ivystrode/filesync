import transmitter

backup = transmitter.Transmitter("192.168.0.217", 
                                5001, 
                                ['daily'], 
                                ("1300", "2155"), 
                                "File_Root",
                                encrypt=True
    
)

backup.run_scheduler()