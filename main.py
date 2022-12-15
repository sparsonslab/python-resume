import subprocess
import os

if __name__ == '__main__':
    path = os.path.join(os.path.dirname(__file__), "src", "sigview.py")
    subprocess.run(['python', path])
