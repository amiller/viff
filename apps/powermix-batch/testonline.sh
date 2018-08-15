#!/bin/sh 
butterk=$1
butterl=$2
k=$3
n=$4
b=$5
cd ~/viff/apps/powermix-batch/
#cd cpp_phase2
#make clean 
#make
#cd ..

start_tm=`date +%s%N`;
python butterfly_online.py --no-ssl player-$n.ini $butterk $butterl
echo "butterfly done"
python powermixing_online_phase1.py --no-ssl player-$n.ini $k $b
cd cpp_phase2
sh run-compute-power-sums-online.sh $k $n $b
for batch in $( seq 1 $b )
do
	cp powers.sum_batch${batch} ../../powers.sum${n}_batch${batch}
done
cd ..
python powermixing_online_phase3.py --no-ssl player-$n.ini $k $b

for batch in $( seq 1 $b )
do
	cp party$n-powermixing-online-phase3-output-batch${batch} solver_phase4/party$n-powermixing-online-phase3-output-batch${batch}
done

cd solver_phase4
python3 solver.py $n $b
end_tm=`date +%s%N`;
use_tm=`echo $end_tm $start_tm | awk '{ print ($1 - $2) / 1000000000}'`
echo $use_tm

for batch in $( seq 1 $b )
do
	
	mv party$n-finaloutput-batch${batch} ../party$n-finaloutput-batch${batch}
done

rm -r -f party$n-powermixing-online-phase1-output
rm -f party$n-powermixing-online-phase3-output
rm -f powers.sum$i
rm -f /solver_phase4/party$n-powermixing-online-phase3-output
