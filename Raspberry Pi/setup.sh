#!/bin/bash

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# This script is part of the Intervalometerator project, a time-lapse camera controller for DSLRs:
# https://github.com/greiginsydney/Intervalometerator
# https://greiginsydney.com/intvlm8r
# https://intvlm8r.com


set -e # The -e switch will cause the script to exit should any command return a non-zero value

# keep track of the last executed command
# https://intoli.com/blog/exit-on-errors-in-bash-scripts/
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting
trap 'echo "\"${last_command}\"" command failed with exit code $?.' EXIT

#Shell note for n00bs like me: in Shell scripting, 0 is success and true. Anything else is shades of false/fail.


# -----------------------------------
# START FUNCTIONS
# -----------------------------------


install_apps ()
{
	apt-get install subversion # Used later in this script to clone the RPi dir's of the Github repo
	apt-get install python-pip python-flask -y
	pip install flask flask-bootstrap flask-login gunicorn configparser
	
	#This is ALL for Paramiko (SSH uploads):
	apt-get install libffi-dev libssl-dev python-dev -y
	apt install krb5-config krb5-user -y
	apt-get install libkrb5-dev -y
	pip install bcrypt pynacl cryptography gssapi paramiko
	
	pip install dropbox
	apt-get install nginx nginx-common supervisor python-dev python-psutil -y
	apt-get install libgphoto2-dev -y
	#If the above doesn't install or throws errors, run apt-cache search libgphoto2 & it should reveal the name of the "development" version, which you should substitute back into your repeat attempt at this step.
	pip install -v gphoto2
	apt-get install libjpeg-dev -y
	pip install -v pillow --no-cache-dir
	apt-get install python-smbus i2c-tools -y
	# We don't want Bluetooth, so uninstall it:
	apt-get purge bluez -y
	apt-get autoremove -y
	apt autoremove
	apt-get clean
	# Prepare for reboot/restart:
	echo "Exited install_apps OK."
}


install_website ()
{
	# Here's where you start to build the website. This process is largely a copy/mashup of these posts.[^3] [^4] [^5]
	cd  ${HOME}
	mkdir -pv photos
	mkdir -pv preview
	mkdir -pv thumbs
	mkdir -pv www
	mkdir -pv www/static
	mkdir -pv www/templates
	# Now create a 'symbolic link' (a shortcut) to the photos, preview and thumbs folders so they appear in the path for the webserver to access them:
	ln -sfnv ${HOME}/photos  ${HOME}/www/static
	ln -sfnv ${HOME}/preview ${HOME}/www/static
	ln -sfnv ${HOME}/thumbs  ${HOME}/www/static
	chown -R pi:www-data /home/pi

	# piTransfer.py will add to this file the name of every image it successfully transfers
	touch photos/uploadedOK.txt

	[ -f intvlm8r.service ] && mv -fv intvlm8r.service /etc/systemd/system/
	systemctl start intvlm8r
	systemctl enable intvlm8r

	[ -f intvlm8r ] && mv -fv intvlm8r /etc/nginx/sites-available/
	ln -sf /etc/nginx/sites-available/intvlm8r /etc/nginx/sites-enabled

	#Step 76 goes here - edit sites-enabled/default
	if grep -qi "8080 default_server" /etc/nginx/sites-enabled/default;
	then
		echo -e "Skipped: Default server is already on port 8080"
	else
		sed -i 's/80 default_server/8080 default_server/g' /etc/nginx/sites-enabled/default # Move default from port 80 to 8080
	fi

	if grep -qi "root ~/www/templates;" /etc/nginx/sites-enabled/default;
	then
		echo -e "Skipped: 'root ~/www/templates;' exists in /etc/nginx/sites-enabled/default"
	else
		sed -i 's+root /var/www/html;+root ~/www/templates;+g' /etc/nginx/sites-enabled/default # Point to correct www path
	fi

	if grep -qi "intvlm8r.sock" /etc/nginx/sites-enabled/default;
	then
		echo -e "Skipped: location data has already been customised in /etc/nginx/sites-enabled/default"
	else
		sed -i $"/^[[:space:]]\+try_files/a include proxy_params;\nproxy_pass http://unix:${HOME}/www/intvlm8r.sock;" /etc/nginx/sites-enabled/default
	fi

	#Generate a secret key here & paste in to intvlm8r.py:
	UUID=$(cat /proc/sys/kernel/random/uuid)
	sed -i "s/### Paste the secret key here. See the Setup docs ###/$UUID/g" www/intvlm8r.py

	# Prompt the user to change the default web login from admin/password:
	chg_web_login

	#Camera Transfer
	[ -f cameraTransfer.service ] && mv cameraTransfer.service /etc/systemd/system/
	chmod 644 /etc/systemd/system/cameraTransfer.service
	systemctl enable cameraTransfer.service
	
	#Pi Transfer
	[ -f piTransfer.service ] && mv piTransfer.service /etc/systemd/system/
	chmod 644 /etc/systemd/system/piTransfer.service
	systemctl enable piTransfer.service

	#Camera Transfer - Cron Job

	#Thank you SO:
	# https://stackoverflow.com/questions/878600/how-to-create-a-cron-job-using-bash-automatically-without-the-interactive-editor
	# https://stackoverflow.com/questions/4880290/how-do-i-create-a-crontab-through-a-script
	(crontab -l -u ${SUDO_USER} 2>/dev/null > cronTemp) || true

	if grep -q cameraTransfer.py "cronTemp";
	then
		echo "Skipped: 'cameraTransfer.py' is already in the crontable. Edit later with 'crontab -e'"
	else
		echo "Cron job. If the Pi is set to always run, a scheduled 'cron job' will copy images off the camera."
		read -p "Shall we create one of those? [Y/n]: " Response
		case $Response in
			(y|Y|"")
				echo "0 * * * * /usr/bin/python ${HOME}/www/cameraTransfer.py" >> cronTemp #echo new cron into cron file
				crontab -u $SUDO_USER cronTemp #install new cron file
				sed -i 's+#cron.* /var/log/cron.log+cron.* /var/log/cron.log+g' /etc/rsyslog.conf #Un-comments the logging line
				;;
			(*)
				#Skip
				;;
		esac
	fi
	rm cronTemp

	#piTransfer
	(crontab -l -u ${SUDO_USER} 2>/dev/null > cronTemp) || true

	if grep -q piTransfer.py "cronTemp";
	then
		echo "Skipped: 'piTransfer.py' is already in the crontable. Edit later with 'crontab -e'"
	else
		echo "0 * * * * /usr/bin/python ${HOME}/www/piTransfer.py" >> cronTemp #echo new cron into cron file
		crontab -u $SUDO_USER cronTemp #install new cron file
		sed -i 's+#cron.* /var/log/cron.log+cron.* /var/log/cron.log+g' /etc/rsyslog.conf #Un-comments the logging line
	fi
	rm cronTemp

	#NTP
	read -p "NTP Step. Does the Pi have network connectivity? [Y/n]: " Response
	case $Response in
		(y|Y|"")
			sed -i 's/ setTime.service//g' /etc/systemd/system/cameraTransfer.service #Result is "After=intvlm8r.service"
			sed -i 's/ setTime.service//g' /etc/systemd/system/piTransfer.service
			
			;;
		(*)
			[ -f setTime.service ] && mv setTime.service /etc/systemd/system/setTime.service
			chmod 644 /etc/systemd/system/setTime.service
			systemctl enable setTime.service
			systemctl disable systemd-timesyncd
			systemctl stop systemd-timesyncd
			;;
	esac


	# Step 101 - slows the I2C speed
	if  grep -q "dtparam=i2c1=on" /boot/config.txt;
	then
		echo 'Skipped: "/boot/config.txt" already contains "dtparam=i2c1=on"'
	else
		sed -i "/dtparam=i2c_arm=on/i dtparam=i2c1=on" /boot/config.txt
	fi

	if  grep -q "i2c_arm_baudrate" /boot/config.txt;
	then
		echo 'Skipped: "/boot/config.txt" already contains "i2c_arm_baudrate"'
	else
		sed -i 's/dtparam=i2c_arm=on/dtparam=i2c_arm=on,i2c_arm_baudrate=40000 /'g /boot/config.txt
	fi

	# Step 102
	# https://unix.stackexchange.com/questions/77277/how-to-append-multiple-lines-to-a-file
	if  grep -Fq "intervalometerator" "/boot/config.txt";
	then
		echo 'Skipped: "/boot/config.txt" already contains our added config lines'
	else
cat <<END >> /boot/config.txt

#The intervalometerator has no need for bluetooth:
dtoverlay=pi3-disable-bt

#This kills the on-board LED (to conserve power):
dtparam=act_led_trigger=none
dtparam=act_led_activelow=on

#This sets up the ability for the Arduino to shut it down:
dtoverlay=gpio-shutdown,gpio_pin=17,active_low=1,gpio_pull=up

#Set GPIO27 to follow the running state: it's High while running and 0 when shutdown is complete. The Arduino will monitor this pin.
dtoverlay=gpio-poweroff,gpiopin=27,active_low
END
	fi
	# Prepare for reboot/restart:
	echo "Exited install_website OK."
}


chg_web_login ()
{
	# This matches the format of the  user/password dictionary, even allowing for some random spaces:
	matchRegex="^users\s*=\s*\{'(\w+)':\s*\{'password':\s*'(.?*)'}}$"

	# Read the current username:
	while read line; do
		if [[ $line =~ $matchRegex ]] ;
		then
				oldLoginName=${BASH_REMATCH[1]}
				oldPassword=${BASH_REMATCH[2]}
				break
		fi
	done <~/www/intvlm8r.py

	if [ ! -z "$oldLoginName" ];
	then
			read -e -i "$oldLoginName" -p "Change the website's login name: " loginName
			if [ ! -z "$loginName" ];
			then
					sed -i "s/^users\s*=\s*{'$oldLoginName'/users = {'$loginName'/g" ~/www/intvlm8r.py
					if [ ! -z "$oldPassword" ];
					then
						read -e -i "$oldPassword" -p "Change the website's password  : " password
						if [ ! -z "$password" ];
				then
					sed -i -E "s/^(users\s*=\s*\{'$loginName':\s*\{'password':\s*)'($oldPassword)'}}$/\1'$password'}}/" ~/www/intvlm8r.py
				else
					echo -e "Error: An empty password is invalid. Skipping"
				fi
					else
						echo -e "Error: An empty password is invalid. Please edit ~/www/intvlm8r.py to resolve"
					fi
			fi
	else
			echo "Error: Login name not found in ~/www/intvlm8r.py. Skipping."
	fi
}


# https://stackoverflow.com/questions/50413579/bash-convert-netmask-in-cidr-notation/50414560
IPprefix_by_netmask ()
{
	c=0 x=0$( printf '%o' ${1//./ } )
	while [ $x -gt 0 ]; do
		let c+=$((x%2)) 'x>>=1'
	done
	echo $c ;
}


make_ap ()
{
	apt-get install dnsmasq hostapd -y
	systemctl stop dnsmasq
	systemctl stop hostapd
	sed -i -E "s|^#?(DAEMON_CONF=\")(.*)\"|\1/etc/hostapd/hostapd.conf\"|" /etc/default/hostapd
	if  grep -Fq "interface wlan0" "/etc/dhcpcd.conf";
	then
		#Un-comment the lines if they're present but inactive:
		sed -i -E "s/^#(interface wlan0\s*)/\1/" /etc/dhcpcd.conf
		# https://unix.stackexchange.com/questions/285160/how-to-edit-next-line-after-pattern-using-sed
		sed -i -E '$!N;s/(wlan0\n)#(\s*static)/\1\2/;P;D' /etc/dhcpcd.conf # Replaces only if "static" is on the line AFTER "wlan0"
		sed -i -E "s/^#(\s*nohook wpa_supplicant.*)/\1/" /etc/dhcpcd.conf
		#Read the current value:
		oldPiIpV4=$(sed -n -E 's|^\s*static ip_address=(([0-9]{1,3}\.){3}[0-9]{1,3})/([0-9]{1,2}).*$|\1|p' /etc/dhcpcd.conf | tail -1) # Delimiter needs to be '|'
		#echo $oldPiIpV4
	else
		#Add the required lines:
		cat <<END >> /etc/dhcpcd.conf

interface wlan0
   static ip_address=10.10.10.1/24
   nohook wpa_supplicant
END
	fi
	if [ -z "$oldPiIpV4" ]; then oldPiIpV4='10.10.10.1'; fi

	if  grep -Fq "interface=wlan0" "/etc/dnsmasq.conf";
	then
		#Read the current values:
		# This matches the format of the DHCP syntax:
		matchRegex="\s*(([0-9]{1,3}\.){3}[0-9]{1,3}),(([0-9]{1,3}\.){3}[0-9]{1,3}),(([0-9]{1,3}\.){3}[0-9]{1,3})," # Bash doesn't do digits as "\d"
		while read line; do
			if [[ $line =~ $matchRegex ]] ;
			then
				oldDhcpStartIp=${BASH_REMATCH[1]}
				oldDhcpEndIp=${BASH_REMATCH[3]}
				oldDhcpSubnetMask=${BASH_REMATCH[5]}
				break
			fi
		done </etc/dnsmasq.conf
	else
		#Create default values:
		cat <<END >> /etc/dnsmasq.conf
interface=wlan0      # Use the required wireless interface - usually wlan0
	dhcp-range=10.10.10.10,10.10.10.100,255.255.255.0,24h
END
	fi
	#Populate defaults if required:
	if [ -z "$oldDhcpStartIp" ]; then oldDhcpStartIp='10.10.10.10'; fi
	if [ -z "$oldDhcpEndIp" ]; then oldDhcpEndIp='10.10.10.100'; fi
	if [ -z "$oldDhcpSubnetMask" ]; then oldDhcpSubnetMask='255.255.255.0'; fi

	#Only move the hostapd.conf file from the Repo is there isn't an existing one:
	[ -f hostapd.conf ] && mv -v hostapd.conf /etc/hostapd/hostapd.conf
	#Extract the required WiFi values:
	oldWifiSsid=$(sed -n -E 's/^\s*ssid=(.*)$/\1/p' /etc/hostapd/hostapd.conf)
	oldWifiChannel=$(sed -n -E 's/^\s*channel=(.*)$/\1/p' /etc/hostapd/hostapd.conf)
	oldWifiPwd=$(sed -n -E 's/^\s*wpa_passphrase=(.*)$/\1/p' /etc/hostapd/hostapd.conf)
	#Populate defaults if required:
	if [ -z "$oldWifiSsid" ]; then oldWifiSsid='intvlm8r'; fi
	if [ -z "$oldWifiChannel" ]; then oldWifiChannel='5'; fi
	if [ -z "$oldWifiPwd" ]; then oldWifiPwd='myPiNetw0rkAccess!'; fi

	echo ""
	echo "Set your Pi as a WiFi Access Point. (Ctrl-C to abort)"
	echo "If unsure, go with the defaults until you get to the SSID and password"
	echo ""
	read -e -i "$oldPiIpV4" -p         "Choose an IP address for the Pi        : " piIpV4
	read -e -i "$oldDhcpStartIp" -p    "Choose the starting IP address for DCHP: " dhcpStartIp
	read -e -i "$oldDhcpEndIp" -p      "Choose  the  ending IP address for DCHP: " dhcpEndIp
	read -e -i "$oldDhcpSubnetMask" -p "Set the appropriate subnet mask        : " dhcpSubnetMask
	read -e -i "$oldWifiSsid" -p       "Pick a nice SSID                       : " wifiSsid
	read -e -i "$oldWifiPwd" -p        "Choose a better password than this     : " wifiPwd
	read -e -i "$oldWifiChannel" -p    "Choose an appropriate WiFi channel     : " wifiChannel

	#TODO: Validate these inputs. Make sure none are null

	cidr_mask=$(IPprefix_by_netmask $dhcpSubnetMask)

	#Paste in the new settings
	sed -i -E "s|^(\s*static ip_address=)(.*)|\1$piIpV4/$cidr_mask|" /etc/dhcpcd.conf #Used "|" as the delimiter, as "/" is in the replacement string
	sed -i -E "s/^(\s*dhcp-range=)(.*)$/\1$dhcpStartIp,$dhcpEndIp,$dhcpSubnetMask,24h/" /etc/dnsmasq.conf
	sed -i -E "s/^(channel=)(.*)$/\1$wifiChannel/" /etc/hostapd/hostapd.conf
	sed -i -E "s/^(ssid=)(.*)$/\1$wifiSsid/" /etc/hostapd/hostapd.conf
	sed -i -E "s/^(wpa_passphrase=)(.*)$/\1$wifiPwd/" /etc/hostapd/hostapd.conf

	systemctl unmask hostapd
	systemctl enable hostapd
	echo "WARNING: After the next reboot, the Pi will come up as a WiFi access point!"
}


unmake_ap ()
{
	systemctl mask hostapd
	systemctl stop dnsmasq
	systemctl stop hostapd
	sed -i -E "s|^\s*(DAEMON_CONF=\")(.*)\"|#\1/etc/hostapd/hostapd.conf\"|" /etc/default/hostapd
	if grep -qi "interface wlan0" /etc/dhcpcd.conf;
	then
		# Comment out the wlan0 lines:
		sed -i -E "s/^(interface wlan0\s*)/#\1/" /etc/dhcpcd.conf
		# https://unix.stackexchange.com/questions/285160/how-to-edit-next-line-after-pattern-using-sed
		sed -i -E '$!N;s/(wlan0\n)(\s*static)/\1#\2/;P;D' /etc/dhcpcd.conf # Replaces only if "static" is on the line AFTER "wlan0"
		sed -i -E "s/^(\s*nohook wpa_supplicant.*)/#\1/" /etc/dhcpcd.conf
	else
		echo -e "Skipped: interface wlan0 is not specified in /etc/dhcpcd.conf"
	fi

	echo "WARNING: After the next reboot, the Pi will come up as a WiFi *client*"
	ssid=$(sed -n -E 's/^\s*ssid="(.*)"/\1/p' /etc/wpa_supplicant/wpa_supplicant.conf)
	echo -e "WARNING: It will attempt to connect to this/these SSIDs:\n$ssid"
	echo "WARNING: 'sudo nano /etc/wpa_supplicant/wpa_supplicant.conf' to change"
}


test_install ()
{
	echo "TEST!"
}


prompt_for_reboot()
{
	read -p "Reboot now? [Y/n]: " rebootResponse
	case $rebootResponse in
		(y|Y|"")
			echo "Bye!"
			exec reboot now
			;;
		(*)
			return
			;;
	esac
}


# -----------------------------------
# END FUNCTIONS
# -----------------------------------


# -----------------------------------
# THE FUN STARTS HERE
# -----------------------------------


if [ "$EUID" -ne 0 ];
then
	echo -e "\nPlease re-run as 'sudo ./AutoSetup.sh <step>'"
	exit 1
fi

case "$1" in
	("start")
		install_apps
		prompt_for_reboot
		;;
	("web")
		install_website
		prompt_for_reboot
		;;
	("login")
		chg_web_login
		;;
	("ap")
		make_ap
		prompt_for_reboot
		;;
	("noap")
		unmake_ap
		prompt_for_reboot
		;;
	("test")
		test_install
		prompt_for_reboot
		;;
	("")
		echo -e "\nNo option specified. Re-run with 'start', 'web', 'login', 'ap', 'noap' or 'test' after the script name\n"
		exit 1
		;;
	(*)
		echo -e "\nThe switch '$1' is invalid. Try again.\n"
		exit 1
		;;
esac

# Exit from the script with success (0)
exit 0
