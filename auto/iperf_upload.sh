#!/bin/bash
# input parameter: project_type port_number filename
sfu_eth=("eno2.7" "enp3s0f0" "enp3s0f1")
hb3_eth=("eno2" "enp3s0f0" "enp3s0f1")
server_ip=("10.10.10.1" "10.10.10.2" "10.10.10.3" "10.10.10.4" "10.10.10.5" "10.10.10.6")
sfu_ip=("10.10.10.11" "10.10.10.12" "10.10.10.13" "10.10.10.14")
hb3_ip=("192.168.1.101" "192.168.1.102" "192.168.1.103" "192.168.1.104")
port=("5001" "5002" "5003" "5004" "5005" "5006")

if [ $1 -eq 0 ]; then
  port_id="1"
  file=$3"_p"$port_id".txt"
  echo $file
  iperf3 -c ${server_ip[0]} -B ${sfu_ip[0]} -i 5 -p ${port[0]} -f m -t 60 -l 1460 -P 10 > ${file} &
  sleep 2
elif [ $1 -eq 1 ]; then
  for (( i=0; i<$2; i++ ))
  do
    port_id=$((i+1))
    file=$3"_p"$port_id".txt"
    echo $file
    iperf3 -c ${server_ip[$i]} -B ${hb3_ip[$i]} -i 5 -p ${port[$i]} -f m -t 60 -l 1460 -P 10 > ${file} &
    sleep 2
  done
fi
