#!/usr/bin/env python

# This program is created by Zaur Molotnikov : https://github.com/qutorial/hosts
# 
# It is a modification of the work of
# - Steven Steven : https://github.com/StevenBlack/hosts
# and 
# - Ben Limmer : https://github.com/l1m5
# and a fork of
# https://github.com/StevenBlack/hosts

# 
#
# This simple Python script will combine all the host files you provide
# as sources into one, unique host file to keep you internet browsing happy.

# Making Python 2 compatible with Python 3
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import platform
import re
import string
import subprocess
import sys
import tempfile
import glob
# zip files are not used actually, support deleted
# StringIO is not needed in Python 3
# Python 3 works differently with urlopen

#Restarting in Python 3 if it exists
if sys.version < '3':
	python3 = os.popen('which python3 2> /dev/null').read().rstrip()
	if python3:
		args = sys.argv[:]
		args.insert(0,python3)
		os.execv(python3,args)
		quit();


# Supporting urlopen in Python 2 and Python 3
try:
	from urllib.parse import urlparse, urlencode
	from urllib.request import urlopen, Request
	from urllib.error import HTTPError
except ImportError:
	from urlparse import urlparse
	from urllib import urlencode
	from urllib2 import urlopen, Request, HTTPError

# This function handles both Python 2 and Python 3
def getFileByUrl(url):
	f = urlopen(url)
	return f.read().decode("UTF-8")		

# In Python 3   "print" is a function, braces are added everywhere

# Detecting Python 3 for version-dependent implementations
Python3=False;
cur_version = sys.version_info
if cur_version >= (3, 0):
	Python3=True;

# This function works in both Python 2 and Python 3
def myInput(msg=""):
	if Python3:
		return input(msg);
	else:
		return raw_input(msg);


# Cross-python writing function
def writeData(f, data):
	if Python3:
		f.write(bytes(data, 'UTF-8'))
	else:
		f.write(str(data).encode('UTF-8'))

# This function doesn't list hidden files
def listdir_nohidden(path):
	return glob.glob(os.path.join(path, '*'))

# Project Settings
BASEDIR_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(BASEDIR_PATH, 'data')
DATA_FILENAMES = 'hosts'
UPDATE_URL_FILENAME = 'update.info'
SOURCES = listdir_nohidden(DATA_PATH)
README_TEMPLATE = os.path.join(BASEDIR_PATH, 'readme_template.md')
README_FILE = os.path.join(BASEDIR_PATH, 'readme.md')
TARGET_HOST = '127.0.0.1'
WHITELIST_FILE = os.path.join(BASEDIR_PATH, 'whitelist')
DNSMASQ_CONF_DST = '/etc/dnsmasq.excludes.conf'
DNSMASQ_CONF_MAIN_FILE = '/etc/dnsmasq.conf'
DNSMASQ_CONF_GENERATED = os.path.join(BASEDIR_PATH, 'dnsmasq.excludes.conf')
GenerateDnsmasqConf = False;

emptyRe=re.compile(r'^\s*$')
def isEmptyLine(s):
	return emptyRe.match(s) is not None

domainCore=r'[\w\d-]{,63}(\.[\w\d-]{,63})*';
validDomainRe=re.compile(r'^' + domainCore + r'$')
def isValidDomain(d):	
	return validDomainRe.match(d) is not None

#Adblock Plus Format
abpDomainRe=re.compile(r'^\|\|' + domainCore + r'\^$');
def isAbpDomain(d):
	return abpDomainRe.match(d) is not None

ipAddressCore=r'\d+\.\d+.\d+.\d+'
hostsLineRe=re.compile(r'^\s*' + ipAddressCore +'\s*' + domainCore + '\s*$')
def isHostsLine(l):
	return hostsLineRe.match(l) is not None

multipleDomainsHostsLineRe=re.compile(r'^\s*' + ipAddressCore +'\s+(' + domainCore + r'\s*)+$');
def isMultipleDomainsHostsLine(l):
	return multipleDomainsHostsLineRe.match(l) is not None

# Such lines from sa-blacklist
# blacklist_from *@*.doctorsem.ru
# blacklist_from *@doctorlhadning.ru
saRe=re.compile(r'^\s*blacklist_from' + r'\s+' + r'\**\@*\**\.*(' + domainCore + r')\s*$');
def isSaHostLine(l):
	return saRe.match(l) is not None

def getSaHost(l):
	return saRe.match(l).groups()[0];

commentRe=re.compile(r'^(\s)*#(.)*$')
def isComment(l):
	return commentRe.match(l) is not None

exclCommentRe=re.compile(r'^(\s)*!(.)*$')
def isExclComment(l):
	return exclCommentRe.match(l) is not None

def cutFirstSubDomain(domain):
	pos = domain.find(".")
	if pos == -1:
		return ("", domain);
	else:
		return (domain[0:pos], domain[pos+1:]);

wwwRe = re.compile(r'^www(\d)*$');
def isWwwSubDomain(domain):
	return wwwRe.match(domain) is not None;

# Exclutions from whitelist file
EXCLUSIONS = []

# Global vars
exclusionRegexs = []
numberOfRules = 0
dnsmLines = 0;

def compileExclusionRegexes():
	for ex in EXCLUSIONS:
		# subdomains of the domain
		s = r'^(' + domainCore + r'\.)*' + ex.replace(".",r"\.") + r'$'
		exclusionRegexs.append(re.compile(s))

def promptForDnsmasq():
	global GenerateDnsmasqConf
	if( "yes" == query_yes_no("Generate a dnsmasq.conf?")):
		GenerateDnsmasqConf = True;
	if not os.path.exists(DNSMASQ_CONF_MAIN_FILE):
		print("""You do not have dnsmasq installed, it is a more secure option for blocking domains by name.""");
		print("""Read more at: http://molotnikov.de/dnsmasq""");

BlockSubdomains = True;
def promptBlockSubdomains():
	global BlockSubdomains;
	if("no" == query_yes_no("Block subdomains of the whitelisted domains?", default="yes")):
		BlockSubdomains = False;
	r = ""
	if not BlockSubdomains:
		r = "not "
	print("Will %sblock subdomains of whitelisted domains" % r)
	
def listWhitelisted():
	print("These domains are whitelisted:")
	for d in EXCLUSIONS:
		print(d)

def main():
	promptForDnsmasq()
	promptForUpdate()
	excludeFromFile()
	listWhitelisted()
	promptBlockSubdomains()
	compileExclusionRegexes()
	print("Compiling the list, this might take a while...")
	mergeFile = createInitialFile()
	finalFile = removeDupsAndExcl(mergeFile)
	finalizeFile(finalFile)
	updateReadme(numberOfRules)
	printSuccess('Success! Your shiny new hosts file has been prepared.\nIt contains ' + "{:,}".format( numberOfRules ) + ' unique entries.')
	if GenerateDnsmasqConf:
		print( "{:,}".format( dnsmLines ) + ' lines in dnsmasq configuration file' );

	promptForMove(finalFile)

# Exclusion from file
def excludeFromFile():
	if os.path.isfile(WHITELIST_FILE):
		with open(WHITELIST_FILE, "r") as ins:
			for line in ins:
				if not (isEmptyLine(line) or isComment(line)):
					if not isValidDomain(line):
						print("Your whitelist contains invalid domain name: ", line);
						exit(0);
					else:
						print("Excluding from whitelist: ", line.strip()); 
						excludeDomain(line);

# Prompt the User
def promptForUpdate():
	response = query_yes_no("Do you want to update all data sources?")
	if (response == "yes"):
		updateAllSources()
	else:
		print ('OK, we\'ll stick with what we\'ve  got locally.')

def promptForMove(finalFile):
	print("!! Make sure to backup your hosts file before replacing it !!");
	question="Do you want to replace your existing hosts file with the newly generated file?"
	#Host file does not have to be replaced, when dnsmasq is used
	response = "no";
	if GenerateDnsmasqConf == True:
		question = question + """ (Not needed when dnsmasq is used)"""
		response = query_yes_no(question, default="no")
	else:
		response = query_yes_no(question)
	
	if (response == "yes"):
		moveHostsFileIntoPlace(finalFile)
  
	if GenerateDnsmasqConf:
		if ("yes" == query_yes_no("Do you want to update your dnsmasq configuration?")):
			updateDnsmasqConf();
  
# End Prompt the User

def excludeDomain(domain):
	if isEmptyLine(domain):
		print("Passing empty line to exclude domain!");
		return;
	domain = domain.strip();	
	if not isValidDomain(domain):
		print("Domain name ", domain, " is not a valid domain name");
		return;
	else:		
		EXCLUSIONS.append(domain);

def matchesExclusions(domain):
	global BlockSubdomains;
	if BlockSubdomains:
		return domain in EXCLUSIONS;
	else:
		for exclusionRegex in exclusionRegexs:
			if exclusionRegex.match(domain) is not None:
				return True
		return False


# Update Logic
def updateSource(source):
	updateURL = getUpdateURLFromFile(source)
	if (updateURL == None):
		return;
	print ('Updating source ' + updateURL)
	# Cross-python call
	resPath = os.path.join(DATA_PATH, source, DATA_FILENAMES)
	try:
		updatedFile = getFileByUrl(updateURL);
		updatedFile = updatedFile.replace('\r', '') #get rid of carriage-return symbols
		# This is cross-python code
		dataFile = open(resPath, 'wb')
		writeData(dataFile, updatedFile)
		dataFile.close()
	except:
		print ("Problem getting file: ", updateURL)
	if not os.path.exists(resPath):
		dataFile = open(resPath, 'wb')
		dataFile.close()

def updateAllSources(): 
	for source in SOURCES:
		updateSource(source)

def getUpdateURLFromFile(source):
	pathToUpdateFile = os.path.join(DATA_PATH, source, UPDATE_URL_FILENAME)
	if os.path.exists(pathToUpdateFile):
		updateFile = open(pathToUpdateFile, 'r')
		retURL = updateFile.readline().strip()
		updateFile.close()
	else:
		retURL = None
		printFailure('Warning: Can\'t find the update file for source ' + source + '\n' +
					 'Make sure that there\'s a file at ' + pathToUpdateFile)
	return retURL
# End Update Logic

def writeLine(dstFile, line=""):
	writeData(dstFile, line + os.linesep)
	
def pumpHosts(srcFile, dstFile):
	for l in srcFile.readlines():
		if isComment(l):
			writeLine(dstFile, l)
		elif isExclComment(l):
			writeLine(dstFile, "#" + l.replace("!", ""))
		else:
			l = l.strip();
			if isHostsLine(l):
				writeLine(dstFile, l)
			elif isValidDomain(l):
				writeLine(dstFile, "0.0.0.0 " + l)
			elif isAbpDomain(l):
				writeLine(dstFile, "0.0.0.0 " + l[2:-1])
			#elif isMultipleDomainsHostsLine(l):
			#	for ll in l.split():
			#		if isValidDomain(ll):
			#			writeLine(dstFile, "0.0.0.0 " + l);
			#Handling lehigh.edu
			elif len(l.split()) >= 2:
				for d in l.split():
					if isValidDomain(d) and ("." in d):
						writeLine(dstFile, "0.0.0.0 " + d);
			elif isSaHostLine(l):
				writeLine(dstFile, "0.0.0.0 " + getSaHost(l));
			else:
				print("Could not handle this line: " + l);
				continue;

# File Logic
def createInitialFile():
	mergeFile = tempfile.NamedTemporaryFile()
	for source in SOURCES:
		with open(os.path.join(DATA_PATH, source, DATA_FILENAMES), 'r') as curFile:
			#Done in a cross-python way
			writeData(mergeFile, '\n# Begin ' + source + '\n')
			pumpHosts(curFile, mergeFile);		
			writeData(mergeFile, '\n# End ' + source + '\n')

	return mergeFile

def makeRule(hostname):
	return "%s %s\n" % (TARGET_HOST, hostname)

def makeDnsmRule(hostname):
	return "address=/%s/127.0.0.1\n" % hostname;

def removeDupsAndExcl(mergeFile):
	global numberOfRules
	global dnsmLines
	hosts_path = os.path.join(BASEDIR_PATH, 'hosts')
	#if no such file - create it
	if not os.path.isfile(hosts_path):
		open(hosts_path, "a").close();
    
    # Another mode is required to read and write the file in Python 3
	finalFile = open(hosts_path, 'r+b')
	mergeFile.seek(0) # reset file pointer

	hostnames = set()
	hostnames.add("localhost")
	
	hostnames_dnsm = set()
	hostnames_dnsm.add("localhost")
	
	dnsmfile = None;	
	if GenerateDnsmasqConf:
		dnsmfile = open(DNSMASQ_CONF_GENERATED, 'wb');
	
	
	excludedWhiteListed=set()
	
	for line in mergeFile.readlines():
		write = 'true'
        # Explicit encoding
		line = line.decode("UTF-8")		
		if isEmptyLine(line):
			writeData(finalFile, os.linesep);
			continue;
		
		line = line.strip();
		
		# Testing the first character doesn't require startswith
		if isComment(line):
			# Cross-python write
			writeData(finalFile, line)
			continue

		strippedRule = stripRule(line) #strip comments
		if isEmptyLine(strippedRule):
			continue;
		domain = strippedRule.split()[1]
		
		hostname, normalizedRule = normalizeRule(strippedRule) # normalize rule
		
		# cut trailing dots for sure
		while hostname.endswith("."):
			hostname = hostname[:-1]
			
		if normalizedRule:
			if matchesExclusions(hostname):
				if not hostname in excludedWhiteListed:
					print("Domain from whitelist excluded:", hostname)
					excludedWhiteListed.add(hostname)
				continue
			
			if hostname not in hostnames:
				writeData(finalFile, makeRule(hostname))
				numberOfRules += 1
				hostnames.add(hostname);
				
			if GenerateDnsmasqConf:
				if hostname not in hostnames_dnsm:
					# cut www. but not from www.com
					(first, rest) = cutFirstSubDomain(hostname)
					if isWwwSubDomain(first):
						if not "." in rest:
							writeData(dnsmfile, makeDnsmRule(hostname))
							dnsmLines += 1
							hostnames_dnsm.add(hostname);
						else:
							if matchesExclusions(rest):
								if not rest in excludedWhiteListed:
									print("Domain from whitelist excluded:", rest)
									excludedWhiteListed.add(rest)
								continue
							elif rest not in hostnames_dnsm:
								writeData(dnsmfile, makeDnsmRule(rest))
								dnsmLines += 1
								hostnames_dnsm.add(rest);
					else:
						writeData(dnsmfile, makeDnsmRule(hostname));
						dnsmLines += 1
						hostnames_dnsm.add(hostname);

	if GenerateDnsmasqConf:
		dnsmfile.close();
	
	mergeFile.close()
	
	for d in EXCLUSIONS:
		if d not in excludedWhiteListed:
			print("This domain was whitelisted, but was not found among the blocked hosts: ", d)

	return finalFile

def normalizeRule(rule):
	result = re.search(r'^[ \t]*(\d+\.\d+\.\d+\.\d+)\s+([\w\.-]+)(.*)',rule)
	if result:
		target, hostname, suffix = result.groups()
		hostname = hostname.lower() # explicitly lowercase hostname
		if suffix is not '':
				print("Suffix %s ignored in the rule %s" % (suffix, rule))
		return hostname, makeRule(hostname)
	#Just ignoring the frequent case ::1 localhost, which we do not report
	if not "::1" in rule:
		print ('This rule has not be parsed properly: ', rule)
	return None, None

def finalizeFile(finalFile):
	writeOpeningHeader(finalFile)
	finalFile.close()

# Some sources put comments around their rules, for accuracy we need to strip them
# the comments are preserved in the output hosts file
def stripRule(line):
	splitLine = line.split()
	if (len(splitLine) < 2) :
		# just return blank
		return ''
	else:
		return splitLine[0] + ' ' + splitLine[1]

def writeOpeningHeader(finalFile):
	global numberOfRules
	finalFile.seek(0) #reset file pointer
	fileContents = finalFile.read(); #save content
	finalFile.seek(0) #write at the top
	writeData(finalFile, '# This file is a merged collection of hosts from reputable sources,\n')
	writeData(finalFile, '# with a dash of crowd sourcing via Github\n#\n')
	writeData(finalFile, '# Project home page: https://github.com/StevenBlack/hosts\n#\n')
	writeData(finalFile, '# Current sources:\n')
	for source in SOURCES:
		writeData(finalFile, '#    ' + source + '\n')
	writeData(finalFile, '#\n')
	writeData(finalFile, '# Merging these sources produced ' + "{:,}".format( numberOfRules ) + ' unique entries\n')
	writeData(finalFile, '# ===============================================================\n')
	writeData(finalFile, '\n')
	writeData(finalFile, '127.0.0.1 localhost\n')
	writeData(finalFile, '\n')
	
	preamble = os.path.join(BASEDIR_PATH, "myhosts");
	if os.path.isfile(preamble):
		print("Writing myhosts file as a preamble...");
		with open(preamble, "r") as f:
			writeData(finalFile, f.read());
	
	finalFile.write(fileContents)

def updateReadme(numberOfRules):
	with open(README_FILE, "wt") as out:
		for line in open(README_TEMPLATE):
			out.write(line.replace('@NUM_ENTRIES@', "{:,}".format( numberOfRules )))

def updateDnsmasqConf():
	print ('Moving the file requires administrative privileges. You might need to enter your password.')
	if(subprocess.call(["/usr/bin/sudo", "cp", DNSMASQ_CONF_GENERATED, DNSMASQ_CONF_DST])):
		printFailure("Moving the file failed.")
	AddingConfLine="conf-file="+DNSMASQ_CONF_DST;
	with open(DNSMASQ_CONF_MAIN_FILE, "r") as mainconf:
		lines = mainconf.readlines()		
		found = False
		for line in lines:
				if AddingConfLine in line and not isComment(line):
					found = True
					break;
		if not found:
			print("The configuration file ", DNSMASQ_CONF_MAIN_FILE, "  does not include ", DNSMASQ_CONF_DST, "!");
			print("Fixing it...");
			command = "echo \"\" >> "+ DNSMASQ_CONF_MAIN_FILE +" && echo " + AddingConfLine +" >> " + DNSMASQ_CONF_MAIN_FILE;
			os.system(""" sudo bash -c "%s" """ % command);	
			print("Success!");
		
	print("Restarting dnsmasq");
	os.system("sudo service dnsmasq restart");

def moveHostsFileIntoPlace(finalFile):
	if (os.name == 'posix'):
		print ('Moving the file requires administrative privileges. You might need to enter your password.')
		if(subprocess.call(["/usr/bin/sudo", "cp", os.path.abspath(finalFile.name), "/etc/hosts"])):
			printFailure("Moving the file failed.")
		if (platform.system() == 'Darwin'):
			print ('Flushing the DNS Cache to utilize new hosts file: killing DNS Responder...')
			if(subprocess.call(["/usr/bin/sudo", "killall", "-HUP", "mDNSResponder"])):
				printFailure("Flushing the DNS Cache failed.")
		else:
			if os.path.isfile("/etc/rc.d/init.d/nscd"):
				print ('Flushing the DNS Cache to utilize new hosts file: running nscd restart...')
				if(subprocess.call(["/usr/bin/sudo", "/etc/rc.d/init.d/nscd", "restart"])):
					printFailure("Flushing the DNS Cache failed.")
	elif (os.name == 'nt'):
		print ('Automatically moving the hosts file in place is not yet supported.')
		print ('Please move the generated file to %SystemRoot%\system32\drivers\etc\hosts')

# End File Logic

# Helper Functions
## {{{ http://code.activestate.com/recipes/577058/ (r2)
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":"yes",   "y":"yes",  "ye":"yes",
             "no":"no",     "n":"no"}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while 1:
        sys.stdout.write(colorize(question, colors.PROMPT) + prompt)
        # Changed to be cross-python
        choice = myInput().lower()
        if default is not None and choice == '':
            return default
        elif choice in valid.keys():
            return valid[choice]
        else:
            printFailure("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")
## end of http://code.activestate.com/recipes/577058/ }}}

def isValidDomainFormatInteractive(domain):
	if (domain == ''):
		print ("You didn\'t enter a domain. Try again.")
		return False	
	if not isValidDomain(domain):
		print ("The domain " + domain + " is not valid. We expect something like \"domain.com\" only as input. Try again, please.")
		return False
	else:
		return True

# Colors
class colors:
    PROMPT 	= '\033[0m'
    SUCCESS = '\033[0m'
    FAIL 	= '\033[0m'
    ENDC 	= '\033[0m'

def colorize(text, color):
	return color + text + colors.ENDC

def printSuccess(text):
	print (colorize(text, colors.SUCCESS))

def printFailure(text):
	print (colorize(text, colors.FAIL))
# End Helper Functions

if __name__ == "__main__":
	main()
