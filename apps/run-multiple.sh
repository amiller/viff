n=$1
t=$(((n / 3)))
echo $t

generate_config_command="python generate-config-files.py --skip-prss -n $n -t $t "
hosts=""
for (( c=1; c<=$n; c++ ))
do  
    hosts+="localhost:$((9000 + c)) "
done
generate_config_command+=$hosts
echo $generate_config_command
$generate_config_command
for (( c=1; c<$n; c++ ))
do  
    python triple_refinement.py -t $t player-$c.ini &
done
python triple_refinement.py -t $t  player-$n.ini