#!/bin/bash
sfu_eth=("eno2.7" "enp3s0f0" "enp3s0f1")
hb3_eth=("eno2" "enp3s0f0" "enp3s0f1")
server_ip=("10.10.10.1" "10.10.10.2" "10.10.10.3" "10.10.10.4" "10.10.10.5" "10.10.10.6")
sfu_ip=("10.10.10.11" "10.10.10.12" "10.10.10.13" "10.10.10.14")
hb3_ip=("192.168.1.101" "192.168.1.102" "192.168.1.103" "192.168.1.104")
port=("5001" "5002" "5003" "5004" "5005" "5006")

echo -e "Proejct Selection:\n"
read -p "Please input tested project (1: SFU, 2: SFU+HB3/HB3): " model
read -p "Please input client Ethernet Port number (1~2):  " port
read -p "Please input tested round (1~10): " count
read -p "Please input tested profile (1:100/40, 2:250/125, 3:1000/500, 4:2000/1000, 5:All): " profile
echo -e "\nConfigure Networking Environment\n"

if [ ${model} -eq 1 ]; then
	vconfig add eno2 7
	ifconfig eno2 192.168.100.2 netmask 255.255.255.0
	ifconfig eno2.7 10.10.10.11
	ip route add 192.168.100.1 via 192.168.100.2 dev eno2
	ip route add 10.10.10.1 via 10.10.10.11 dev eno2.7
	rm /opt/iperf_auto/log/*
	echo -e "Start Testing SFU:\n"
	python3 iperf_delay_auto_test.py ${count} ${profile} 0 ${port} ${model}
elif [ ${model} -eq 2 ] || [ ${model} -eq 3 ]; then
	vconfig rem eno2 7
	ifconfig eno2 192.168.1.101 netmask 255.255.255.0
	ifconfig enp3s0f0 192.168.1.102 netmask 255.255.255.0
	ifconfig enp3s0f1 192.168.1.103 netmask 255.255.255.0
	ip route del default via 192.168.1.1
	ip route add 192.168.1.1 via 192.168.1.101 dev eno2
	ip route add 192.168.100.1 via 192.168.1.1 dev eno2
	ip route add 10.10.10.1 via 192.168.1.1 dev eno2
	ip route add 10.10.10.2 via 192.168.1.1 dev enp3s0f0
	ip route add 10.10.10.3 via 192.168.1.1 dev enp3s0f1
	ip route add 10.10.10.5 via 192.168.1.1 dev eno2
	ip route add 10.10.10.6 via 192.168.1.1 dev enp3s0f0
	rm /opt/iperf_auto/log/*
	echo -e "Start Testing SFU+HB3\n"
	python3 iperf_delay_auto_test.py ${count} ${profile} 0 ${port} ${model}
fi

exit 0
