#!/bin/sh 
k=$1
n=$2
b=$3
rm -r -f phase2-party$n
rm -r -f party$n-powermixing-online-phase1-output
rm -f party$n-powermixing-online-phase3-output
rm -f powers.sum$i
rm -f /solver_phase4/party$n-powermixing-online-phase3-output


start_tm=`date +%s%N`;
python powermixing_online_phase1.py --no-ssl player-$n.ini $k $b
mkdir phase2-party$n
cp -r cpp_phase2 phase2-party$n/cpp_phase2
cd phase2-party$n/cpp_phase2
sh run-compute-power-sums-local.sh $k $n $b
for batch in $( seq 1 $b )
do
	cp powers.sum_batch${batch} ../../powers.sum${n}_batch${batch}
done
cd ../..
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


rm -r -f phase2-party$n
rm -r -f party$n-powermixing-online-phase1-output
rm -f party$n-powermixing-online-phase3-output
rm -f powers.sum$i
rm -f /solver_phase4/party$n-powermixing-online-phase3-output

cd ..


