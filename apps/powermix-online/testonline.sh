#!/bin/sh 
k=$1
n=$2
cd ~/viff/apps/powermix-online/
python powermixing_online_phase1.py --no-ssl player-$n.ini $k
cd cpp_phase2
sh run-compute-power-sums-online.sh $k $n
cp powers.sum ../powers.sum$n
cd ..
python powermixing_online_phase3.py --no-ssl player-$n.ini $k
cp party$n-powermixing-online-phase3-output solver_phase4/party$n-powermixing-online-phase3-output
cd solver_phase4
python3 solver.py $n
cp party$n-finaloutput ../party$n-finaloutput

rm -r -f party$n-powermixing-online-phase1-output
rm -f party$n-powermixing-online-phase3-output
rm -f powers.sum$i
rm -f /solver_phase4/party$n-powermixing-online-phase3-output