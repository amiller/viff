#!/bin/bash
gnome-terminal -e "python test.py --no-ssl player-1.ini 3"
for i in {2..20}
do
	gnome-terminal -e "python test.py --no-ssl player-$i.ini 3 &"
done
