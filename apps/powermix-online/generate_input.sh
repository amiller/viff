#!/bin/sh 
k=$1
n=$2
cd ~/viff/apps/powermix-online/
#cd cpp_phase2
#make clean 
#make
#cd ..


python preinput_generator.py --no-ssl player-$n.ini $k
python input_generator.py --no-ssl player-$n.ini $k
cd ~