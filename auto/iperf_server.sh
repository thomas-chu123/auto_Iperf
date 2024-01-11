#!/bin/bash
sfu_eth=("eno2.7" "enp3s0f0" "enp3s0f1")
hb3_eth=("eno2" "enp3s0f0" "enp3s0f1")
server_ip=("10.10.10.1" "10.10.10.2" "10.10.10.3" "10.10.10.4" "10.10.10.5" "10.10.10.6")
sfu_ip=("10.10.10.11" "10.10.10.12" "10.10.10.13" "10.10.10.14")
hb3_ip=("192.168.1.101" "192.168.1.102" "192.168.1.103" "192.168.1.104")
port=("5001" "5002" "5003" "5004" "5005" "5006")

pkill iperf3
ifconfig eno2 10.10.10.1 netmask 255.255.255.0
ifconfig eno2:1 10.10.10.2 netmask 255.255.255.0
ifconfig eno2:2 10.10.10.3 netmask 255.255.255.0
ifconfig eno2:3 10.10.10.4 netmask 255.255.255.0
ifconfig eno2:4 10.10.10.5 netmask 255.255.255.0
ifconfig eno2:4 10.10.10.6 netmask 255.255.255.0
for i in {0..5};
do
  echo "start server:" ${server_ip[$i]} "port:" ${port[$i]}
  iperf3 -s -B ${server_ip[$i]} -i 5 -p ${port[$i]} -f m -i 60 &
  sleep 0.5
done
