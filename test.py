import os

path = './uploads'

files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

print(files)