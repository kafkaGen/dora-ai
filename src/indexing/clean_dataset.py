import os
import shutil

data_dir = "datasets/Screenshots2"
destination = "datasets/routes"

for fl in os.listdir(data_dir):
    group = fl.split("_")[0]
    step = fl.split("_")[1]

    os.makedirs(f"{destination}/{group}/{step}", exist_ok=True)

    shutil.copy(f"{data_dir}/{fl}/image.png", f"{destination}/{group}/{step}/image.png")


welcome = "datasets/Screenshots2/1_1_1746784519.787812/image.png"
for fl in os.listdir(destination):
    os.makedirs(f"{destination}/{fl}/0", exist_ok=True)
    shutil.copy(welcome, f"{destination}/{fl}/0/image.png")
