make clean;
make;
k=$1;
n=$(lscpu -p | grep -c "^[0-9]");
mkdir -p random$k; seq $k | xargs -n1 -P$n -I{} sh -c "./power-mixing $k {} > random$k/random{}.input"
rm -f powers.sum; time seq $k | xargs -n1 -P$n -I{} sh -c "./power-mixing random$k/random{}.input"