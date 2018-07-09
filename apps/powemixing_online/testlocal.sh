#!/bin/sh 
k=$1
n=$2



python powermixing_online_phase1.py --no-ssl player-$n.ini $k
mkdir phase2-party$n
cp -r cpp_phase2 phase2-party$n/cpp_phase2
cd phase2-party$n/cpp_phase2
sh run-compute-power-sums-local.sh $k $n
cp powers.sum$n ../../powers.sum$n
cd ../..
python powermixing_online_phase3.py --no-ssl player-$n.ini $k
cp party$n-powermixing-online-phase3-output solver_phase4/party$n-powermixing-online-phase3-output
cd solver_phase4
python3 solver.py $n
mv party$n-finaloutput ../party$n-finaloutput

cd ..

rm -r -f phase2-party$n
rm -r -f party$n-powermixing-online-phase1-output
rm -f party$n-powermixing-online-phase3-output
rm -f powers.sum$i
rm -f /solver_phase4/party$n-powermixing-online-phase3-output
