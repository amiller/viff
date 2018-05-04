make clean;
make;
k=$1;
n=$(lscpu -p | grep -c "^[0-9]");
mkdir -p inputs/random$k; seq $k | xargs -n1 -P$n -I{} sh -c "./compute-power-sums $k {} > inputs/random$k/random{}.input"
rm -f powers.sum; time seq $k | xargs -n1 -P$n -I{} sh -c "./compute-power-sums inputs/random$k/random{}.input"