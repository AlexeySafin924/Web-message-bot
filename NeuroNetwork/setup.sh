#!/bin/bash

virtualenv --python=python2 aivenv
source aivenv/bin/activate
pip install -r AIrequirements.txt
git clone https://github.com/glnur/chatBot
cd chatBot
python execute.py
