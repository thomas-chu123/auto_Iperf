# 1. configure the SFU GPON password (SSH)
#    test speed: 100/40, 250/100, 1000/500
#    set ont ploam_password <HEX value>
# 2. check delay and iperf server, configure delay 7ms, 15ms, 20ms, 25ms (SSH)
# 3. configure delay on delay server
# 4. kill the server, start iperf server on server side (SSH)
# 5. kill the client, start iperf client on client side (SSH)
# 6. wait 11min
# 7. write the summary data to table
# 8. repeat the testing on step 2
# 9. repeat the testing on step 1

import copy
import logging
import sys
import time
from datetime import date

import openpyxl
import paramiko
import serial

output_logging = 20

test_profile_HEX = {"100_40": "F2101213010331", "250_125": "F2101213010330", "1000_500": "F2101213010328",
                "2000_1000": "F2101213010329"}

test_profile_ASCII = {"100_40": "1111111131", "250_125": "1111111130", "1000_500": "1111111128",
                "2000_1000": "1111111129"}

select_profile = {}

delay_pattern = ['0.0ms', '2.0ms', '6.0ms', '8.0ms']

test_result = []

test_round = []

test_report = {}

test_count = 10

direction = ['download', 'upload', 'download_with_load', 'upload_with_load']

CPE_IP_ADDR = ""
CPE_USERNAME = ""
CPE_PASSWORD = ""
CPE_COMMAND_PON = ""
CPE_COMMAND_REBOOT = ""
CPE_BAUDRATE = 115200
CPE_EVB = False

CPE_IP_ADDR_EVB = "192.168.100.1"
CPE_USERNAME_EVB = "telecomadmin"
CPE_PASSWORD_EVB = "nE7jA%5m"
CPE_COMMAND_PON_EVB = "tcapi set gpon_onu Password "
CPE_COMMAND_REBOOT_EVB = "\n\nreboot\n"

CPE_IP_ADDR_SFU = "192.168.100.1"
CPE_USERNAME_SFU = "admin"
CPE_PASSWORD_SFU = "1234"
CPE_COMMAND_PON_SFU = "set ont ploam_password "
CPE_COMMAND_REBOOT_SFU = "\n\nsys reboot\n"

DELAY_IP_ADDR = "10.1.1.191"
DELAY_USERNAME = "root"
DELAY_PASSWORD = "pqa1234"

SERVER_IP_ADDR = "10.1.1.192"
SERVER_USERNAME = "root"
SERVER_PASSWORD = "pqa1234"

CLIENT_IP_ADDR = "10.1.1.190"
CLIENT_USERNAME = "root"
CLIENT_PASSWORD = "pqa1234"

def enable_logging():
    # Enable the logging to console and file
    logging.basicConfig(level=output_logging,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename='iperf_auto.log',
                        filemode='a')

    console = logging.StreamHandler()
    console.setLevel(output_logging)
    formatter = logging.Formatter('%(levelname)-4s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.getLogger("paramiko").setLevel(logging.WARNING)

def configure_cpe(gpon_pass):
    if CPE_EVB==True:
        ssh_cpe(CPE_IP_ADDR, CPE_USERNAME, CPE_PASSWORD, CPE_COMMAND_PON + str(gpon_pass) + "\n" + "\n\ntcapi save" + "\n")
    else:
        ssh_cpe(CPE_IP_ADDR, CPE_USERNAME, CPE_PASSWORD, CPE_COMMAND_PON + str(gpon_pass) + "\n")

def configure_CPE_console(gpon_pass):
    console = serial.Serial('/dev/modem',baudrate=CPE_BAUDRATE,bytesize=8,parity='N',stopbits=1, timeout=5)
    console.open()
    if not console.isOpen():
        sys.exit()
    console.write("\r\n\r\n")
    time.sleep(1)
    input_data = console.read(console.inWaiting()).decode('utf-8', 'ignore')
    print (input_data)
    if "Username" in input_data:
        console.write((CPE_USERNAME + '\r\n').encode('utf-8', 'ignore'))
    time.sleep(1)
    input_data = console.read(console.inWaiting()).decode('utf-8', 'ignore')
    print(input_data)
    if "Password" in input_data:
        console.write((CPE_PASSWORD + '\r\n').encode('utf-8', 'ignore'))
    time.sleep(1)
    input_data = console.read(console.inWaiting()).decode('utf-8', 'ignore')
    print(input_data)
    console.write(("set ont ploam_password " + str(gpon_pass) + "\r\n").encode('utf-8', 'ignore'))
    console.close()

def reboot_cpe():
    ssh_cpe(CPE_IP_ADDR, CPE_USERNAME, CPE_PASSWORD, CPE_COMMAND_REBOOT)

def delay_start():
    ssh_connect(DELAY_IP_ADDR, DELAY_USERNAME, DELAY_PASSWORD, "/opt/iperf_auto/create.sh ")
    return

def delay_control(delay_ms):
    for i in range(10):
        ssh_connect(DELAY_IP_ADDR, DELAY_USERNAME, DELAY_PASSWORD, "/opt/iperf_auto/delay.sh " + delay_ms)
        time.sleep(3)
        delay_result = ssh_connect(DELAY_IP_ADDR, DELAY_USERNAME, DELAY_PASSWORD, "tc qdisc |grep netem")

        if delay_ms == "0.0ms":
            if "delay" not in delay_result:
                logging.info("Configure delay success: %s", delay_ms)
                break
            else:
                logging.info("Configure delay fail: %s", delay_ms)
                continue
        else:
            if delay_ms in delay_result:
                logging.info("Configure delay success: %s", delay_ms)
                break
            else:
                logging.info("Configure delay fail: %s", delay_ms)
                continue

def iperf_client(direction, filename, port, model):
    ssh_connect(CLIENT_IP_ADDR, CLIENT_USERNAME, CLIENT_PASSWORD,
                "/opt/iperf_auto/iperf_" + direction + ".sh " + str(model) + " " + str(port) + " " + filename )

def iperf_server():
    ssh_connect(SERVER_IP_ADDR, SERVER_USERNAME, SERVER_PASSWORD, "/opt/iperf_auto/iperf_server.sh")

def scan_result(filename):
    data_rate = 0
    lines = []
    lines = ssh_connect(CLIENT_IP_ADDR, CLIENT_USERNAME, CLIENT_PASSWORD, "cat " + filename)
    for line in lines.split("\n"):
        if "[SUM]" in line and "receiver" in line:
            data_rate = line.split()[5]
            #print(data_rate)
            #if data_rate == 0:
            #    print(data_rate)
    return data_rate

def generate_report(report_file, id):
    workbook = openpyxl.load_workbook(report_file)
    worksheet = workbook['result']

    today = date.today()
    fw_name = "test_report_" + today.strftime("%Y_%m_%d") + ".xlsx"

    x_cell = 3

    if id == 5:
        y_cell = 3
    else:
        y_cell = (id - 1) * 10 + (id - 1) + 3

    profile_count = 0
    for profile in test_report:
        for round in range(test_count):
            for data in test_report[profile][round]:
                worksheet.cell(y_cell, x_cell, ).value = float(data)
                x_cell += 1
            x_cell = 3
            y_cell += 1
        profile_count += 1
        x_cell = 3
        y_cell = profile_count * 10 + profile_count + 3

    workbook.save(fw_name)
    workbook.close()

def ssh_cpe(ip_addr, user, password, command):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    stdin = ''
    stdout = ''
    stderr = ''

    try:
        ssh_client.connect(hostname=ip_addr, port=22, username=user, password=password, timeout=5,
                           auth_timeout=5, banner_timeout=5)

        channel = ssh_client.get_transport().open_session()
        # logging.info("Connect to SSH server: %s", ip_addr)
        channel.get_pty()
        channel.invoke_shell()
        channel.send(command)
        time.sleep(2)
        stdout_output = channel.recv(9999)
        # print("Command Output:", stdout_output.decode())
        time.sleep(2)
        ssh_client.close()
        return
        # return stdout_output
    except Exception as e:
        logging.info("Connect CPE SSH fail: " + repr(e))
        print("Exception: ", repr(e))
        ssh_client.close()

def ssh_connect(ip_addr, user, password, command):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    stdin = ''
    stdout = ''
    stderr = ''
    stdout_output = ""
    stderr_output = ""
    try:
        #logging.info("Connect to SSH server: " + ip_addr)
        ssh_client.connect(hostname=ip_addr, port=22, username=user, password=password, timeout=10,
                           auth_timeout=10, banner_timeout=10)
        #stdin, stdout, stderr = ssh_client.exec_command(command=command, timeout=10)
        channel = ssh_client.get_transport().open_session()
        channel.exec_command(command=command)
        channel.shutdown_write()
        exit_code = channel.recv_exit_status()

        if "cat" in command or "tc qdisc" in command:
            stdout = channel.makefile().read().decode()
            #stderr = channel.makefile_stderr().read().decode()
            stdout_output = stdout

        #logging.info("Err: " + stderr_output + "\r\n")
        #logging.info("Out: " + stdout_output + "\r\n")
        channel.close()
        ssh_client.close()
        return stdout_output
    except Exception as e:
        logging.info("Connect Server SSH fail: " +  repr(e))
        print("Exception: ", repr(e))
        ssh_client.close()

if __name__ == '__main__':
    enable_logging()
    logging.info("Start PC2 Delay Server")
    delay_start()
    logging.info("Start PC3 Iperf Server")
    iperf_server()
    time.sleep(5)

    profile_id = int(sys.argv[2])

    if sys.argv[3]==1:
        CPE_EVB = True
    else:
        CPE_EVB = False

    port_num = int(sys.argv[4])
    project = sys.argv[5]

    if project == "1":
        project = "0"
    else:
        project = "1"

    if CPE_EVB==False:
        test_profile = copy.deepcopy(test_profile_HEX)
        CPE_IP_ADDR = CPE_IP_ADDR_SFU
        CPE_USERNAME = CPE_USERNAME_SFU
        CPE_PASSWORD = CPE_PASSWORD_SFU
        CPE_COMMAND_PON = CPE_COMMAND_PON_SFU
        CPE_COMMAND_REBOOT = CPE_COMMAND_REBOOT_SFU
    else:
        test_profile = copy.deepcopy(test_profile_ASCII)
        CPE_IP_ADDR = CPE_IP_ADDR_EVB
        CPE_USERNAME = CPE_USERNAME_EVB
        CPE_PASSWORD = CPE_PASSWORD_EVB
        CPE_COMMAND_PON = CPE_COMMAND_PON_EVB
        CPE_COMMAND_REBOOT = CPE_COMMAND_REBOOT_EVB

    if profile_id == 5:
        select_profile = copy.deepcopy(test_profile)
    elif profile_id == 1:
        select_profile = {k: v for k, v in test_profile.items() if k.startswith('100_40')}
    elif profile_id == 2:
        select_profile = {k: v for k, v in test_profile.items() if k.startswith('250_125')}
    elif profile_id == 3:
        select_profile = {k: v for k, v in test_profile.items() if k.startswith('1000_500')}
    elif profile_id == 4:
        select_profile = {k: v for k, v in test_profile.items() if k.startswith('2000_1000')}

    for profile in select_profile:
        try:
            logging.info("Configure CPE's GPON Password...... %s", select_profile[profile])
            configure_cpe(select_profile[profile])
            time.sleep(10)
            logging.info("Rebooting CPE...................... ")
            reboot_cpe()
            time.sleep(80)
        except Exception as e:
            logging.info("Configure CPE failed with %s", select_profile[profile])
        test_round = []

        logging.info("Testing Profile: %s", profile)
        if len(sys.argv) > 1:
            if test_count > 10:
                test_count = 10
            else:
                test_count = int(sys.argv[1])
        else:
            test_count = 10

        for round in range(1, test_count + 1):
            logging.info("Testing Round: %s", round)
            test_result = []
            for delay in delay_pattern:
                logging.info("Testing Delay: %s", delay)
                delay_control(delay)
                for type in direction:
                    file = "/opt/iperf_auto/log/" + "iperf_" + profile + "_" + str(
                        round) + "_" + delay + "_" + type
                    logging.info("Testing Type: %s", type)
                    logging.info("Start PC3 Iperf Client")
                    iperf_client(type, file, port_num, project)
                    time.sleep(90)
                    result = 0
                    for iPort in range(1,int(port_num)+1):
                        throughput_data = scan_result(file + "_p" + str(iPort) + ".txt")
                        logging.info(file + " Port: " + str(iPort) + " Throughput " + str(throughput_data) + " Mbps")
                        result = float(result) + float(throughput_data)
                    test_result.append(result)
                    logging.info(file + " Summary Throughput: " + str(result) + " Mbps")
            test_round.append(test_result)
        test_report[profile] = test_round

    logging.info("Output Excel Report")
    generate_report('test_report.xlsx', profile_id)
    logging.info("Test Finished")
    sys.exit(0)
