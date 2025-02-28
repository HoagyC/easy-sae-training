import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Union

def load_vastnode_info():
    """Load the vastnode info from the json file."""
    with open("secrets/.vastnode", "r") as f:
        vastnode_info = json.load(f)
    return vastnode_info

VAST_NUM = 0
DEST_ADDR = f"root@ssh{VAST_NUM}.vast.ai"
SSH_PYTHON = "/opt/conda/bin/python"
PORT = 0

def init_vastnode():
    """Initialise the vastnode."""
    global VAST_NUM
    global DEST_ADDR
    global PORT

    vastnode_info = load_vastnode_info()
    VAST_NUM = vastnode_info["vast_num"]
    PORT = vastnode_info["port"]
    DEST_ADDR = f"root@ssh{VAST_NUM}.vast.ai"

USER = "aidan"

SSH_DIRECTORY = f"sparse_coding_{USER}"
BUCKET_NAME = "sparse-coding"

ACCESS_KEY_NAME_DICT = {
    "AKIAV3IKT32M2ZA3WRLQ": "hoagy",
    "AKIATUSYDLZAEZ7T5GLX": "aidan",
    "AKIATEQID7TUM5FUW4R5": "logan",
}


def sync():
    """Sync the local directory with the remote host."""
    command = f'rsync -rv --filter ":- .gitignore" --exclude ".git" -e "ssh -p {PORT}" . {DEST_ADDR}:{SSH_DIRECTORY}'
    subprocess.call(command, shell=True)

def connect():
    """SSH into the remote host."""
    command = f"ssh -p {PORT} {DEST_ADDR}"
    subprocess.call(command, shell=True)

def datasets_sync():
    """Sync .csv files with the remote host."""
    command = f'rsync -am --include "*.csv" --exclude "*" -e "ssh -p {PORT}" . {DEST_ADDR}:{SSH_DIRECTORY}'
    subprocess.call(command, shell=True)


def autointerp_sync():
    """Sync the local directory with the remote host's auto interp results, excluding hdf files."""
    command = f'rsync -r --exclude "*.hdf" --exclude "*.pkl" -e ssh {DEST_ADDR}:/mnt/ssd-cluster/auto_interp_results/ ./auto_interp_results'
    print(command)
    subprocess.call(command, shell=True)


def copy_models():
    """Copy the models from local directory to the remote host."""
    command = f"scp -P {PORT} -r models {DEST_ADDR}:{SSH_DIRECTORY}/models"
    subprocess.call(command, shell=True)
    # also copying across a few other files
    command = f"scp -P {PORT} -r outputs/thinrun/autoencoders_cpu.pkl {DEST_ADDR}:{SSH_DIRECTORY}"
    subprocess.call(command, shell=True)


def copy_secrets():
    """Copy the secrets.json file from local directory to the remote host."""
    command = f'rsync -rv -e "ssh -p {PORT}" ./secrets {DEST_ADDR}:{SSH_DIRECTORY}'
    subprocess.call(command, shell=True)


def copy_recent():
    """Get the most recent outputs folder in the remote host and copy across to same place in local directory."""
    # get the most recent folders
    command = f'ssh -p {PORT} {DEST_ADDR} "ls -td {SSH_DIRECTORY}/outputs/* | head -1"'
    output = subprocess.check_output(command, shell=True)
    output = output.decode("utf-8").strip()
    # copy across
    command = f"scp -P {PORT} -r {DEST_ADDR}:{output} outputs"
    subprocess.call(command, shell=True)


def copy_dotfiles():
    """Copy dotfiles into remote host and run install and deploy scripts"""
    df_dir = f"dotfiles_{USER}"
    # command = f"scp -P {PORT} -r ~/git/dotfiles {DEST_ADDR}:{df_dir}"
    command = f"rsync -rv --filter ':- .gitignore' --exclude '.git' -e 'ssh -p {PORT}' ~/git/ {DEST_ADDR}:{df_dir}"
    subprocess.call(command, shell=True)
    command = f"ssh -p {PORT} {DEST_ADDR} 'cd ~/{df_dir} && ./install.sh && ./deploy.sh'"
    subprocess.call(command, shell=True)


def setup():
    """Sync, copy models, create venv and install requirements."""
    sync()
    copy_models()
    copy_secrets()
    command = f'ssh -p {PORT} {DEST_ADDR} "cd {SSH_DIRECTORY} && sudo apt -y install python3.9 python3.9-venv && python3.9 -m venv .env --system-site-packages && source .env/bin/activate && pip install -r requirements.txt"'
    # command = f"ssh -p {VAST_PORT} {dest_addr} \"cd {SSH_DIRECTORY} && echo $PATH\""
    subprocess.call(command, shell=True)


class dotdict(dict):
    """Dictionary that can be accessed with dot notation."""

    def __init__(self, d: Optional[dict] = None):
        if d is None:
            d = {}
        super().__init__(d)

    def __dict__(self):
        return self

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError(f"Attribute {name} not found")

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]

if __name__ == "__main__":
    init_vastnode()

    if sys.argv[1] == "sync":
        sync()
    elif sys.argv[1] == "connect":
        connect()
    elif sys.argv[1] == "models":
        copy_models()
    elif sys.argv[1] == "recent":
        copy_recent()
    elif sys.argv[1] == "setup":
        setup()
    elif sys.argv[1] == "secrets":
        copy_secrets()
    elif sys.argv[1] == "interp_sync":
        autointerp_sync()
    elif sys.argv[1] == "dotfiles":
        copy_dotfiles()
    elif sys.argv[1] == "datasets":
        datasets_sync()
    else:
        raise NotImplementedError(f"Command {sys.argv[1]} not recognised")