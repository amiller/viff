t=2
n=6
python generate-config-files.py -n $n -t $t localhost:9001 localhost:9002 localhost:9003 localhost:9004 localhost:9005 localhost:9006
PROGRAM="triple_refinement.py -t $t --no-ssl --statistics --deferred-debug"
set -x
tmux new-session "python ${PROGRAM} player-1.ini; zsh" \; \
     splitw -h -p 70 "python ${PROGRAM} player-2.ini; zsh" \; \
     splitw -h -p 60 "python ${PROGRAM} player-3.ini; zsh" \; \
     splitw -h -p 50 "python ${PROGRAM} player-4.ini; zsh" \; \
     splitw -v -p 50 "python ${PROGRAM} player-5.ini; zsh" \; \
     selectp -t 0 \; \
     splitw -v -p 50 "python ${PROGRAM} player-6.ini; zsh"
