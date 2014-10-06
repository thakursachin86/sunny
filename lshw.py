#!/usr/bin/python

import subprocess,re,json,uuid,httplib
import sys
import xml.etree.ElementTree as ET

mining = {}

cmd1=subprocess.Popen("dmidecode -t system | grep 'Manufacturer' | awk -F ' ' '{print $2}'",shell=True,stdout=subprocess.PIPE).communicate()[0]
vendor='\n'.join(cmd1.splitlines())

cmd2=subprocess.Popen("dmidecode -t system | grep 'Product Name' | awk -F ' ' '{print $3}'",shell=True,stdout=subprocess.PIPE).communicate()[0]
model='\n'.join(cmd2.splitlines())

cmd3=subprocess.Popen("dmidecode -t chassis | grep 'Serial Number' | awk -F ' ' '{print $3}'",shell=True,stdout=subprocess.PIPE).communicate()[0]
chassis_serial='\n'.join(cmd3.splitlines())

cmd4=subprocess.Popen("dmidecode -t baseboard | grep 'Serial Number' | awk -F ' ' '{print $3}'",shell=True,stdout=subprocess.PIPE).communicate()[0]
board_serial='\n'.join(cmd4.splitlines())

subprocess.call("modprobe dcmi",shell=True)
cmd5=subprocess.Popen("dcmitool lan print | egrep -e '^IP.*[0-9]$' | awk '{print $4}'",shell=True,stdout=subprocess.PIPE).communicate()[0]
ipmi_ip='\n'.join(cmd5.splitlines())

cmd6=subprocess.Popen("dcmitool lan print | egrep -e '^MAC' | awk '{print $4}'",shell=True,stdout=subprocess.PIPE).communicate()[0]
ipmi_mac='\n'.join(cmd6.splitlines())

pxe_mac= ':'.join(re.findall('..', '%012x' % uuid.getnode()))

cmd7=subprocess.Popen("grep 'model name' /proc/cpuinfo | sort -u | awk -F ' ' '{print $4 \" \" $5 \" \" $6 \" \" $7 \" \" $8 \" \" $9 \" \" $10}'",shell=True,stdout=subprocess.PIPE).communicate()[0]
cpu_model='\n'.join(cmd7.splitlines())

cmd8=subprocess.Popen("grep 'model name' /proc/cpuinfo | sort -u | awk -F ' ' '{print $10}'",shell=True,stdout=subprocess.PIPE).communicate()[0]
cpu_clock='\n'.join(cmd8.splitlines())

cmd9=subprocess.Popen("grep 'cores' /proc/cpuinfo | sort -u | awk '{print $4}'",shell=True,stdout=subprocess.PIPE).communicate()[0]
cpu_cores='\n'.join(cmd9.splitlines())

cmd10=subprocess.Popen("grep 'MemTotal' /proc/meminfo | cut -d: -f2 | awk -F ' ' '{print $1 \" \" $2 }'",shell=True,stdout=subprocess.PIPE).communicate()[0]
total_memory='\n'.join(cmd10.splitlines())

cmd11=subprocess.Popen("dmidecode -t bios | grep 'Version' | awk -F ' ' '{print $2}'",shell=True,stdout=subprocess.PIPE).communicate()[0]
bios_firmware_version='\n'.join(cmd11.splitlines())

cmd12=subprocess.Popen("dmidecode -t bios | grep 'Firmware Revision' | awk -F ' ' '{print $3}'",shell=True,stdout=subprocess.PIPE).communicate()[0]
mc_firmware_revision='\n'.join(cmd12.splitlines())

command = 'lshw -xml'
hwinfo_xml = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,shell=True).communicate()[0]
root = ET.fromstring(hwinfo_xml)

disk_list = root.findall(".//node[@class='disk']")

for disk in disk_list:
        mining ['disk_model'] = disk.find('description').text
        mining ['disk_size'] = str(int(disk.find('size').text) / (1000**3)) + 'GB'
        mining ['disk_firmware_version'] = disk.find('version').text

mega_list = root.findall(".//node[@class='disk']")

mining['controller'] = {}
for mega in mega_list:
        if mega.find('vendor').text == 'LSI':
                mining['controller'] = {}
                mining['controller']['lsi_megaraid_product'] = mega.find('product').text
                mining['controller']['lsi_megaraid_vendor'] = mega.find('vendor').text
                cmd13=subprocess.Popen("megacli  -AdpAllinfo -a0 | grep 'FW Version' |  awk -F ' ' '{print $4}'",shell=True,stdout=subprocess.PIPE).communicate()[0]
                mining['controller']['lsi_megaraid_firmware'] = '\n'.join(cmd13.splitlines())

onboard_nic_list = root.findall(".//node[@class='network']")
mining ['interfaces'] = {}        
for onboard_nic in onboard_nic_list:
        if onboard_nic.find('vendor').text == 'Intel Corporation':
		mining ['interfaces']['onboard_nic_product'] = onboard_nic.find('product').text
                mining ['interfaces']['onboard_nic_vendor']  = onboard_nic.find('vendor').text
                mining ['interfaces']['onboard_nic_mac'] = onboard_nic.find('serial').text
                firmware = onboard_nic.findall(".//setting[@id='firmware']")
                for firm in firmware:
                        mining ['interfaces']['onboard_nic_firmware'] = firm.attrib["value"]
                driver = onboard_nic.findall(".//setting[@id='driver']")
                for driver in driver:
                        mining ['interfaces']['onboard_nic_driver'] = driver.attrib["value"]
                        
                driverversion = onboard_nic.findall(".//setting[@id='driverversion']")
                for driverversion in driverversion:
                        mining ['interfaces']['onboard_nic_driverversion'] = driverversion.attrib["value"]
                        
                ipaddr = onboard_nic.findall(".//setting[@id='ip']")
                for ip in ipaddr:
                        onboard_nic_ip = ip.attrib["value"]
                        
pcie_nic_list = root.findall(".//node[@class='network']")

for pcie_nic in pcie_nic_list:
        if pcie_nic.find('vendor').text == 'Mellanox Technologies':
                mining ['interfaces']['pcie_nic_product'] = pcie_nic.find('product').text
                mining ['interfaces']['pcie_nic_vendor'] = pcie_nic.find('vendor').text
                mining ['interfaces']['pcie_nic_mac'] = pcie_nic.find('serial').text
                firmware = pcie_nic.findall(".//setting[@id='firmware']")
                for firm in firmware:
                        mining ['interfaces']['pcie_nic_firmware'] = firm.attrib["value"]
                driver = pcie_nic.findall(".//setting[@id='driver']")
                for driver in driver:
                        mining ['interfaces']['pcie_nic_driver'] = driver.attrib["value"]
                        
                driverversion = pcie_nic.findall(".//setting[@id='driverversion']")
                for driverversion in driverversion:
                        mining ['interfaces']['pcie_nic_driverversion'] = driverversion.attrib["value"]


mining ['vendor'] = vendor
mining ['model'] = model
mining ['chassis_serial'] = chassis_serial
mining ['board_serial'] = board_serial
mining ['bios_firmware_version'] = bios_firmware_version 
mining ['mc_firmware_revision'] = mc_firmware_revision
mining ['ipmi_ip'] = ipmi_ip
mining ['ipmi_mac'] = ipmi_mac
mining ['pxe_mac'] = pxe_mac
mining ['cpu_model'] = cpu_model
mining ['cpu_clock'] = cpu_clock
mining ['cpu_cores'] = cpu_cores
mining ['total_memory'] = total_memory

json_mining = json.dumps(mining)

print json_mining

#headers = {"Content-type": "application/json"}

#c = httplib.HTTPConnection("10.10.10.225:8000")
#c.request("POST", "/adminui/registerPhysicalServer/", json_mining, headers)
