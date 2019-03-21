#!/bin/sh
master_container=voice_master
docker stop "$master_container" "w1" "w2"
docker rm "$master_container" "w1" "w2"
docker run --name "$master_container" -d -p $IP:8019:8019 voxhub/silvius-worker:latest /bin/sh -c 'cd /root/silvius-backend ; python kaldigstserver/master_server.py'
docker run --name "w1" --link="$master_container:master_host" -d voxhub/silvius-worker /root/worker.sh -u ws://master_host:8019/worker/ws/speech
docker run --name "w2" --link="$master_container:master_host" -d voxhub/silvius-worker /root/worker.sh -u ws://master_host:8019/worker/ws/speech
