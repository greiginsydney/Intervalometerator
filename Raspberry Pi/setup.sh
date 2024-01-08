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
trap 'echo "\"${last_command}\"" command failed with exit code $?.' ERR

#Shell note for n00bs like me: in Shell scripting, 0 is success and true. Anything else is shades of false/fail.


# -----------------------------------
# CONSTANTS
# -----------------------------------

GREEN="\033[38;5;10m"
YELLOW="\033[38;5;11m"
GREY="\033[38;5;60m"
RESET="\033[0m"

OSLIST="bookworm" # Add new OS's here, space-delimited, as they're released.

# -----------------------------------
# START FUNCTIONS
# -----------------------------------


venv_test ()
{
	echo -e ""$GREEN"Testing operating system and virtual environment"$RESET""
	THISOS=$(sed -n -E "s|^VERSION_CODENAME=(\s*.*)$|\1|p" /etc/os-release) ## Delimiter is a '|' here
	
	if [[ " $OSLIST " =~ .*\ $THISOS\ .* ]];
	then
		echo "'$THISOS' OS detected. Requires a virtual environment."
		VENV_REQUIRED=1
	else
		echo "'$THISOS' OS detected. A virtual environment is optional."
		VENV_REQUIRED=0
	fi;

	if [[ ($VENV_REQUIRED == 1) ]];
 	then
		while true;
		do
			if [[ "$VIRTUAL_ENV" != "" ]];
			then
				VENV_ACTIVE=1
				echo -e ""$GREEN"Virtual environment active."$RESET""
				break
			else
				if [[ ! $TRIED ]];
				then
					echo -e "\n"$YELLOW"Virtual environment NOT active. Attempting to activate."$RESET""
					source "venv/bin/activate"
					TRIED==1
				else
					VENV_ACTIVE=0
					break
				fi;
			fi;
		done
	fi;

	if [[ ($VENV_REQUIRED == 1) && ($VENV_ACTIVE == 0) ]];
	then
		echo -e "\n"$YELLOW"The required virtual environment could not be activated"$RESET""
		echo "Please execute the command 'source venv/bin/activate' and re-run the script."
		echo -e "If that fails, check you have correctly created the required VENV. Review \nhttps://github.com/greiginsydney/Intervalometerator/blob/bookworm/docs/step1-setup-the-Pi.md"
		echo ""
		exit
	fi
	#echo ${SUDO_USER}
	#echo $(which pip3)
}


install_apps ()
{
	if [[ -d /home/${SUDO_USER}/Intervalometerator/Raspberry\ Pi ]];
	then
		echo -e ""$GREEN"Moving repo files."$RESET""
		cp -fvr /home/${SUDO_USER}/Intervalometerator/Raspberry\ Pi/* /home/${SUDO_USER}/
		rm -fr /home/${SUDO_USER}/Intervalometerator/
	else
		echo -e "\n"$YELLOW"No repo files to move."$RESET""
	fi;

	
	if [[ -f /home/${SUDO_USER}/www/intvlm8r.py ]];
	then
		echo ''
		if [[ -f /home/${SUDO_USER}/www/intvlm8r.py.new ]];
		then
			echo 'intvlm8r.py.new & intvlm8r.py found. Looks like this is an upgrade.'
			cp -fv /home/${SUDO_USER}/www/intvlm8r.py /home/${SUDO_USER}/www/intvlm8r.old
			cp -fv /home/${SUDO_USER}/www/intvlm8r.py.new /home/${SUDO_USER}/www/intvlm8r.py

		else
			echo "intvlm8r.py found. Looks like a repeat run through the 'start' process."
		fi;
		echo ''


		if python3 -c 'import pkgutil; exit(not pkgutil.find_loader("paramiko"))';
		then
			installSftp=1
		else
			installSftp=0
		fi
		if python3 -c 'import pkgutil; exit(not pkgutil.find_loader("dropbox"))';
		then
			installDropbox=1
		else
			installDropbox=0
		fi
		# if python3 -c 'import pkgutil; exit(not pkgutil.find_loader("oauth2client"))';
		# then
		# 	installGoogle=1
		# else
		installGoogle=0
		# fi
		if python3 -c 'import pkgutil; exit(not pkgutil.find_loader("sysrsync"))';
		then
			installRsync=1
		else
			installRsync=0
		fi

		echo '====== Select Upload/Transfer options ======='
		echo "An 'X' indicates the option is already installed"
	elif [[ -f www/intvlm8r.py.new ]];
	then
		echo ''
		echo 'intvlm8r.py.new but no intvlm8r.py found. Proceeding with a new installation.'
		cp -fv www/intvlm8r.py.new www/intvlm8r.py

		#Ask the admin if they want to NOT install some of the transfer/upload options:
		echo ''
		echo '====== Select Upload/Transfer options ======='
		echo "An 'X' indicates the option will be installed"
		installSftp=1
		installDropbox=1
		installGoogle=0
		installRsync=1
	else
		echo ''
		echo "Neither intvlm8r.py.new or intvlm8r.py found. Something's amiss. Are we in the right folder?"
		echo 'Aborting.'
		echo ''
		exit 1
	fi
	while true; do
		echo ''

		echo "1. [$([[ installSftp    -eq 1 ]] && echo ''X'' || echo '' '')] SFTP"
		echo "2. [$([[ installDropbox -eq 1 ]] && echo ''X'' || echo '' '')] Dropbox"
		#echo "3. [$([[ installGoogle  -eq 1 ]] && echo ''X'' || echo '' '')] Google Drive"
		echo "4. [$([[ installRsync   -eq 1 ]] && echo ''X'' || echo '' '')] rsync"
		echo ''
		#echo 'Press 1, 2, 3 or 4 to toggle the selection.'
		echo 'Press 1, 2 or 4 to toggle the selection.'
		read -p 'Press return on its own to continue with the install ' response
		case "$response" in
			(1)
				installSftp=$((1-installSftp))
				;;
			(2)
				installDropbox=$((1-installDropbox))
				;;
			#(3)
			#	installGoogle=$((1-installGoogle))
			#	;;
			(4)
				installRsync=$((1-installRsync))
				;;
			("")
				break
				;;
		esac
	done

	echo -e ""$GREEN"Installing python3-pip"$RESET""
	apt-get install python3-pip -y
	echo -e ""$GREEN"Upgrading pip3"$RESET""
	pip3 install --upgrade pip
	echo -e ""$GREEN"Installing python3-flask"$RESET""
	apt-get install python3-flask -y
	echo -e ""$GREEN"Installing Werkzeug"$RESET""
	pip3 install Werkzeug
	echo -e ""$GREEN"Installing flask, flask-bootstrap, flask-login, Flask_Caching, configparser"$RESET""
	pip3 install flask flask-bootstrap flask-login Flask_Caching configparser
	echo -e ""$GREEN"Installing gunicorn, psutil, packaging"$RESET""
	pip3 install gunicorn psutil packaging
	echo -e ""$GREEN"Installing redis-server"$RESET""
	apt install redis-server -y

	# Add new 'redis' component (if >=Bookworm)
	# if [[ ($VENV_REQUIRED == 1) ]]; #I don't know which of these is the better
	if [[ ($VENV_ACTIVE == 1) ]];
	then
 	 	echo -e ""$GREEN"Installing redis"$RESET""	
  		pip3 install redis
    	fi
     
	echo -e ""$GREEN"Installing celery[redis]"$RESET""
	pip3 install "celery[redis]"

	if [ $installSftp -eq 1 ];
	then
		#This is ALL for Paramiko (SSH uploads):
		export DEBIAN_FRONTEND=noninteractive
		echo -e ""$GREEN"Installing libffi-dev, libssl-dev"$RESET""
		apt-get install libffi-dev libssl-dev -y
  		echo -e ""$GREEN"Installing krb5-config, krb5-user"$RESET""
		apt install krb5-config krb5-user -y
		echo -e ""$GREEN"Installing libkrb5-dev"$RESET""
		apt-get install libkrb5-dev -y
		echo -e ""$GREEN"Installing bcrypt"$RESET""
		# pip3 install -U "bcrypt<4.0.0" See issue #129
		pip3 install -U bcrypt
		echo -e ""$GREEN"Installing pynacl, cryptography, gssapi, paramiko"$RESET""
		pip3 install pynacl cryptography gssapi paramiko
	fi

	if [ $installDropbox -eq 1 ];
	then
		echo -e ""$GREEN"Installing dropbox"$RESET""
		pip3 install dropbox
	fi

	if [ $installGoogle -eq 1 ];
	then
		echo -e ""$GREEN"Installing google-api-python-client, oauth2client"$RESET""
		pip3 install -U pip google-api-python-client oauth2client
	fi

	if [ $installRsync -eq 1 ];
	then
		echo -e ""$GREEN"Installing sysrsync"$RESET""
		pip3 install sysrsync
	fi

	echo -e ""$GREEN"Installing nginx, nginx-common, supervisor, python-dev-is-python3, jq"$RESET""
	apt-get install nginx nginx-common supervisor python-dev-is-python3 jq -y

	# ================== START libgphoto ==================
	if ( apt list --manual-installed | grep -q libgphoto );
	then
		# Installed via apt = legacy. Uninstall
		echo -e ""$YELLOW"Legacy libgphoto2 install detected. Purging"$RESET""
		apt purge libexif12 libgphoto2-6 libgphoto2-port12 libltdl7 libgphoto2-dev -y
	else
		echo -e ""$GREEN"Legacy libgphoto2 install not found"$RESET""
	fi

	installLibgphoto2=0
	echo -e ""$GREEN"Checking for installed and latest release versions of libgphoto2"$RESET""
	latestLibgphoto2Rls=$(curl --silent "https://api.github.com/repos/gphoto/libgphoto2/releases/latest" | grep '"tag_name":' | sed -E 's/.*"v([^"]+)".*/\1/')
	echo "Current     online version of libgphoto2 = $latestLibgphoto2Rls"
	echo -n "Checking installed version of libgphoto2 "
	set +e #Suspend the error trap
	isLibgphoto2=$(pkg-config --modversion --silence-errors libgphoto2)
	set -e #Resume the error trap

	if [[ $isLibgphoto2 ]]; then
		echo -e "\rCurrent  installed version of libgphoto2 = $isLibgphoto2"
		if dpkg --compare-versions $isLibgphoto2 "lt" $latestLibgphoto2Rls ;
		then
			echo ''
			echo -e ""$GREEN"Updating libgphoto2"$RESET""
			installLibgphoto2=1
		else
			echo 'No libgphoto2 upgrade required'
		fi
	else
		echo -e "\rCurrent  installed version of libgphoto2 = None"
		echo ''
		echo -e ""$GREEN"Installing libgphoto2"$RESET""
		installLibgphoto2=1
	fi

	if [ $installLibgphoto2 -eq 1 ];
	then
		echo -e ""$GREEN"Installing libgphoto2 pre-req's"$RESET""
		apt-get install python3-pip build-essential libltdl-dev libusb-1.0-0-dev libexif-dev libpopt-dev libudev-dev pkg-config git automake autoconf autopoint gettext libtool wget -y

		echo -e ""$GREEN"Installing libgphoto2 from GitHub"$RESET""
  		rm -rf /home/${SUDO_USER}/libgphoto2
		git clone https://github.com/gphoto/libgphoto2.git
		cd /home/${SUDO_USER}/libgphoto2
		autoreconf --install --symlink
		./configure
		make
		make install
		ldconfig

  		cd /home/${SUDO_USER}/

		echo -e ""$GREEN"Generate udev rules for the camera"$RESET""
		# TY: https://maskaravivek.medium.com/how-to-control-and-capture-images-from-dslr-using-raspberry-pi-cfc0cf2d5e85
		/usr/local/lib/libgphoto2/print-camera-list udev-rules version 201 group plugdev mode 0660 | sudo tee /etc/udev/rules.d/90-libgphoto2.rules
	fi
	# =====================  END  libgphoto =========================
	# ===================== START python-gphoto =====================
	echo -e ""$GREEN"Checking for installed and latest release versions of python-gphoto2"$RESET""
	latestPythonGphotoRls=$(curl --silent "https://pypi.org/pypi/gphoto2/json" | jq  -r '.info.version ')
	echo "Current    online version of python-gphoto2 = $latestPythonGphotoRls"

	echo -n "Checking installed version of python-gphoto2"
	#isGphoto=$(su - $SUDO_USER -c "pip3 show gphoto2 2>/dev/null" | sed -n 's/.*Version:\s\(.*\).*/\1/p')
	isGphoto=$(pip3 show gphoto2 2>/dev/null | sed -n 's/.*Version:\s\(.*\).*/\1/p')
		if [[ $isGphoto && ($isGphoto != "(none)") ]]; then
		if [[ $isGphoto != $latestPythonGphotoRls ]]; then
			echo -e "\rCurrent installed version of python-gphoto2 = $isGphoto"
			echo -e ""$GREEN"Updating python-gphoto2"$RESET""
			pip3 install -v -U --force-reinstall gphoto2 --no-binary :all:
		else
			echo -e "\rCurrent installed version of python-gphoto2 = $isGphoto"
			echo 'No python-gphoto2 upgrade required'
		fi
	else
		echo -e "\rCurrent installed version of python-gphoto2 = None"
		echo -e "\r"$GREEN"Installing python-gphoto2"$RESET""
		pip3 install -v gphoto2 --no-binary :all:
	fi
	# ================== END python-gphoto ==================
	# ================ START image handling =================
	echo -e ""$GREEN"Installing libjpeg-dev, libopenjp2-7"$RESET""
	apt-get install libjpeg-dev libopenjp2-7 -y
	echo -e ""$GREEN"Installing pillow"$RESET""
	pip3 install -v pillow --no-cache-dir
	echo -e ""$GREEN"Installing ExifReader, requests"$RESET""
	pip3 install ExifReader requests
	echo -e ""$GREEN"Installing libraw-dev"$RESET""
	apt install libraw-dev -y
	echo -e ""$GREEN"Installing cython imageio"$RESET""
	pip3 install cython imageio
	# =================== END image handling ===================
	# ====================== START rawpy =======================
	installRawpy=0
	echo -e ""$GREEN"Checking for installed and latest release versions of rawpy"$RESET""
	latestRawpyRls=$(curl --silent "https://api.github.com/repos/letmaik/rawpy/releases/latest" | grep '"tag_name":' | sed -E 's/.*"v([^"]+)".*/\1/')
	echo "Current    online version of rawpy = $latestRawpyRls"
	isRawpy=$(su - $SUDO_USER -c "pip3 show rawpy 2>/dev/null" | sed -n 's/.*Version:\s\(.*\).*/\1/p')
	if [[ $isRawpy && ($isRawpy != "(none)") ]]; then
		echo -e "\rCurrent installed version of rawpy = $isRawpy"
		if [[ $isRawpy != $latestRawpyRls ]]; then
			echo -e ""$GREEN"Updating rawpy"$RESET""
			installRawpy=1
		else
			echo 'No rawpy upgrade required'
		fi
	else
		echo -e "\rCurrent installed version of rawpy = None"
		echo -e ""$GREEN"Installing rawpy"$RESET""
		installRawpy=1
	fi

	if [ $installRawpy -eq 1 ];
	then
		# echo -e ""$GREEN"Installing rawpy from GitHub"$RESET""
		# pip install "git+https://github.com/letmaik/rawpy.git@v$latestRawpyRls"
  		# Force rawpy to NOT attempt to install: it's only going to fail
  		echo -e "\n"$YELLOW"Skipping rawpy installation/upgrade. Thumbnails will not work if rawpy isn't present"$RESET""
	fi
	# ======================== END rawpy ========================

	echo -e ""$GREEN"Installing rsyslog"$RESET""
	apt install rsyslog -y
	echo -e ""$GREEN"Installing smbus2"$RESET""
	pip3 install smbus2
	echo -e ""$GREEN"Installing i2c-tools"$RESET""
	apt-get install i2c-tools -y
	# We don't want Bluetooth, so uninstall it:
	echo -e ""$GREEN"Purging bluez"$RESET""
	apt-get purge bluez -y
	echo -e ""$GREEN"Autoremoving"$RESET""
	apt-get autoremove -y
	apt autoremove
	apt-get clean

	# -------------------------------------------------------------------------------------------------
	# Thank you: http://www.uugear.com/portfolio/a-single-script-to-setup-i2c-on-your-raspberry-pi/
	echo -e ""$GREEN"Enabling i2c"$RESET""
	if grep -q 'i2c-bcm2708' /etc/modules; then
		echo 'i2c-bcm2708 module already exists'
	else
		echo 'adding i2c-bcm2708 to /etc/modules/'
		echo 'i2c-bcm2708' >> /etc/modules
	fi
	if grep -q 'i2c-dev' /etc/modules; then
		echo 'i2c-dev module already exists'
	else
		echo 'adding i2c-dev to /etc/modules/'
		echo 'i2c-dev' >> /etc/modules
	fi
	if grep -q 'dtparam=i2c1=on' /boot/config.txt; then
		echo 'i2c1 parameter already set'
	else
		echo 'setting dtparam=i2c1=on in /boot/config.txt'
		echo 'dtparam=i2c1=on' >> /boot/config.txt
	fi
	if grep -q 'dtparam=i2c_arm=on' /boot/config.txt; then
		echo 'i2c_arm parameter already set'
	else
		echo 'setting dtparam=i2c_arm=on in /boot/config.txt'
		echo 'dtparam=i2c_arm=on' >> /boot/config.txt
	fi
	if [ -f /etc/modprobe.d/raspi-blacklist.conf ]; then
		echo 'removing i2c from /etc/modprobe.d/raspi-blacklist.conf'
		sed -i 's/^blacklist spi-bcm2708/#blacklist spi-bcm2708/' /etc/modprobe.d/raspi-blacklist.conf
		sed -i 's/^blacklist i2c-bcm2708/#blacklist i2c-bcm2708/' /etc/modprobe.d/raspi-blacklist.conf
	else
		echo '/etc/modprobe.d/raspi-blacklist.conf does not exist - nothing to do.'
	fi
	# -------------------------------------------------------------------------------------------------
	echo -e ""$GREEN"Creating gphoto2 shortcuts"$RESET""
	whereisgphoto=$("pip3 show gphoto2" | sed -n 's/.*Location:\s\(.*\).*/\1/p')
	if [ ! -z "$whereisgphoto" ]; then
		gphoto2="$whereisgphoto/gphoto2"
		examples="$gphoto2/examples"
		if [ -d  $gphoto2 ]; then
			ln -sfnv "$gphoto2" /home/${SUDO_USER}/gphoto2
			echo -e "Created shortcut 'gphoto2' to point to '$gphoto2'"
		else
			echo -e "\n"$YELLOW"Unable to find installed gphoto2 to create shortcut"$RESET""
		fi
		if [ -d  $examples ]; then
			ln -sfnv "$examples" /home/${SUDO_USER}/examples
			echo -e "Created shortcut 'examples' to point to '$examples'"
		else
			echo -e "\n"$YELLOW"Unable to find installed gphoto2/examples to create shortcut"$RESET""
		fi
	else
		echo -e "\n"$YELLOW"Unable to find installed gphoto2 to create shortcuts"$RESET""
	fi

	# And a shortcut for the logs folder:
	ln -sfnv /var/log/ /home/${SUDO_USER}/log
 
	# Prepare for reboot/restart:
	echo -e "\n"$GREEN"Exited install_apps OK"$RESET""
}


pip3-install ()
{
	DISPLAY_TEXT=""
	matchRegex="^[a-zA-Z]+"

	echo "$1"
	for ARG in $1;
	do
		echo "|$ARG|"
		if [[ $ARG =~ $matchRegex ]] ;
		then
			# Only capture neat 'words' for the display text. (Strip all operators that don't start with a letter).
			DISPLAY_TEXT+=" ${ARG}"
		fi
	done
	echo -e ""$GREEN"Installing$DISPLAY_TEXT"$RESET""
	exit
	${WHICH_PIP3} "install $1"
}


install_website ()
{
	# Check for the '-E' switch:
	if env | grep -q 'HOME=/root';
	then
		echo -e "\nPlease re-run as 'sudo -E ./setup.sh web'"
		echo ''
		exit 1
	else
		echo -e ""$GREEN"Environment passed with '-E' switch"$RESET""
	fi

	declare -a ServiceFiles=("celery" "celery.service" "intvlm8r" "intvlm8r.service" "cameraTransfer.service" "setTime.service" "piTransfer.service" "heartbeat.service" "apt-daily.timer" "apt-daily.service" "myIp.service")
 	declare -a VenvFiles=("cameraTransfer.service" "setTime.service" "piTransfer.service" "heartbeat.service" ) # These? "apt-daily.timer" "apt-daily.service" "myIp.service" "celery.service" 

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

	# piTransfer.py will add to this file the name of every image it successfully transfers
	if [ ! -f photos/uploadedOK.txt ];
	then
		echo "/home/$SUDO_USER/photos/default_image.JPG" > photos/uploadedOK.txt #So we don't try to upload the default_image
	fi
	touch ${HOME}/setTime.log # Created here so it has correct ownership
	touch ${HOME}/hbresults.txt

	if [ -f default_image.JPG ];
	then
		mv -nv default_image.JPG ~/photos/default_image.JPG
	fi

	if [ -f default_image-thumb.JPG ];
	then
		mv -nv default_image-thumb.JPG ~/thumbs/default_image-thumb.JPG
	fi

	if [ -f piThumbsInfo.txt ];
	then
		mv -nv piThumbsInfo.txt ~/thumbs/piThumbsInfo.txt # -n = "do not overwrite"
	fi

	if [ -f piTransfer.log ];
	then
		mv -nv piTransfer.log ~/www/static/piTransfer.log # -n = "do not overwrite"
	fi

	chown -R $SUDO_USER:www-data ${HOME}

	if [ -f www/intvlm8r.old ];
	then
		echo -e ""$GREEN"intvlm8r.old found. Skipping the login prompt step."$RESET""
		echo "(You can edit the logins directly in /www/intvlm8r.py, or run 'sudo -E ./setup.sh login' to change the first one)"

		firstLogin=$(sed -n -E "s|^(users\s*=.*)$|\1|p" www/intvlm8r.old | tail -1) # Delimiter is a '|' here
		if [ ! -z "$firstLogin" ];
		then
			sed -i -E "s|^(users = .*)|$firstLogin|g" www/intvlm8r.py
			echo -e ""$GREEN"intvlm8r.old found. Restored first login."$RESET""
		else
			echo 'Upgrade file found but the first login was not found/detected.'
		fi

		if grep -q '^users.update' ~/www/intvlm8r.old;
		then
			#There are additional users we need to reinstate.
			matchRegex="^(users.update\(\{')(\w+)'.*$"
			# Read each extra user in turn and reinstate them in the file - if they're not present already:
			while read line; do
				if [[ $line =~ $matchRegex ]] ;
				then
					if grep -q "^${BASH_REMATCH[1]}${BASH_REMATCH[2]}'" ~/www/intvlm8r.py;
					then
						echo "Skipped: user '${BASH_REMATCH[2]}' already exists"
					else
						sed -i "/^users\s*=.*/a $line" ~/www/intvlm8r.py
						echo "Reinstated user '${BASH_REMATCH[2]}'"
					fi
				fi
			done <~/www/intvlm8r.old
		fi

    		if grep -q "### Paste the secret key here. See the Setup docs ###" www/intvlm8r.old;
		then
			echo 'intvlm8r.old found but the Secret Key has not been set.' #Skip the extraction.
		else
			oldSecretKey=$(sed -n -E "s|^\s*app.secret_key = b'(.*)'.*$|\1|p" www/intvlm8r.old | tail -1) # Delimiter is a '|' here
			if [ ! -z "$oldSecretKey" ];
			then
				echo 'intvlm8r.old found and the original Secret Key has been extracted.'
			else
				echo 'intvlm8r.old found but unable to detect the original Secret Key.'
			fi
		fi
	else
		# Prompt the user to change the default web login from admin/password:
		chg_web_login
	fi

	if grep -q '### Paste the secret key here. See the Setup docs ###' www/intvlm8r.py;
	then
		if [ ! -z "$oldSecretKey" ];
		then
			sed -i "s/### Paste the secret key here. See the Setup docs ###/$oldSecretKey/g" www/intvlm8r.py
			echo 'intvlm8r.old found and the original Secret Key has been restored.'
		else
			#Generate a secret key here & paste in to intvlm8r.py:
			UUID=$(cat /proc/sys/kernel/random/uuid)
			sed -i "s/### Paste the secret key here. See the Setup docs ###/$UUID/g" www/intvlm8r.py
			echo 'A new Secret Key was created.'
		fi
	else
		echo 'Skipped: a Secret Key already exists.'
	fi

	if [ $SUDO_USER != 'pi' ];
	then
		echo -e ""$GREEN"Changing user from default:"$RESET" Updated hard-coded user references to new user $SUDO_USER"
		#ServiceFiles declaration moved to the top of 'web'. (Now also used by daemon-reload step.)
		for val in "${ServiceFiles[@]}";
		do
			if [ -f $val ];
			then
				sed -i "s|/pi/|/$SUDO_USER/|g" $val
				sed -i "s|User=pi|User=$SUDO_USER|g" $val
			fi
		done
		if [ -f celery.conf ]; 		then sed -i "s| pi | $SUDO_USER |g" celery.conf; fi
		if [ -f celery ]; 		then sed -i "s|\"pi\"|\"$SUDO_USER\"|g" celery; fi
		if [ -f intvlm8r.logrotate ]; 	then sed -i "s| pi | $SUDO_USER |g" intvlm8r.logrotate; fi
		usermod -a -G i2c $SUDO_USER #This gives the user permission to access i2c
		if [ /etc/udev/rules.d/99-com.rules ];
		then
			if grep -q 'SUBSYSTEMS=="usb", ENV{DEVTYPE}=="usb_device", GROUP="www-data", MODE="0666"' /etc/udev/rules.d/99-com.rules;
			then
				echo 'Skipped: USB allow for group www-data already exists in /etc/udev/rules.d/99-com.rules'
			else
				sed -i '1s/^/SUBSYSTEMS=="usb", ENV{DEVTYPE}=="usb_device", GROUP="www-data", MODE="0666"\n\n/' /etc/udev/rules.d/99-com.rules
				echo 'Added: USB allow for group www-data in /etc/udev/rules.d/99-com.rules'
				#udevadm control --reload # (Not needed as we're going to reboot)
				#udevadm trigger
			fi
		fi
	fi

	#If we have a new intvlm8r file, backup any existing intvlm8r (just in case this is an upgrade):
	if [ -f intvlm8r ];
	then
		if cmp -s intvlm8r /etc/nginx/sites-available/intvlm8r;
		then
			echo "Skipped: the file '/etc/nginx/sites-available/intvlm8r' already exists & the new version is unchanged"
		else
			[ -f /etc/nginx/sites-available/intvlm8r ] && mv -fv /etc/nginx/sites-available/intvlm8r /etc/nginx/sites-available/intvlm8r.old
			#Copy new intvlm8r site across:
			mv -fv intvlm8r /etc/nginx/sites-available/intvlm8r
		fi
	fi
	ln -sf /etc/nginx/sites-available/intvlm8r /etc/nginx/sites-enabled

	#Original Step 76 was here - edit sites-enabled/default - now obsolete
	rm -f /etc/nginx/sites-enabled/default

	# Suppress server details in HTML headers:
	if grep -q "^\s*server_tokens off;$" /etc/nginx/nginx.conf;
	then
		echo "Skipped: '/etc/nginx/nginx.conf' already contains 'server_tokens off'"
	else
		sed -i -E 's/^(\s*)#\s*(server_tokens off;)/\1\2/g' /etc/nginx/nginx.conf #Match on "<whitepace>#<whitepace>server_tokens off" and remove the "#"
	fi

	#intvlm8r
	if [ -f intvlm8r.service ];
	then
		if cmp -s intvlm8r.service /etc/systemd/system/intvlm8r.service;
		then
			echo "Skipped: the file '/etc/systemd/system/intvlm8r.service' already exists & the new version is unchanged"
		else
			mv -fv intvlm8r.service /etc/systemd/system/intvlm8r.service
		fi
	fi
	#systemctl start intvlm8r - TEMPORARILY COMMENTED OUT FOR TESTING, PENDING DELETION (bugs2201)
	echo -e ""$GREEN"Enabling intvlm8r"$RESET""
	systemctl enable intvlm8r

	if [ -f intvlm8r.logrotate ];
	then
		if cmp -s intvlm8r.logrotate /etc/logrotate.d/intvlm8r.logrotate;
		then
			echo "Skipped: the file '/etc/logrotate.d/intvlm8r.logrotate' already exists & the new version is unchanged"
		else
			mv -fv intvlm8r.logrotate /etc/logrotate.d/intvlm8r.logrotate
		fi
	fi
	chown root /etc/logrotate.d/intvlm8r.logrotate
	chgrp root /etc/logrotate.d/intvlm8r.logrotate

	#Camera Transfer
	if [ -f cameraTransfer.service ];
	then
		if cmp -s cameraTransfer.service /etc/systemd/system/cameraTransfer.service;
		then
			echo "Skipped: the file '/etc/systemd/system/cameraTransfer.service' already exists & the new version is unchanged"
		else
			mv -fv cameraTransfer.service /etc/systemd/system/cameraTransfer.service
		fi
	fi
	chmod 644 /etc/systemd/system/cameraTransfer.service
	echo -e ""$GREEN"Enabling cameraTransfer.service"$RESET""
	systemctl enable cameraTransfer.service

	#Pi Transfer
	if [ -f piTransfer.service ];
	then
		if cmp -s piTransfer.service /etc/systemd/system/piTransfer.service;
		then
			echo "Skipped: the file '/etc/systemd/system/piTransfer.service' already exists & the new version is unchanged"
		else
			mv -fv piTransfer.service /etc/systemd/system/piTransfer.service
		fi
	fi
	chmod 644 /etc/systemd/system/piTransfer.service
	echo -e ""$GREEN"Enabling piTransfer.service"$RESET""
	systemctl enable piTransfer.service

	#Celery
	if [ -f celery.conf ];
	then
		if cmp -s celery.conf /etc/tmpfiles.d/celery.conf;
		then
			echo "Skipped: the file '/etc/tmpfiles.d/celery.conf' already exists & the new version is unchanged"
		else
			mv -fv celery.conf /etc/tmpfiles.d/celery.conf
		fi
	fi

	if [ -f celery ];
	then
		if cmp -s celery /etc/default/celery;
		then
			echo "Skipped: the file '/etc/default/celery' already exists & the new version is unchanged"
		else
			mv -fv celery /etc/default/celery
		fi
	fi

	if [ -f celery.service ];
	then
		if cmp -s celery.service /etc/systemd/system/celery.service;
		then
			echo "Skipped: the file '/etc/systemd/system/celery.service' already exists & the new version is unchanged"
		else
			mv -fv celery.service /etc/systemd/system/celery.service
		fi
	fi
	chmod 644 /etc/systemd/system/celery.service
	echo -e ""$GREEN"Enabling celery.service"$RESET""
	systemctl enable celery.service

	#Redis
	if grep -q "^Type=notify$" /etc/systemd/system/redis.service;
	then
		echo "Skipped: '/etc/systemd/system/redis.service' already contains 'Type=notify'"
	else
		sed -i --follow-symlinks 's|^Type=.*|Type=notify|g' /etc/systemd/system/redis.service
	fi

	if grep -q "^daemonize yes$" /etc/redis/redis.conf;
	then
		echo "Skipped: '/etc/redis/redis.conf' already contains 'daemonize yes'"
	else
		sed -i 's/^\s*#*\s*daemonize .*/daemonize yes/g' /etc/redis/redis.conf #Match on "daemonize <anything>" whether commented-out or not, and replace the line.
	fi

	if grep -q "^supervised systemd$" /etc/redis/redis.conf;
	then
		echo "Skipped: '/etc/redis/redis.conf' already contains 'supervised systemd'"
	else
		sed -i 's/^#\?supervised .*/supervised systemd/g' /etc/redis/redis.conf #Match on "supervised <anything>" whether commented-out or not, and replace the line.
	fi

	#Redis is just a *little* too chatty by default:
	if grep -q "^loglevel warning$" /etc/redis/redis.conf;
	then
		echo "Skipped: '/etc/redis/redis.conf' already contains 'loglevel warning'"
	else
		sed -i 's/^\s*#*\s*loglevel .*/loglevel warning/g' /etc/redis/redis.conf #Match on "loglevel <anything>" whether commented-out or not, and replace the line.
	fi

	#Heartbeat
	if [ -f heartbeat.service ];
	then
		if cmp -s heartbeat.service /etc/systemd/system/heartbeat.service;
		then
			echo "Skipped: the file '/etc/systemd/system/heartbeat.service' already exists & the new version is unchanged"
		else
			mv -fv heartbeat.service /etc/systemd/system/heartbeat.service
		fi
	fi
	chmod 644 /etc/systemd/system/heartbeat.service
	echo -e ""$GREEN"Enabling heartbeat.service"$RESET""
	systemctl enable heartbeat.service

	if [ -f heartbeat.timer ];
	then
		if cmp -s heartbeat.timer /etc/systemd/system/heartbeat.timer;
		then
			echo "Skipped: the file '/etc/systemd/system/heartbeat.timer' already exists & the new version is unchanged"
		else
			mv -fv heartbeat.timer /etc/systemd/system/heartbeat.timer
		fi
	fi
	chmod 644 /etc/systemd/system/heartbeat.timer
	echo -e ""$GREEN"Enabling heartbeat.timer"$RESET""
	systemctl enable heartbeat.timer


	if [ -f myIp.sh ];
	then
		chmod +x myIp.sh
	fi
	if [ -f myIp.service ];
	then
		if cmp -s myIp.service /etc/systemd/system/myIp.service;
		then
			echo "Skipped: the file '/etc/systemd/system/myIp.service' already exists & the new version is unchanged"
		else
			mv -fv myIp.service /etc/systemd/system/myIp.service
		fi
	fi
	chmod 644 /etc/systemd/system/myIp.service
	echo -e ""$GREEN"Enabling myIp.service"$RESET""
	systemctl enable myIp.service


	#Camera Transfer - Cron Job

	#Thank you SO:
	# https://stackoverflow.com/questions/878600/how-to-create-a-cron-job-using-bash-automatically-without-the-interactive-editor
	# https://stackoverflow.com/questions/4880290/how-do-i-create-a-crontab-through-a-script
	(crontab -l -u ${SUDO_USER} 2>/dev/null > cronTemp) || true

	if grep -q cameraTransfer.py 'cronTemp';
	then
		echo "Skipped: 'cameraTransfer.py' is already in the crontable. Edit later with 'crontab -e'"
	else
		echo "0 * * * * /usr/bin/python3 ${HOME}/www/cameraTransfer.py 2>&1 | logger -t cameraTransfer" >> cronTemp #echo new cron into cron file
		crontab -u $SUDO_USER cronTemp #install new cron file
		echo "Success: 'cameraTransfer.py' added to the crontable. Edit later with 'crontab -e'"
	fi
	rm cronTemp

	#piTransfer
	(crontab -l -u ${SUDO_USER} 2>/dev/null > cronTemp) || true

	if grep -q piTransfer.py 'cronTemp';
	then
		echo "Skipped: 'piTransfer.py' is already in the crontable. Edit later with 'crontab -e'"
	else
		echo "0 * * * * /usr/bin/python3 ${HOME}/www/piTransfer.py 2>&1 | logger -t piTransfer" >> cronTemp #echo new cron into cron file
		crontab -u $SUDO_USER cronTemp #install new cron file
		echo "Success: 'piTransfer.py' added to the crontable. Edit later with 'crontab -e'"
	fi
	rm cronTemp

	#overnight time sync. Takes place at 0330 to catch any change to/from Daylight Saving Time
	(crontab -l -u ${SUDO_USER} 2>/dev/null > cronTemp) || true

	if grep -F -q "30 3 * * * /usr/bin/python3 ${HOME}/www/setTime.py" "cronTemp";
	then
	    echo "Skipped: 'setTime.py' is already in the crontable. Edit later with 'crontab -e'"
	else
	    sed -i '/setTime.py/d' cronTemp #delete any previous reference to setTime.
 	    echo "30 3 * * * /usr/bin/python3 ${HOME}/www/setTime.py 2>&1 | logger -t setTime" >> cronTemp #echo new cron into cron file
	    crontab -u $SUDO_USER cronTemp #install new cron file
	    echo "Success: 'setTime.py' added to the crontable. Edit later with 'crontab -e'"
	fi
	rm cronTemp

	sed -i 's+#cron.* /var/log/cron.log+cron.* /var/log/cron.log+g' /etc/rsyslog.conf #Un-comments the logging line

	setcap CAP_SYS_TIME+ep /bin/date #Allows the Pi user (actually ALL users) to issue date without needing to be root.
	# (Thank you SO: https://unix.stackexchange.com/a/78309)

	#NTP
	if [ -f www/intvlm8r.old ];
	then
		echo -e ""$GREEN"intvlm8r.old found. Skipping the NTP prompt step."$RESET""
	else
		timeTest
		timeSync1
	fi
	if [ -f setTime.service ];
	then
		if cmp -s setTime.service /etc/systemd/system/setTime.service;
		then
			echo "Skipped: the file '/etc/systemd/system/setTime.service' already exists & the new version is unchanged"
		else
			mv -fv setTime.service /etc/systemd/system/setTime.service
		fi
	fi
	timeSync2

	#Disable the daily auto-update process.
	#https://askubuntu.com/questions/1037285/starting-daily-apt-upgrade-and-clean-activities-stopping-mysql-service
	echo ''
	apt-get remove unattended-upgrades -y

	echo ''
	if [[ $(systemctl status apt-daily.timer | grep -Fq "could not be found") ]];
	then
		echo "apt-daily.timer could not be found"
	else
		if ( systemctl is-enabled apt-daily.timer >/dev/null 2>&1 );
		then
			systemctl stop apt-daily.timer
			systemctl disable apt-daily.timer
			systemctl mask apt-daily.timer
			echo -e ""$GREEN"Stopped and disabled apt-daily.timer"$RESET""
		else
			echo 'apt-daily.timer   already stopped and disabled'
		fi
	fi

	if [[ $(systemctl status apt-daily.service | grep -Fq "could not be found") ]];
	then
		echo "apt-daily.service could not be found"
	else
		if ( systemctl is-enabled apt-daily.service >/dev/null 2>&1 );
		then
			echo 'apt-daily.service already disabled'
		else
			systemctl mask apt-daily.service
			echo -e ""$GREEN"Stopped and disabled apt-daily.service"$RESET""
		fi
	fi

	echo ''
	# Block GVFS if found. (So far only found on desktop installs of the o/s - and one reason why I'm not supporting the desktop)
	# References:
	# https://www.reddit.com/r/linuxquestions/comments/gfi31i/can_gvfs_be_disabled_and_removed/
	# https://github.com/gphoto/gphoto2/issues/181
	if [ -f /usr/lib/gvfs/gvfs-gphoto2-volume-monitor ];
	then
		chmod -v -x /usr/lib/gvfs/gvfs-gphoto2-volume-monitor
	fi
	if [ -f /usr/lib/gvfs/gvfsd-gphoto2 ];
	then
		chmod -v -x /usr/lib/gvfs/gvfsd-gphoto2
		echo ''
	fi

	# Update all service files to use the new path if 'venv'. (Added with bookworm support in early 2024)
	#if [[ ($VENV_REQUIRED == 1) ]];
	if [[ ($VENV_ACTIVE == 1) ]];
	then
		for val in "${VenvFiles[@]}";
		do
			val="/etc/systemd/system/$val"
			#echo $val
			sed -i -E "s|^(\s*ExecStart\s*=\s*)(sudo\s*)?(/usr/bin/python3)|\1\2/home/$SUDO_USER/venv/bin/python3|g" $val
		done
  		sed -i -E "s|^(\s*ExecStart\s*=\s*)(/usr/local/bin/gunicorn)|\1/home/$SUDO_USER/venv/bin/gunicorn|g" /etc/systemd/system/intvlm8r.service 
		sed -i -E "s|^(\s*CELERY_BIN\s*=\s*)(\"/usr/local/bin/celery\")|\1\"/home/$SUDO_USER/venv/bin/celery\"|g" /etc/default/celery
  		sed -i -E --follow-symlinks "s|^(\s*ExecStartPost\s*=\s*)(.*)(sleep)(.*)$|\1\n# \2\3\4|g" /etc/systemd/system/redis.service		# Comment-out the ExecStartPost 'sleep' command. (Legacy installs only: we added it initially)
    		# nginx:
      		sed -i -E "s|^(\s*user www-data)(.*)$|# \1\2|g" /etc/nginx/nginx.conf	# Comment-out existing www-data user
      		if  grep -q 'user pi;' /etc/nginx/nginx.conf
		then
			echo "Skipped: '/etc/nginx/nginx.conf' already contains 'user pi;'"
		else
			sed -i "1i user pi;" /etc/nginx/nginx.conf
		fi
	fi

	# Check and reload services if required:
	# TY Alexander Tolkachev & Sergi Mayordomo, https://serverfault.com/questions/855042/how-do-i-know-if-systemctl-daemon-reload-needs-to-be-run
	for val in "${ServiceFiles[@]}";
	do
		systemctl status $val 2>&1 | grep -q "changed on disk" && echo -e "\n"$GREEN"Executing daemon-reload"$RESET"" && systemctl daemon-reload && break;
	done

	# Step 101 - slows the I2C speed
	if  grep -q 'dtparam=i2c1=on' /boot/config.txt;
	then
		echo "Skipped: '/boot/config.txt' already contains 'dtparam=i2c1=on'"
	else
		sed -i '/dtparam=i2c_arm=on/i dtparam=i2c1=on' /boot/config.txt
	fi

	if  grep -q 'i2c_arm_baudrate' /boot/config.txt;
	then
		echo "Skipped: '/boot/config.txt' already contains 'i2c_arm_baudrate'"
	else
		sed -i 's/dtparam=i2c_arm=on/dtparam=i2c_arm=on,i2c_arm_baudrate=40000/g' /boot/config.txt
	fi
	sed -i 's/^#dtparam=i2c_arm=on,i2c_arm_baudrate=40000/dtparam=i2c_arm=on,i2c_arm_baudrate=40000/g' /boot/config.txt #Un-comments the speed line

	# Step 102
	# https://unix.stackexchange.com/questions/77277/how-to-append-multiple-lines-to-a-file
	if  grep -Fq 'intervalometerator' '/boot/config.txt';
	then
		echo "Skipped: '/boot/config.txt' already contains our added config lines"
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
dtoverlay=gpio-poweroff,gpiopin=27,active_low #**LEGACY
#dtoverlay=gpio-led,gpio=27,trigger=default-on,active_low - TEMPORARILY REMOVED 20230412 PENDING MORE TESTING
END
	fi

: '
TEMPORARILY REMOVED 20230412 PENDING MORE TESTING
	if grep -q '^dtoverlay=gpio-poweroff' /boot/config.txt;
	then
		echo -e ""$YELLOW"'/boot/config.txt' contains legacy dtoverlay=gpio-poweroff. Updating.""$RESET"
		sed -i 's/^dtoverlay=gpio-poweroff,gpiopin=27,active_low/dtoverlay=gpio-led,gpio=27,trigger=default-on,active_low/g' /boot/config.txt
	else
		echo "Skipped: '/boot/config.txt' does not contain legacy 'dtoverlay=gpio-poweroff'"
	fi
'
	if [ -f www/intvlm8r.old ];
	then
		mv -fv www/intvlm8r.old www/intvlm8r.bak
	fi

	# WiFi Power Save
	# Disable WiFi power save mode:
	if iw wlan0 get power_save | grep -q 'on';
	then
		iw wlan0 set power_save off
		echo -e ""$GREEN"Disabled WiFi power save mode"$RESET""
	else
		echo -e "WiFi power save mode is already off"
	fi
	# Permanently disable WiFi power save mode:
	if grep -q '/sbin/iw dev wlan0 set power_save off' /etc/rc.local; then
		echo -e 'WiFi power save mode is already disabled in /etc/rc.local'
	else
		sed -i '/^exit 0/i \/sbin\/iw dev wlan0 set power_save off\n' /etc/rc.local
		echo -e ""$GREEN"WiFi power save mode disabled in /etc/rc.local"$RESET""
	fi

	remoteit

	if [ -f www/intvlm8r.py.new ];
	then
		rm -fv www/intvlm8r.py.new
	fi

	# Prepare for reboot/restart:
	echo 'Exited install_website OK.'
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
		matchLoginName="^\w+$"
		while true; do
			echo ''
			read -e -r -i "$oldLoginName" -p "Change the website's login name: " loginName
			if [[ ${#loginName} -lt 1 ]];
			then
				echo " The login name can't be empty/blank"
				continue
			fi
			if [[ ! $loginName =~ $matchLoginName ]];
			then
				echo 'Please use only standard word characters for the login name'
				continue
			fi
			break	# We only get to here if the login name is not blank and doesn't contain invalid characters
		done
		sed -i "s/^users\s*=\s*{'$oldLoginName'/users = {'$loginName'/g" ~/www/intvlm8r.py
		matchPassword="[\']+"
		if [[ $oldPassword == 'password' ]]; # we'll change this to a random 8-char default:
		then
			oldPassword=$(shuf -zer -n4 {a..z} | tr -d '\0' )
			oldPassword+=$(shuf -zer -n4 {0..9} | tr -d '\0')
		fi
		while true; do
			read -e -r -i "$oldPassword" -p "Change the website's password  : " password
			if [ -z "$password" ];
			then
				echo -e 'Error: An empty password is invalid.'
				echo ''
				continue
			fi
			if [[ $password =~ $matchPassword ]];
			then
				echo ''
				echo "Please try a different password. Don't use backslashes or apostrophes/single-quotes"
				echo ''
				continue
			fi
			echo ''
			set +e #Suspend the error trap
			escapedPassword=$(echo "$password" | sed 's/[]<>[\\\/.&""|$(){}?+*^]/\\&/g')
			sed -i -E "s/^(users\s*=\s*\{'$loginName':\s*\{'password':)\s*'.*'}}$/\1 '$escapedPassword'}}/" ~/www/intvlm8r.py
			if [[ "$?" -ne 0 ]];
			then
				echo 'Whoops - something broke. Please try again with a less complex password'
				echo ''
				continue
			fi
			set -e #Resume the error trap
			break
		done
	else
		echo 'Error: Login name not found. Please edit ~/www/intvlm8r.py to resolve.'
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


# https://stackoverflow.com/questions/20762575/explanation-of-convertor-of-cidr-to-netmask-in-linux-shell-netmask2cdir-and-cdir
CIDRtoNetmask ()
{
	# Number of args to shift, 255..255, first non-255 byte, zeroes
	set -- $(( 5 - ($1 / 8) )) 255 255 255 255 $(( (255 << (8 - ($1 % 8))) & 255 )) 0 0 0
	[ $1 -gt 1 ] && shift $1 || shift
	echo ${1-0}.${2-0}.${3-0}.${4-0}
}


make_ap ()
{
	apt-get install dnsmasq hostapd -y
	systemctl stop dnsmasq
	systemctl stop hostapd
	sed -i -E "s|^\s*#*\s*(DAEMON_CONF=\")(.*)\"|\1/etc/hostapd/hostapd.conf\"|" /etc/default/hostapd
	sed -i -E '/^#[^# ].*/d' /etc/dhcpcd.conf #Trim all default commented-out config lines: Match "<SINGLE-HASH><value>"
	if  grep -Fq 'interface wlan0' '/etc/dhcpcd.conf';
	then
		wlanLine=$(sed -n '/interface wlan0/=' /etc/dhcpcd.conf) #This is the line number that the wlan config starts at
		sed -i -E "s/^\s*#*\s*(interface wlan0.*)/\1/" /etc/dhcpcd.conf #Un-comment if present but inactive
		# The following lines all search the file for lines AFTER the appearance of "interface wlan0"
		sed -i -E "$wlanLine,$ s/^\s*#*\s*(static\s*ip_address=)(.*)/\  \1\2/" /etc/dhcpcd.conf
		sed -i -E "$wlanLine,$ s/^\s*#*\s*(static routers.*)/##  \1/" /etc/dhcpcd.conf  # DOUBLE-Comment-out "routers"
		sed -i -E "$wlanLine,$ s/^\s*#*\s*(static domain_name_servers.*)/##  \1/" /etc/dhcpcd.conf  # DOUBLE-Comment-out "domain_name_servers"
		#Look anywhere in the file for this one. Its position is not critical (although it's probably at the end anyway).
		sed -i -E "s/^\s*#*\s*(nohook wpa_supplicant.*)$/\  \1/" /etc/dhcpcd.conf  #Un-comment "nohook wpa_supplicant"
		#Read the current value:
		oldPiIpV4=$(sed -n -E 's|^\s*static ip_address=(([0-9]{1,3}\.){3}[0-9]{1,3})/([0-9]{1,2}).*$|\1|p' /etc/dhcpcd.conf | tail -1) # Delimiter needs to be '|'
		#echo $oldPiIpV4
	else
		#Add the required lines:
		cat <<END >> /etc/dhcpcd.conf

interface wlan0
   static ip_address=10.10.10.1/24
   ## static routers=192.168.0.1
   ## static domain_name_servers=192.168.0.1
   nohook wpa_supplicant
END
	fi
	if ! grep -Fq 'nohook wpa_supplicant' '/etc/dhcpcd.conf';
	then
		sed -i -e "\$anohook wpa_supplicant" '/etc/dhcpcd.conf';
	fi
	if [ -z "$oldPiIpV4" ]; then oldPiIpV4='10.10.10.1'; fi

	if  grep -q 'interface=wlan0' /etc/dnsmasq.conf;
	then
		#Read the current values:
		wlanLine=$(sed -n '/interface=wlan0/=' /etc/dnsmasq.conf) #This is the line number that the wlan config starts at
		oldDhcpStartIp=$(sed -n -E "$wlanLine,$ s|^\s*dhcp-range=(.*)$|\1|p" /etc/dnsmasq.conf ) # Delimiter is '|'
		matchRegex="\s*(([0-9]{1,3}\.){3}[0-9]{1,3}),(([0-9]{1,3}\.){3}[0-9]{1,3}),(([0-9]{1,3}\.){3}[0-9]{1,3})," # Bash doesn't do digits as "\d"
		if [[ $oldDhcpStartIp =~ $matchRegex ]] ;
			then
				oldDhcpStartIp=${BASH_REMATCH[1]}
				oldDhcpEndIp=${BASH_REMATCH[3]}
				oldDhcpSubnetMask=${BASH_REMATCH[5]}
			fi
	else
		echo 'No IPs in /etc/dnsmasq.conf. Adding some defaults'
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

	echo ''
	echo 'Set your Pi as a WiFi Access Point. (Ctrl-C to abort)'
	echo 'If unsure, go with the defaults until you get to the SSID and password'
	echo ''
	read -e -i "$oldPiIpV4" -p         'Choose an IP address for the Pi        : ' piIpV4
	read -e -i "$oldDhcpStartIp" -p    'Choose the starting IP address for DCHP: ' dhcpStartIp
	read -e -i "$oldDhcpEndIp" -p      'Choose  the  ending IP address for DCHP: ' dhcpEndIp
	read -e -i "$oldDhcpSubnetMask" -p 'Set the appropriate subnet mask        : ' dhcpSubnetMask
	read -e -i "$oldWifiSsid" -p       'Pick a nice SSID                       : ' wifiSsid
	read -e -i "$oldWifiPwd" -p        'Choose a better password than this     : ' wifiPwd
	read -e -i "$oldWifiChannel" -p    'Choose an appropriate WiFi channel     : ' wifiChannel

	#TODO: Validate these inputs. Make sure none are null

	cidr_mask=$(IPprefix_by_netmask $dhcpSubnetMask)

	#Paste in the new settings
	sed -i -E "s|^(\s*static ip_address=)(.*)|\1$piIpV4/$cidr_mask|" /etc/dhcpcd.conf #Used "|" as the delimiter, as "/" is in the replacement string
	sed -i -E "s/^(\s*dhcp-range=)(.*)$/\1$dhcpStartIp,$dhcpEndIp,$dhcpSubnetMask,24h/" /etc/dnsmasq.conf
	sed -i -E "s/^(channel=)(.*)$/\1$wifiChannel/" /etc/hostapd/hostapd.conf
	sed -i -E "s/^(ssid=)(.*)$/\1$wifiSsid/" /etc/hostapd/hostapd.conf
	sed -i -E "s/^(wpa_passphrase=)(.*)$/\1$wifiPwd/" /etc/hostapd/hostapd.conf

	systemctl unmask hostapd
	echo 'Enabling hostapd'
	systemctl enable hostapd
	echo 'Enabling dnsmasq'
	systemctl enable dnsmasq
	echo 'WARNING: After the next reboot, the Pi will come up as a WiFi access point!'
}


unmake_ap ()
{
	if systemctl --all --type service | grep -q 'dnsmasq';
	then
		systemctl disable dnsmasq #Stops it launching on bootup
		echo 'Disabled dnsmasq'
	fi
	if systemctl --all --type service | grep -q 'hostapd';
	then
		systemctl disable hostapd
		echo 'Disabled hostapd'
		sed -i -E "s|^\s*#*\s*(DAEMON_CONF=\")(.*\")|## \1\2|" /etc/default/hostapd # DOUBLE-Comment-out
	fi
	[ -f /etc/hostapd/hostapd.conf ] && mv -fv /etc/hostapd/hostapd.conf ~/hostapd.conf

	oldCountry=$(sed -n -E 's|^\s*country=(.*)$|\1|p' /etc/wpa_supplicant/wpa_supplicant.conf | tail -1) # Delimiter needs to be '|'
	oldSsid=$(sed -n -E 's|^\s*ssid="(.*)"$|\1|p' /etc/wpa_supplicant/wpa_supplicant.conf | tail -1) # Delimiter needs to be '|'
	oldPsk=$(sed -n -E 's|^\s*psk="(.*)"$|\1|p' /etc/wpa_supplicant/wpa_supplicant.conf | tail -1) # Delimiter needs to be '|'
	while true; do
		read -e -i "$oldCountry" -p 'Set your two-letter WiFi country code : ' newCountry
		if [ -z "$newCountry" ];
		then
			echo -e 'Error: Country value cannot be empty.'
			echo ''
			continue
		fi
		break
	done
	while true; do
		read -e -i "$oldSsid"    -p "Set the network's SSID                : " newSsid
		if [ -z "$newSsid" ];
		then
			echo -e 'Error: SSID value cannot be empty.'
			echo ''
			continue
		fi
		break
	done
	while true; do
		read -e -i "$oldPsk"     -p "Set the network's Psk (password)      : " newPsk
		if [ -z "$newPsk" ];
		then
			echo -e "Error: Psk value cannot be empty."
			echo ''
			continue
		fi
		break
	done

	sed -i -E "s|^\s*country=.*|country=$newCountry|" /etc/wpa_supplicant/wpa_supplicant.conf

	set +e #Suspend the error trap
	sed -i -E "s|^(\s*ssid=).*|\1\"$newSsid\"|" /etc/wpa_supplicant/wpa_supplicant.conf
	if [[ "$?" -ne 0 ]];
	then
		echo 'Whoops - something broke setting the SSID. Please manually edit /etc/wpa_supplicant/wpa_supplicant.conf to add the required values'
		echo '(The most likely cause is that your SSID contains the quote (") or pipe (|) characters)'
		echo ''
		continue
	fi
	sed -i -E "s|^(\s*psk=).*|\1\"$newPsk\"|" /etc/wpa_supplicant/wpa_supplicant.conf
	if [[ "$?" -ne 0 ]];
	then
		echo 'Whoops - something broke setting the Psk. Please manually edit /etc/wpa_supplicant/wpa_supplicant.conf to add the required values'
		echo '(The most likely cause is that your Psk contains the quote (") or pipe (|) characters)'
		echo ''
		continue
	fi
	set -e #Resume the error trap

	sed -i -E '/^#[^# ].*/d' /etc/dhcpcd.conf #Trim all default commented-out config lines: Match "<SINGLE-HASH><value>"
	if ! grep -Fq 'interface wlan0' '/etc/dhcpcd.conf';
	then
		cat <<END >> /etc/dhcpcd.conf
interface wlan0
  static ip_address=192.168.0.10/24
  static routers=192.168.0.1
  static domain_name_servers=192.168.0.1
END
	fi
	# Just in case either of these lines are STILL missing, paste in some defaults:
	if ! grep -Fq 'static routers=' '/etc/dhcpcd.conf';
	then
		sed -i -e "\$astatic routers=192.168.0.1" '/etc/dhcpcd.conf';
	fi
	if ! grep -Fq 'static domain_name_servers=' '/etc/dhcpcd.conf';
	then
		sed -i -e "\$astatic domain_name_servers=192.168.0.1" '/etc/dhcpcd.conf';
	fi

	wlanLine=$(sed -n '/interface wlan0/=' /etc/dhcpcd.conf) #This is the line number that the wlan config starts at
	echo ""
	read -p 'Do you want to assign the Pi a static IP address? [Y/n]: ' staticResponse
	case $staticResponse in
		(y|Y|"")
			oldPiIpV4=$(sed -n -E 's|^\s*#*\s*static ip_address=(([0-9]{1,3}\.){3}[0-9]{1,3})/([0-9]{1,2}).*$|\1|p' /etc/dhcpcd.conf | tail -1) # Delimiter needs to be '|'
			oldDhcpSubnetCIDR=$(sed -n -E 's|^\s*#*\s*static ip_address=(([0-9]{1,3}\.){3}[0-9]{1,3})/([0-9]{1,2}).*$|\3|p' /etc/dhcpcd.conf | tail -1) # Delimiter needs to be '|'
			oldRouter=$(sed -n -E 's|^\s*#*\s*static routers=(([0-9]{1,3}\.){3}[0-9]{1,3}).*$|\1|p' /etc/dhcpcd.conf | tail -1) # Delimiter needs to be '|'
			oldDnsServers=$(sed -n -E 's|^\s*#*\s*static domain_name_servers=(.*)$|\1|p' /etc/dhcpcd.conf | tail -1) # Delimiter needs to be '|'
			if [ "$oldDhcpSubnetCIDR" ]; then oldDhcpSubnetMask=$(CIDRtoNetmask $oldDhcpSubnetCIDR); fi
			read -e -i "$oldPiIpV4" -p         'Choose an IP address for the Pi         : ' piIpV4
			read -e -i "$oldDhcpSubnetMask" -p 'Set the appropriate subnet mask         : ' dhcpSubnetMask
			read -e -i "$oldRouter" -p         'Set the Router IP                       : ' router
			read -e -i "$oldDnsServers" -p     'Set the DNS Server(s) (space-delimited) : ' DnsServers

			cidr_mask=$(IPprefix_by_netmask $dhcpSubnetMask)
			#Paste in the new settings
			sed -i -E "s/^#+(interface wlan0.*)/\1/" /etc/dhcpcd.conf
			sed -i -E "$wlanLine,$ s|^\s*#*\s*(static ip_address=)(.*)$|\  \1$piIpV4/$cidr_mask|" /etc/dhcpcd.conf #Used "|" as the delimiter, as "/" is in the replacement string
			sed -i -E "$wlanLine,$ s|^\s*#*\s*(static routers=)(.*)$|\  \1$router|" /etc/dhcpcd.conf #Used "|" as the delimiter, as "/" is in the replacement string
			sed -i -E "$wlanLine,$ s|^\s*#*\s*(static domain_name_servers=)(.*)$|\  \1$DnsServers|" /etc/dhcpcd.conf #Used "|" as the delimiter, as "/" is in the replacement string
			sed -i -E "s/^\s*#*\s*(nohook wpa_supplicant.*)/##  \1/" /etc/dhcpcd.conf  # DOUBLE-Comment-out "nohook wpa_supplicant", as this line prevents us trying to connect to a WiFi network
			;;
		(*)
			if grep -qi 'interface wlan0' /etc/dhcpcd.conf;
			then
				# Comment out the wlan0 lines:
				sed -i -E 's/^(interface wlan0\s*)/##\1/' /etc/dhcpcd.conf
				# https://unix.stackexchange.com/questions/285160/how-to-edit-next-line-after-pattern-using-sed
				sed -i -E "$wlanLine,$ s/^\s*(static\s*ip_address=)(.*)/##  \1\2/" /etc/dhcpcd.conf
				sed -i -E "$wlanLine,$ s/^\s*(static routers.*)/##  \1/" /etc/dhcpcd.conf  # DOUBLE-Comment-out "routers"
				sed -i -E "$wlanLine,$ s/^\s*(static domain_name_servers.*)/##  \1/" /etc/dhcpcd.conf  # DOUBLE-Comment-out "domain_name_servers"
				sed -i -E "s/^\s*#*\s*(nohook wpa_supplicant.*)/##  \1/" /etc/dhcpcd.conf  # DOUBLE-Comment-out "nohook wpa_supplicant", as this line prevents us trying to connect to a WiFi network
			else
				echo -e 'Skipped: interface wlan0 is not specified in /etc/dhcpcd.conf'
			fi
			;;
	esac

	echo 'WARNING: After the next reboot, the Pi will come up as a WiFi *client*'
	ssid=$(sed -n -E 's/^\s*ssid="(.*)"/\1/p' /etc/wpa_supplicant/wpa_supplicant.conf)
	echo -e "WARNING: It will attempt to connect to this/these SSIDs: $ssid"
	echo "WARNING: 'sudo nano /etc/wpa_supplicant/wpa_supplicant.conf' to change"
}


timeTest ()
{
	echo ''
	NTP=$(systemctl show systemd-timesyncd -p ActiveState)
	if [ $NTP = "ActiveState=active" ];
	then
		echo -e ""$GREEN"NTP is currently active. NTP is our master time source."$RESET""
	else
		echo -e ""$GREEN"NTP is not active. The Arduino is our master time source."$RESET""
	fi
}


timeSync1 ()
{
	echo ''
	echo 'Does the Pi have network connectivity?'
	read -p 'If so, can we use NTP as our master time source? [Y/n]: ' Response
	echo ''
	case $Response in
		(y|Y|"")
			echo 'Enabling systemd-timesyncd'
			systemctl enable systemd-timesyncd
			echo -e ""$GREEN"Starting systemd-timesyncd"$RESET""
			systemctl start systemd-timesyncd
			;;
		(*)
			echo 'Disabling systemd-timesyncd'
			systemctl disable systemd-timesyncd
			echo -e ""$GREEN"Stopping systemd-timesyncd"$RESET""
			systemctl stop systemd-timesyncd
			;;
	esac
}


timeSync2 ()
{
	NTP=$(systemctl show systemd-timesyncd -p ActiveState)
	if [ $NTP = 'ActiveState=active' ];
	then
		echo -e ""$GREEN"NTP is active"$RESET""
		if  grep -q 'Requires=intvlm8r.service time-sync.target' /etc/systemd/system/setTime.service;
		then
			echo " 'Requires time-sync.target' suffix is already present"
		else
			sed -i -E 's/^(Requires=intvlm8r.service)(.*)$/\1 time-sync.target/g' /etc/systemd/system/setTime.service #Add REQUIRES time-sync.target
			echo " Added 'Requires time-sync.target' suffix"
		fi
		sed -i '/Before=time-sync.target/d' /etc/systemd/system/setTime.service #Delete time-sync.target
		echo " Deleted 'Before=time-sync.target'"
	else
		echo -e ""$GREEN"NTP is not active"$RESET""
		sed -i -E 's/^(Requires=intvlm8r.service)(.*)$/\1/g' /etc/systemd/system/setTime.service ##Delete REQUIRES time-sync.target
		echo " Deleted 'Requires time-sync.target' suffix"
		if  grep -q 'Before=time-sync.target' /etc/systemd/system/setTime.service;
		then
			echo " 'Before=time-sync.target' is already present"
		else
			sed -i '/^Requires=intvlm8r.service.*/a Before=time-sync.target' /etc/systemd/system/setTime.service #Add Before
			echo " Added 'Before=time-sync.target'"
		fi
	fi
	echo ''
	chmod 644 /etc/systemd/system/setTime.service
	echo 'Enabling setTime.service'
	systemctl enable setTime.service
}


test_install ()
{
	echo 'TEST!'
	echo ''
	set +e #Suspend the error trap
	desktop=$(type Xorg 2>&1)
	set -e #Resume the error trap
	matchRegex="not found$"
	if [[ $desktop =~ $matchRegex ]];
	then
		echo -e ""$GREEN"PASS:"$RESET" OS test passed - DESKTOP operating system not installed"
	else
		echo -e ""$YELLOW"FAIL:"$RESET" Unsupported DESKTOP operating system version detected"
	fi
	echo "$(cat /etc/os-release | grep CODENAME)"
	echo ''
	[ -f /etc/nginx/sites-available/intvlm8r ] && echo -e ""$GREEN"PASS:"$RESET" /etc/nginx/sites-available/intvlm8r exists" || echo -e ""$YELLOW"FAIL:"$RESET" /etc/nginx/sites-available/intvlm8r not found"
	[ -f /etc/systemd/system/intvlm8r.service ] && echo -e ""$GREEN"PASS:"$RESET" /etc/systemd/system/intvlm8r.service exists" || echo -e ""$YELLOW"FAIL:"$RESET" /etc/systemd/system/intvlm8r.service not found"
	[ -f /etc/systemd/system/cameraTransfer.service ] && echo -e ""$GREEN"PASS:"$RESET" /etc/systemd/system/cameraTransfer.service exists" || echo -e ""$YELLOW"FAIL:"$RESET" /etc/systemd/system/cameraTransfer.service not found"
	[ -f /etc/systemd/system/piTransfer.service ] && echo -e ""$GREEN"PASS:"$RESET" /etc/systemd/system/piTransfer.service exists" || echo -e ""$YELLOW"FAIL:"$RESET" /etc/systemd/system/piTransfer.service not found"
	[ -f /etc/systemd/system/setTime.service ] && echo -e ""$GREEN"PASS:"$RESET" /etc/systemd/system/setTime.service exists" || echo -e ""$YELLOW"FAIL:"$RESET" /etc/systemd/system/setTime.service not found"
	[ -f /etc/systemd/system/redis.service ] && echo -e ""$GREEN"PASS:"$RESET" /etc/systemd/system/redis.service exists" || echo -e ""$YELLOW"FAIL:"$RESET" /etc/systemd/system/redis.service not found"
	[ -f /etc/systemd/system/celery.service ] && echo -e ""$GREEN"PASS:"$RESET" /etc/systemd/system/celery.service exists" || echo -e ""$YELLOW"FAIL:"$RESET" /etc/systemd/system/celery.service not found"
	grep -q 'i2c_arm_baudrate' /boot/config.txt && echo -e ""$GREEN"PASS:"$RESET" i2c_arm_baudrate is present in /boot/config.txt" || echo -e ""$YELLOW"FAIL:"$RESET" i2c_arm_baudrate not present in /boot/config.txt"
	if grep -qcim1 'i2c-dev' /etc/modules;
	then
		echo -e ""$GREEN"PASS:"$RESET" i2c-dev installed in /etc/modules"
		echo ''
		echo 'If the Arduino is connected & programmed it will show as "04" in the top line below:'
		set +e #Suspend the error trap
		i2cdetect -y -a 1 0x04 0x04
		if [[ "$?" -ne 0 ]];
		then
			echo -e ""$YELLOW"FAIL:"$RESET" i2cdetect threw an error"
   			echo "Did the './setup.sh start' test complete without error?"
		fi
		set -e #Resume the error trap
	else
		echo -e ""$YELLOW"FAIL:"$RESET" i2c-dev not installed in /etc/modules"
	fi
	echo ''
	# Test for ap/noap mode:
	ap_test=0
	if systemctl --all --type service | grep -q 'dnsmasq';
	then
		((ap_test=ap_test+1))
	fi
	if systemctl --all --type service | grep -q 'hostapd';
	then
		((ap_test=ap_test+2))
	fi
	[ -f /etc/hostapd/hostapd.conf ] && ap_test=$((ap_test+4))
	case $ap_test in
		(0)
			echo -e ""$GREEN"PASS:"$RESET" The Pi is a Wi-Fi client, not an Access Point"
			if [[ ($VENV_REQUIRED == 1) ]];
			then
				ssid=$(LANG=C nmcli -t -f active,ssid dev wifi | grep ^yes | cut -d: -f2-)
			else
				ssid=$(sed -n -E 's/^\s*ssid="(.*)"/\1/p' /etc/wpa_supplicant/wpa_supplicant.conf)
			fi		
			if [ -z "$ssid" ];
			then
				echo -e ""$YELLOW"FAIL:"$RESET" An SSID (network name) was expected but not found in /etc/wpa_supplicant/wpa_supplicant.conf"
			else
				echo -e ""$GREEN"PASS:"$RESET" It will attempt to connect to this/these SSIDs: $ssid"
			fi
			;;
		(1)
			echo -e ""$YELLOW"FAIL:"$RESET" dnsmasq running alone. hostapd should also be running for the Pi to be an AP"
			;;
		(2)
			echo -e ""$YELLOW"FAIL:"$RESET" hostapd running alone. dnsmasq should also be running for the Pi to be an AP"
			;;
		(3)
			echo -e ""$YELLOW"FAIL:"$RESET" hostapd & dnsmasq are installed, but hostapd.conf is missing"
			;;
		(4)
			echo -e ""$YELLOW"FAIL:"$RESET" hostapd.conf is present but hostapd & dnsmasq are missing"
			;;
		(5)
			echo -e ""$YELLOW"FAIL:"$RESET" Test returned unexpected value 5"
			;;
		(6)
			echo -e ""$YELLOW"FAIL:"$RESET" Test returned unexpected value 6"
			;;
		(7)
			echo -e ""$GREEN"PASS:"$RESET" hostapd, dnsmasq & hostapd.conf all exist. The Pi SHOULD be an AP"
   			myWifiSsid=$(sed -n -E 's/^\s*ssid=(.*)$/\1/p' /etc/hostapd/hostapd.conf)
			if [ -z "$myWifiSsid" ];
			then
				echo -e ""$YELLOW"FAIL:"$RESET" An SSID (network name) was expected but not found in /etc/hostapd/hostapd.conf"
			else
				echo -e ""$GREEN"PASS:"$RESET" Its SSID (network name) is $myWifiSsid"
			fi
			myWifiChannel=$(sed -n -E 's/^\s*channel=(.*)$/\1/p' /etc/hostapd/hostapd.conf)
			if [ -z "$myWifiChannel" ];
			then
				echo -e ""$YELLOW"FAIL:"$RESET" A Wi-Fi channel was expected but not found in /etc/hostapd/hostapd.conf"
			else
				echo -e ""$GREEN"PASS:"$RESET" It's using channel $myWifiChannel"
			fi
			;;
	esac
	#WiFiCountry=$(sed -n -E 's|^\s*country=(.*)$|\1|p' /etc/wpa_supplicant/wpa_supplicant.conf | tail -1) # Delimiter needs to be '|'
	#WiFiSsid=$(sed -n -E 's|^\s*ssid="(.*)"$|\1|p' /etc/wpa_supplicant/wpa_supplicant.conf | tail -1) # Delimiter needs to be '|'
	#WiFiPsk=$(sed -n -E 's|^\s*psk="(.*)"$|\1|p' /etc/wpa_supplicant/wpa_supplicant.conf | tail -1) # Delimiter needs to be '|'

	if iw wlan0 get power_save | grep -q 'on';
	then
		echo -e ""$YELLOW"FAIL:"$RESET" WiFi power save is ON"
	else
		echo -e ""$GREEN"PASS:"$RESET" WiFi power save is OFF"
	fi
	echo ''
	systemctl is-active --quiet nginx    && printf ""$GREEN"PASS:"$RESET" %-9s service is running\n" nginx    || printf ""$YELLOW"FAIL:"$RESET" %-9s service is dead\n" nginx
	systemctl is-active --quiet intvlm8r && printf ""$GREEN"PASS:"$RESET" %-9s service is running\n" intvlm8r || printf ""$YELLOW"FAIL:"$RESET" %-9s service is dead\n" intvlm8r
	systemctl is-active --quiet celery   && printf ""$GREEN"PASS:"$RESET" %-9s service is running\n" celery   || printf ""$YELLOW"FAIL:"$RESET" %-9s service is dead\n" celery
	systemctl is-active --quiet redis    && printf ""$GREEN"PASS:"$RESET" %-9s service is running\n" redis    || printf ""$YELLOW"FAIL:"$RESET" %-9s service is dead\n" redis

	#remoteit
	echo ''
	set +e #Suspend the error trap
	remoteit=$(dpkg -s remoteit 2> /dev/null)
	set -e #Resume the error trap

	remoteit_version=0
	if [[ $remoteit == *"install ok"* ]];
	then
		if [ -f /usr/lib/systemd/system/connectd.service ];
		then
			((remoteit_version=remoteit_version+1))
		fi
		if [ -f /usr/lib/systemd/system/remoteit-refresh.service ];
		then
			((remoteit_version=remoteit_version+2))
		fi
		case $remoteit_version in
			(0)
				echo -e ""$YELLOW"FAIL:"$RESET" remote.it is installed, with NEITHER legacy nor 2023 services detected. Try a reinstall?"
				;;
			(1)
				echo -e ""$GREEN"PASS:"$RESET" remote.it is installed - legacy config (uses connectd.service)"
				;;
			(2)
				echo -e ""$GREEN"PASS:"$RESET" remote.it is installed - 2023 config (uses remoteit-refresh.service)"
				;;
			(3)
				echo -e ""$YELLOW"FAIL:"$RESET" remote.it is installed, with conflicting config detected (legacy + 2023 services)"
				;;
		esac

		if systemctl is-active --quiet schannel;
		then
			echo -e ""$GREEN"PASS:"$RESET" schannel  service is running (remote.it)"
		else
			echo -e ""$YELLOW"FAIL:"$RESET" schannel  service is dead (remote.it)"
		fi

		# Test health of a legacy config:
		if [[ $remoteit_version == 1 ]];
		then
			if [ -f /etc/systemd/system/connectd.service ];
			then
				if  grep -q 'After=network.target rc-local.service celery.service' /etc/systemd/system/connectd.service;
				then
					echo -e ""$GREEN"PASS:"$RESET" /etc/systemd/system/connectd.service waits until celery is up"
				else
					echo -e ""$YELLOW"FAIL:"$RESET" /etc/systemd/system/connectd.service does NOT wait until celery is up. Run 'sudo -E ./setup.sh remoteit' to fix"
				fi
			else
				echo -e ""$YELLOW"FAIL:"$RESET" /etc/systemd/system/connectd.service not present. Run 'sudo -E ./setup.sh remoteit' to fix"
			fi
		fi
		
		# Test health of a 2023 config:
		# If present, the service name will be injected into the start of the service list, so it displays first, retaining the correct context.
		
	else
		echo -e ""$GREEN"PASS:"$RESET" remote.it is not installed"
	fi

	matchRegex="\s*Names=([\.[:alnum:]-]*).*LoadState=(\w*).*ActiveState=(\w*).*SubState=(\w*).*" # Bash doesn't do digits as "\d"
	serviceList="setTime cameraTransfer piTransfer heartbeat.timer apt-daily.timer apt-daily.service"
	if [[ $remoteit_version == 2 ]];
	then
		serviceList="remoteit-refresh.service ${serviceList}"
	fi
	for service in $serviceList; do
		status=$(systemctl show $service)
		if [[ $status =~ $matchRegex ]] ;
		then
			serviceName=${BASH_REMATCH[1]}
			serviceLoadState=${BASH_REMATCH[2]}
			serviceActiveState=${BASH_REMATCH[3]}
			serviceSubState=${BASH_REMATCH[4]}
		fi
		echo ''
		echo -e "Service = $serviceName"
		case "$serviceName" in
			("heartbeat.timer")
				[ $serviceLoadState == 'loaded' ]     && echo -e "  LoadState   = "$GREEN"$serviceLoadState"$RESET""   || echo -e "  LoadState   = "$YELLOW"$serviceLoadState"$RESET""
				[ $serviceActiveState == 'active' ]   && echo -e "  ActiveState = "$GREEN"$serviceActiveState"$RESET"" || echo -e "  ActiveState = "$YELLOW"$serviceActiveState"$RESET""
				;;
			("apt-daily.timer")
				[ $serviceLoadState == 'masked' ]     && echo -e "  LoadState   = "$GREEN"$serviceLoadState"$RESET""   || echo -e "  LoadState   = "$YELLOW"$serviceLoadState"$RESET""
				[ $serviceActiveState == 'inactive' ]   && echo -e "  ActiveState = "$GREEN"$serviceActiveState"$RESET"" || echo -e "  ActiveState = "$YELLOW"$serviceActiveState"$RESET""
				;;
			("apt-daily.service")
				[ $serviceLoadState == 'loaded' ]     && echo -e "  LoadState   = "$GREEN"$serviceLoadState"$RESET""   || echo -e "  LoadState   = "$YELLOW"$serviceLoadState"$RESET""
				[ $serviceActiveState == 'inactive' ]   && echo -e "  ActiveState = "$GREEN"$serviceActiveState"$RESET"" || echo -e "  ActiveState = "$YELLOW"$serviceActiveState"$RESET""
				;;
			(*)
				[ $serviceLoadState == 'loaded' ]     && echo -e "  LoadState   = "$GREEN"$serviceLoadState"$RESET""   || echo -e "  LoadState   = "$YELLOW"$serviceLoadState"$RESET""
				[ $serviceActiveState == 'inactive' ] && echo -e "  ActiveState = "$GREEN"$serviceActiveState"$RESET"" || echo -e "  ActiveState = "$YELLOW"$serviceActiveState"$RESET""
				;;
		esac
		[ $serviceSubState != 'failed' ] && echo -e "  SubState    = "$GREEN"$serviceSubState"$RESET"" || echo -e "  SubState    = "$YELLOW"$serviceSubState"$RESET""
	done

	timeTest
	echo ''

	gvfsFiles="/usr/lib/gvfs/gvfsd-gphoto2 /usr/lib/gvfs/gvfs-gphoto2-volume-monitor"
	for gvfsFile in $gvfsFiles;
	do
		[ -x  $gvfsFile ] && ""$YELLOW"FAIL:"$RESET" %-41s is executable\n" $gvfsFile || printf ""$GREEN"PASS:"$RESET" %-41s is not executable or does not exist\n" $gvfsFile
	done

	echo ''
}


test_os()
{
	set +e #Suspend the error trap
	desktop=$(type Xorg 2>&1)
	set -e #Resume the error trap
	matchRegex="not found$"
	if [[ $desktop =~ $matchRegex ]];
	then
		echo ''
		echo -e ""$GREEN"PASS:"$RESET" OS test passed - DESKTOP operating system not installed"
		echo ''
	else
		echo ''
		echo -e ""$YELLOW"FAIL:"$RESET" Unsupported DESKTOP operating system version detected"
		echo $desktop
		echo ''
		echo "Use the Raspberry Pi Imager @ https://www.raspberrypi.com/software/ to install the 'no desktop environment' version"
		echo "(It's on the 'Raspberry Pi OS (other)' page)"
		echo "See https://github.com/greiginsydney/Intervalometerator/blob/master/docs/step1-setup-the-Pi.md"
		echo ''
		exit
	fi
}


remoteit()
{
	if [ -f /usr/lib/systemd/system/connectd.service ];
	then
		echo -e ""$GREEN"PASS:"$RESET" remote.it   is   installed - legacy version"
		if [ -f /etc/systemd/system/connectd.service ];
		then
			#There's already a customised version of connectd.service
			echo -e 'A copy of connectd.service already exists in /etc/systemd/system/'
		else
			cp -fv /usr/lib/systemd/system/connectd.service /etc/systemd/system/connectd.service
		fi
		#Modify the service to wait until celery is up:
		if  grep -q 'After=network.target rc-local.service celery.service' /etc/systemd/system/connectd.service;
		then
			echo "'After=celery.service' suffix is already present"
		else
			sed -i -E 's/^(After=network.target rc-local.service)(.*)$/\1 celery.service/g' /etc/systemd/system/connectd.service #Add AFTER celery.service
			echo "Added 'After=celery.service' suffix"
			sed -i "/^After=network.target rc-local.service celery.service/a #Celery requirement added by intvlm8r setup.sh $today" /etc/systemd/system/connectd.service
		fi
	else
		echo -e ""$GREEN"PASS:"$RESET" remote.it is not installed - legacy version"
		if [ -f /etc/systemd/system/connectd.service ];
		then
			rm -f /etc/systemd/system/connectd.service;
			echo 'Removed /etc/systemd/system/connectd.service'
		fi
	fi
	if [ -f /usr/lib/systemd/system/remoteit-refresh.service ];
	then
		echo -e ""$GREEN"PASS:"$RESET" remote.it   is   installed - current (2023) version"
	else
		echo -e ""$GREEN"PASS:"$RESET" remote.it is not installed - current (2023) version"
	fi
}


# Here's where I test new bits when I'm working on the script.
# Released versions of the script shouldn't have anything there. That's the plan anyway.
dev()
{
	echo ''
}


prompt_for_reboot()
{
	echo ''
	read -p 'Reboot now? [Y/n]: ' rebootResponse
	case $rebootResponse in
		(y|Y|"")
			echo 'Bye!'
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
	echo -e "\nPlease re-run as 'sudo -E [-H] ./setup.sh <step>'"
	echo -e "(Only the 'start' step needs the extra -H switch)"
	exit 1
fi

case "$1" in
	('start')
		test_os
		venv_test
		install_apps
		prompt_for_reboot
		;;
	('web')
		test_os
		venv_test
		install_website
		prompt_for_reboot
		;;
	('login')
		test_os
		chg_web_login
		;;
	('ap')
		test_os
		make_ap
		prompt_for_reboot
		;;
	('noap')
		test_os
		unmake_ap
		prompt_for_reboot
		;;
	('time')
		test_os
		timeTest
		timeSync1
		timeSync2
		;;
	('remoteit')
		remoteit
		;;
	('test')
		test_install
		;;
	('dev')
		dev
		;;
	('')
		echo -e "\nNo option specified. Re-run with 'start', 'web', 'login', 'ap', 'noap', 'test', 'time' or 'remoteit' after the script name\n"
		exit 1
		;;
	(*)
		echo -e "\nThe switch '$1' is invalid. Try again.\n"
		exit 1
		;;
esac

# Exit from the script with success (0)
exit 0
