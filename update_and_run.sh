#!/bin/bash

cd /home/admin/Desktop/EON-EMS

if pgrep -f EON_EMS.py > /dev/null
then
  echo "Program is running. Before updating - Shut it down"
  exit 1
fi

git pull

source venv/bin/activate

pip install -r req.txt

python3 EON_EMS.py
