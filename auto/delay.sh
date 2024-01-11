brctl addbr br0
brctl addif br0 eno2
brctl addif br0 enp1s0f1
ifconfig br0 up
brctl stp br0 on
echo 0 > /proc/sys/net/bridge/bridge-nf-call-iptables
echo 0 > bridge-nf-call-arptales
iptables -F
tc qdisc del dev enp1s0f1 root netem
tc qdisc add dev enp1s0f1 root netem delay $1
tc qdisc del dev eno2 root netem
tc qdisc add dev eno2 root netem delay $1
