import os
import time

# this little script writes all the filenames (with relative path) to a manifest file
# in next version, receiver will get this manifest first
# it will then check off all the files on the manifest to see if
# 1. They exist, and
# 2. They have been modified
# these details will be sent as a tuple or dict

for item in os.walk('sendthis'):
    if len(item[2]) > 0:
        for file in item[2]:
            file_namepath = item[0] + "\\" + file
            file_modded_date =  time.ctime(os.path.getmtime(item[0] + "\\" + file))
            with open("file_manifest.txt", "a") as f:
                f.write(f"('{file_namepath}', '{file_modded_date}')\n")
            