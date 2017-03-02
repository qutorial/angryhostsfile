#Angry Hosts File - blocking unwanted hosts

This tool can produce a hosts file or a dnsmasq configuration, which will 
block many of "unwanted" hosts: trackers, ads, etc.

The *philosophy* is to block everything, even when suspicions are little. It is a
paranoia tool. It is very angry in this sense.

Use whitelist to make it less angry :)

A tool to configure dnsmasq or `hosts` file using a merge from a 
number of different sources.

This is a modified version of the original Steven Black's work.
The differences are:
* Hosts Tool is just a tool, we do not provide a hosts file, but the tool builds it
* This tool configures dnsmasq in addition to hosts file, it provides stronger blocking
* It contains more hosts sources, blocking more than 430K hosts
* It works with unicode domain names
* We give you the option to block or not to block subdomains of the whitelisted domains
* You have to put the whitelisted domains in the `whitelist` file

**Currently this hosts file contains 679,959 unique entries.**

## Source of host data amalgamated here

Currently the `hosts` files from the following locations are amalgamated:

* The [Adaway hosts file](http://adaway.org/hosts.txt), updated regularly.
* MVPs.org Hosts file at [http://winhelp2002.mvps.org/hosts.htm](http://winhelp2002.mvps.org/hosts.htm), updated monthly, or thereabouts.
* Dan Pollock at [http://someonewhocares.org/hosts/](http://someonewhocares.org/hosts/) updated regularly.
* Malware Domain List at [http://www.malwaredomainlist.com/](http://www.malwaredomainlist.com/), updated regularly.
* Peter Lowe at [http://pgl.yoyo.org/adservers/](http://pgl.yoyo.org/adservers/), updated regularly.
* Small list of Steven Black in raw form [here](https://raw.github.com/StevenBlack/hosts/master/data/StevenBlack/hosts).
* Qutorial's list [here](https://raw.githubusercontent.com/qutorial/hosts/master/data/Qutorial/hosts).
* And some more:
	* [adzhosts](http://downloads.sourceforge.net/project/adzhosts/HOSTS.txt?r=&ts=1447427220&use_mirror=skylink)
	* [hosts-file.net](http://hosts-file.net/download/hosts.txthttp://jansal.googlecode.com/svn/trunk/adblock/hosts)
	* [adzhosts2](http://skylink.dl.sourceforge.net/project/adzhosts/HOSTS.txt)
	* [adzhosts3](http://optimate.dl.sourceforge.net/project/adzhosts/HOSTS.txt)
	* [disonnect.me ads](https://s3.amazonaws.com/lists.disconnect.me/simple_ad.txt)
	* [disconnect.me tracking](https://s3.amazonaws.com/lists.disconnect.me/simple_tracking.txt)
	* [sa-blacklist](http://www.sa-blacklist.stearns.org/sa-blacklist/sa-blacklist.current)
	* [zeustracker.abuse.ch](https://zeustracker.abuse.ch/blocklist.php?download=domainblocklist)
	* [malwaredomains.lehigh.edu](http://malwaredomains.lehigh.edu/files/domains.txt)
	* [securemecca.com](http://securemecca.com/Downloads/hosts.txt)
	* [adblockplus malware](https://easylist-downloads.adblockplus.org/malwaredomains_full.txt)


You can add additional sources by placing them in the `data/` directory. Provide a copy of that new
`hosts` file, and place its update url in `update.info`. The `updateHostsFile.py` routine will
automatically refresh the `hosts` file from source each time a new amalgamated file is generated.


## How do I incorporate my own hosts?

If you have custom host records, place them in file `myhosts`.  The contents of this file are prepended to the amalgamated hosts file during the update process.

Once used with dnsmasq, just keep your hosts file untouched by Hosts Tool.

## Using updateHostsFile.py

This Python script will generate a unique hosts file (and dnsmasq configuration)
based on the sources in the `data/` folder. 

You can either have the script go out and fetch an updated version over the web (defined by the
update.info text file in the source's directory), or it will use the `hosts` files which are 
already there.

Usage
    ./updateHostsFile.py

## What is dnsmasq and why configuring it?

It is a lightweight DNS server with which you could block malware hostnames from 
resolving. It is a stronger blocking method compared to `hosts` file, as it blocks
subdomains also. Read more [here](http://molotnikov.de/dnsmasq).

## What is the `hosts` file?

A hosts file, named `hosts` (with no file extension), is a plain-text file used by all operating
systems to map hostnames to IP addresses.

In most operating systems, the `hosts` file is preferential to `DNS`.  Therefore if a host name is
resolved by the `hosts` file, the request never leaves your computer.

Having a smart `hosts` file goes a long way towards blocking malware, adware, and other irritants.

For example, to nullify requests to some doubleclick.net servers, adding these lines to your hosts
file will do it:

    # block doubleClick's servers
    127.0.0.1 ad.ae.doubleclick.net
    127.0.0.1 ad.ar.doubleclick.net
    127.0.0.1 ad.at.doubleclick.net
    127.0.0.1 ad.au.doubleclick.net
    127.0.0.1 ad.be.doubleclick.net
    # etc...


## Location of your hosts file
To modify your current `hosts` file, look for it in the following places and modify it with a text
editor.

**Mac OS X, iOS, Android, Linux**: `/etc/hosts` folder.

**Windows**: `%SystemRoot%\system32\drivers\etc\hosts` folder.

## Reloading hosts file
Your operating system will cache DNS lookups. You can either reboot or run the following commands to
manually flush your DNS cache once the new hosts file is in place.

### Mac OS X
Open a Terminal and run:

`sudo dscacheutil -flushcache;sudo killall -HUP mDNSResponder`

### Windows
Open a Command Prompt:

**Windows XP**: Start -> Run -> `cmd`

**Windows Vista, 7**: Start Button -> type `cmd` -> right-click Command Prompt ->
"Run as Administrator"

**Windows 8**: Start -> Swipe Up -> All Apps -> Windows System -> right-click Command Prompt ->
"Run as Administrator"

and run:

`ipconfig /flushdns`

### Linux

Ubuntu Linux, some other Debians: 
DNS reloads hosts file automatically once you update it.

Open a Terminal and run:

`/etc/rc.d/init.d/nscd restart`

**Linux with systemd**: systemctl restart network.service

**Fedora Linux**: systemctl restart NetworkManager.service
