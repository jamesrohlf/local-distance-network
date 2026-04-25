#!/usr/bin/env bash
# Double-click on macOS to run. Uses whichever python3 is on PATH.
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
python3 local_distance_network.py
status=$?
if [ $status -ne 0 ]; then
  echo
  echo "(exited with status $status)"
  echo "Press Return to close this window."
  read _dummy
fi
