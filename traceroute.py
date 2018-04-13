#!/usr/bin/python
# -*- coding: UTF-8 -*-

import socket
import os
import sys
import struct
import time
import select
import binascii  

from random import randint


ICMP_ECHO_REQUEST = 8 #ICMP type code for echo request messages
ICMP_ECHO_REPLY = 11 #ICMP type code for echo reply messages

# calculate checksum for the packet
def checksum(string): 
	csum = 0
	countTo = (len(string) // 2) * 2 
	count = 0

	while count < countTo:
		thisVal = ord(string[count+1]) * 256 + ord(string[count]) 
		csum = csum + thisVal 
		csum = csum & 0xffffffff 
		count = count + 2

	if countTo < len(string):
		csum = csum + ord(string[len(string) - 1])
		csum = csum & 0xffffffff

	csum = (csum >> 16) + (csum & 0xffff)
	csum = csum + (csum >> 16)
	answer = ~csum 
	answer = answer & 0xffff
	answer = answer >> 8 | (answer << 8 & 0xff00)

	if sys.platform == 'darwin':
		answer = socket.htons(answer) & 0xffff
	else:
		answer = socket.htons(answer)

	return answer
	
def createPacket(icmpSocket, destinationAddress, ID):
	# Build ICMP header
	header = struct.pack('BBHHH', ICMP_ECHO_REQUEST, 0, 0, ID, 1)
	# Checksum ICMP packet using given function
	checksumResult = checksum(header)
	# Insert checksum into packet
	header = struct.pack('BBHHH', ICMP_ECHO_REQUEST, 0, checksumResult, ID, 1)
	return header
	
def trace(destinationAddress, port, numHops, timesOut, tries):
	try:
		PROTO2 = socket.getprotobyname('icmp')
		try:
			# get host name
			address = socket.gethostbyname(destinationAddress)
		except socket.gaierror:
			print("no such site exists")
		# print info
		print("traceroute to " + destinationAddress + "(" + str(address) + ")" + ", " + str(numHops) + " hops max")
		ttl = 1
		# rounds is for each trace link
		rounds = 1
		# array holds times
		array = []
		# calculates errors/timeouts
		timeouts = 0
		errors = 0
		while True:
			# checks if ttl exceeds current hop
			if ttl > numHops:
				sys.exit()
			# starts measuring time
			currentTime = time.time()
			# creates new socket and packet and sets sockopt to it
			sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, PROTO2)
			packet = createPacket(sock, destinationAddress, 5)
			sock.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
			# print round number, only at the start (to avoid multiple prints at each repeated measurement)
			if(rounds == 1):
				print(" " + str(ttl) + " "),
			# sends packet
			sock.sendto(packet, (address, port))
			try:
				# sets timeout so it doesn't get stuck
				sock.settimeout(timesOut)
				# receive info from packet and calc time
				blank, hopAddress = sock.recvfrom(1024)
				hopAddress = hopAddress[0]
				arrivalTime = time.time()
				sock.close()
				# try to get address in form of xyxyxy.xy
				try:
					hopLocation = socket.gethostbyaddr(hopAddress)[0]
				# else just leave it at IP
				except socket.herror:
					hopLocation = hopAddress
				# ensure it prints location once if it's reached
				if hopLocation is not None and rounds == 1 or "* " == array[0]:
					print(str(hopLocation)),
				# ensure its print IP address once if it's reached
				if rounds == 1 or "* " == array[0]:
					print("(" + str(hopAddress) + ")"),
					# print out error *'s
					array.insert(0, "empty")
					print "* " * timeouts,
				# add times to array for future calculations and print it
				array.append(str((arrivalTime-currentTime)*1000) + "ms   ")
				print(str((arrivalTime-currentTime)*1000) + "ms   "),
				# if reached destination
				if address == hopAddress and rounds == tries:
					# prints no. of errors encountered along the traceroute
					print("\n\nDESTINATION REACHED -> " + str(errors) + " packets lost along the traceroute")
					sys.exit()
				# if repeated measurement end, move along the route
				if(rounds == tries):
					print("")
					ttl += 1
					rounds = 0
					array = []
					timeouts = 0
				rounds +=1
			# handles timeouts, aka. adds *, prints it and if no. of repeated
			# measurements reached, go to the next hop link and reset counters
			except socket.timeout:
				array.append("* ")
				timeouts += 1
				errors += 1
				if(rounds == tries):
					print "* " * timeouts
					ttl += 1
					rounds = 0
					n = 0
				rounds += 1
	except KeyboardInterrupt:
		sys.exit()

def main():
	# asks for user input
	try:
		print("Address to trace:"),
		adrChoice = raw_input()
		print("Max hops to jump:"),
		hopChoice = raw_input()
		print("Timeout in secs:"),
		timeChoice = raw_input()
		print("No. of repeated measurements:"),
		repChoice = raw_input()
		trace(adrChoice, 80, int(hopChoice), float(timeChoice), int(repChoice))
	except KeyboardInterrupt:
		print("EXIT")
	
main()

#call file with sudo/admin privileges