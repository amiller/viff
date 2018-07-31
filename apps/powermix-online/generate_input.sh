#!/bin/sh 
k=$1
n=$2
cd ~/viff/apps/powermix-online/

export PYTHONPATH=$PYTHONPATH:$HOME/opt/lib/python

python preinput_generator.py --no-ssl player-$n.ini $k
python input_generator.py --no-ssl player-$n.ini $k
cd ~