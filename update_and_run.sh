#!/bin/bash

cd /home/admin/Desktop/EON-EMS

if pgrep -f EON_EMS.py > /dev/null
then
  echo "Program is running. Before updating - Shut it down"
  echo "Press Enter to continue..."
  read
  exit 1
fi

git pull

if [ ! -d "venv" ]; then
  echo "Virtual environment 'venv' not found. Creating..."
  python3 -m venv venv
  if [ $? -ne 0 ]; then
    echo "Error creating virtual environment. Exiting."
    echo "Press Enter to continue..."
    read
    exit 1
  fi
else
  echo "Virtual environment 'venv' found."
fi

source venv/bin/activate

pip install --upgrade pip
pip install -r req.txt

python3 EON_EMS.py