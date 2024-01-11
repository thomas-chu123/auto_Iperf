@echo on
start %cd%\iperf3.exe  -s -p 5001 -f m -i 60
start %cd%\iperf3.exe  -s -p 5002 -f m -i 60
pause
