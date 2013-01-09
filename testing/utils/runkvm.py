#!/usr/bin/env python
import pexpect
import sys
import getopt, sys
import time
import os, commands
import setproctitle
import re

try:
        import argparse
except ImportError , e:
	module = str(e)[16:]
	sys.exit("we requires the python argparse module")

def read_exec_shell_cmd( ex, filename, prompt, timeout):
	if os.path.exists(filename):
		f_cmds = open(filename, "r")
		for line in f_cmds:
			print  line
			ex.sendline(line)  
			ex.expect (prompt,timeout=timeout, searchwindowsize=100) 
	else:
		print  filename 
		ex.sendline(filename)
		ex.expect (prompt,timeout=timeout, searchwindowsize=100)
	return

def compile_on (args):
	cmd = "sudo virsh console %s" % (args.hostname)
	timeout = 180
        child = pexpect.spawn (cmd)
#       child.logfile = f
	prompt = "root@%s " % (args.hostname) 

	a = child.expect (['Escape.*', 'Active console session exists for this domain', prompt])
	if a==0:
		child.sendline ('')
		i = child.expect (['login: ', 'Active console session exists', prompt], timeout=120) 
		if i==0:
			child.sendline ('root')
			child.expect ('Password:')
			child.sendline ('swan')
			child.expect ('root.*')
			print  'logged in as root on %s'%args.hostname
		elif i==1:
			print 'console is busy on host  %s'%args.hostname
			sys.exit(1) 
	elif i==1:
		print 'console is busy on host  %s'%args.hostname
		sys.exit(1) 

	if args.reboot:
		cmd = "reboot "
		print 'rebooting %s'%args.hostname
		child.sendline(cmd)
		i = child.expect (['login: ', 'Active console session exists', prompt], timeout=120) 
		if i==0:
			child.sendline ('root')
			child.expect ('Password:')
			child.sendline ('swan')
			child.expect ('root.*')
			print  'logged in as root on %s'%args.hostname

	prompt = "root@%s source" % (args.hostname) 
	cmd = "cd /source/"
	read_exec_shell_cmd( child, cmd, prompt, timeout)
	cmd = "make clean"
	read_exec_shell_cmd( child, cmd, prompt, timeout)
	cmd = "make programs install module_install"
	read_exec_shell_cmd( child, cmd, prompt, timeout)
			
	return  

def install ():
	return

def run_test(args):
	print 'HOST : ', args.hostname 
	print 'TEST : ', args.testname

	timeout = 180
	cmd = "%s-%s" % (sys.argv,args.hostname)
	setproctitle.setproctitle(cmd)

	output_file = "./OUTPUT/%s.boot-console.txt" % (args.hostname)
	f = open(output_file, 'w') 
	
	out = commands.getoutput("sudo virsh destroy %s"%args.hostname)
	cmd = "sudo virsh reset %s" % (args.hostname)
	r =  pexpect.spawn (cmd)
	time.sleep( 2 )
	time.sleep( 2 )
        out = commands.getoutput("sudo virsh start %s"%args.hostname)
        time.sleep( 2 )


	cmd = "sudo virsh console %s" % (args.hostname)
	child = pexpect.spawn (cmd)
	child.logfile = f
	time.sleep( 2 )

	a = child.expect (['Escape.*', 'Active console session exists for this domain'])
	if a==0:
		child.sendline ('')
		i = child.expect (['login: ', 'Active console session exists'], timeout=120) 
		if i==0:
			child.sendline ('root')
			child.expect ('Password:')
			child.sendline ('swan')
			child.expect ('root.*')
			print  'logged in as root'
		elif i==1:
			print 'console is busy'
			sys.exit(1) 

	prompt = "root@%s %s" % (args.hostname, args.testname) 

	cmd = "cd /testing/pluto/%s " % (args.testname)
	print cmd
	child.sendline(cmd)
	child.expect (prompt, searchwindowsize=100) 
	
	f.close
	output_file = "./OUTPUT/%s.console.txt" % (args.hostname)
	f = open(output_file, 'w') 
	child.logfile = f

	cmd = '/testing/guestbin/swanprep --testname %s --hostname %s'%(args.testname,args.hostname)
	read_exec_shell_cmd( child, cmd, prompt, timeout)
	
	cmd = "rm -fr /tmp/pluto.log"
	read_exec_shell_cmd( child, cmd, prompt, timeout) 

	cmd = 'ln -s /testing/pluto/%s/OUTPUT/pluto.%s.log /tmp/pluto.log'%(args.testname,args.hostname)
	read_exec_shell_cmd( child, cmd, prompt, timeout)

	cmd = './testparams.sh'
	read_exec_shell_cmd( child, cmd, prompt, timeout)

	cmd = "./%sinit.sh" %  (args.hostname) 
	read_exec_shell_cmd( child, cmd, prompt, timeout)

	cmd = "./%srun.sh" %  (args.hostname) 
	if os.path.exists(cmd):
		read_exec_shell_cmd( child, cmd, prompt, timeout)
		time.sleep(60)

	cmd = "END of test %s" % (args.testname)
	f.write(cmd)
	f.close 
	
	return  

def main():

	parser = argparse.ArgumentParser(description='runkvm arguments.')
	parser.add_argument('--testname', '-t', action='store', default='basic-pluto-01', help='The name of the test to run.')
	parser.add_argument('--hostname', '-H', action='store', default='east', help='The name of the host to run.')
	parser.add_argument('--compile', help='compile the source on east.')
	parser.add_argument('--reboot', help='first reboot the host')
	parser.add_argument('--timeout', default=120, help='timeout for each command for expect.')
	args = parser.parse_args()
	if args.compile:
		compile_on(args)
	run_test(args)
	return
if __name__ == "__main__":
	main()
