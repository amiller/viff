#!/bin/sh 
n=3
k=32
fname="powermixing_online_phase3.py"
python generate-config-files.py -n 3 -t 1 localhost:9001 localhost:9002 localhost:9003
for c in `seq 1 $n`
do  
    gnome-terminal -e "sh testlocal.sh $k $c"
done

#gnome-terminal -e "python $fname --no-ssl player-1.ini $k"
#gnome-terminal -e "python $fname --no-ssl player-2.ini "
#gnome-terminal -e "python $fname --no-ssl player-3.ini "
#gnome-terminal -e "python $fname --no-ssl player-4.ini "
