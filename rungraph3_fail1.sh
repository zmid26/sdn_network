#!/bin/bash

osascript -e 'tell app "Terminal"
    do script "cd Documents/Github/lab-project-1-sdn-zmid26; python3 controller.py 12345 Config/graph_3.txt"
end tell'

sleep 0.2

osascript -e 'tell app "Terminal"
    do script "cd Documents/Github/lab-project-1-sdn-zmid26; python3 switch.py 0 noname 12345"
end tell'
sleep 0.2

osascript -e 'tell app "Terminal"
    do script "cd Documents/Github/lab-project-1-sdn-zmid26; python3 switch.py 1 noname 12345 -f 2"
end tell'
sleep 0.2

osascript -e 'tell app "Terminal"
    do script "cd Documents/Github/lab-project-1-sdn-zmid26; python3 switch.py 2 noname 12345 -f 1"
end tell'

#use option-command-w to close all instances of terminal