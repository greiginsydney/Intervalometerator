# Frequently Asked Questions


- [Where do I change the website's login name and/or password?](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/FAQ.md#where-do-i-change-the-websites-login-name-andor-password)
- [How can I add more users to the list of website logins?](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/FAQ.md#how-can-i-add-more-users-to-the-list-of-website-logins)
- [Can I move the intvlm8r off port 80 or 443?](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/FAQ.md#can-i-move-the-intvlm8r-off-port-80-or-443)
- [My camera and/or Pi are running low on storage. How can I delete old images?](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/FAQ.md#my-camera-andor-pi-are-running-low-on-storage-how-can-i-delete-old-images)
- [Can I copy/transfer images more than once per day?](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/FAQ.md#can-i-copytransfer-images-more-than-once-per-day)
- [Can I pause the shooting schedule during the day (e.g. at lunchtime)?](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/FAQ.md#can-i-pause-the-shooting-schedule-during-the-day-eg-at-lunchtime)
- [Does the intvlm8r support Daylight Saving Time?](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/FAQ.md#does-the-intvlm8r-support-daylight-saving-time)
- [Can I install the intvlm8r under another user, not 'pi'?](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/FAQ.md#can-i-install-the-intvlm8r-under-another-user-not-pi)

<br>

<hr>

## Where do I change the website's login name and/or password?

If you only have one login (the default configuration), you can use the setup script with the "login" switch. This prompts you to change the _first_ login in the file:

```text
pi@Model3B:~ $ sudo -E ./setup.sh login
Change the website's login name: admin1
Change the website's password  : password1
"exit 0" command failed with exit code 0.   <-- ignore this. An exit code of 0 is good in Python-land.
pi@Model3B:~ $
```

The alternative is to manually edit the main python script (`sudo nano ~/www/intvlm8r.py`). Around line 75 is "# Our user database".

## How can I add more users to the list of website logins?

This is done by adding new lines to the main python script (`sudo nano ~/www/intvlm8r.py`). Around line 75 is "# Our user database".

Add more users in this format:

```text
# Our user database:
#users = {'admin': {'password': '### Paste the hash of the password here. See the Setup docs ###'}}
users = {'admin': {'password': 'password'}}
users.update({'superuser': {'password': 'godmode'}})
users.update({'someoneElse': {'password': 'rand0mCharact3rs'}})
```

## Can I move the intvlm8r off port 80 or 443?

Yes! It's as simple as changing the "listen" line in `/etc/nginx/sites-enabled/intlm8r` to the new port number. Oh, and don't forget to open the firewall and/or add a NAT translation rule for it.

In this example the intvlm8r now listens on port 8000:

```text
server {
    listen 8000 default_server;
    server_name intvlm8r intvlm8r.yourdomainname.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/pi/www/intvlm8r.sock;
    }
}
```

## My camera and/or Pi are running low on storage. How can I delete old images?

Hidden config options in the INI file will let you delete images off the camera after they've been safely transferred to the Pi, and after they've been safely uploaded to your nominated "off-box" destination.

This option isn't visible in the browser, so to change it you need to SSH to the Pi. Browse to /home/pi/www/ and edit the file intvlm8r.ini. Set the two highlighted options On or Off as required. If the option's not already there, just add the line in by hand:

<pre>
[Global]
file created = 05 Jan 2020
thumbscount = 20

[Transfer]
tfrmethod = Dropbox
dbx_token = thequickbrownfoxjumpsoverthelazydogorsomething
transferday = Daily
transferhour = 00
sftpserver = 20.20.20.20
sftpuser = intvlm8r
sftppassword = mysecretsftppassword
sftpremotefolder = upload/GreyBox/
<b>deleteaftertransfer = On</b>

[Copy]
copyday = Daily
copyhour = 00
<b>deleteaftercopy = On</b>
</pre>

## Can I copy/transfer images more than once per day?

The web interface only supports one copy (from the camera) and transfer (from the Pi) per day, but it's easy to add more by adding extra occurrences to the "crontable".

Here's what the crontable looks like by default:

``` python
pi@Model3B:~ $ crontab -l
0 * * * * /usr/bin/python3 /home/pi/www/cameraTransfer.py 2>&1 | logger -t cameraTransfer
0 * * * * /usr/bin/python3 /home/pi/www/piTransfer.py 2>&1 | logger -t piTransfer

```

The `0 * * * *` at the start of the line instructs the Pi to run python3 and the related script when minute = 0, every hour, every day. As defined here, the script runs at the top of every hour, checking if this hour and this day is the correct time to execute a copy or transfer before proceeding. If not, the script will exit and wait for the next hour.

You can edit the crontable with `crontab -e` and give it more things to do. Here I've added a copy at 15 minutes past the hour (every hour, every day), and a transfer at 15 minutes to:

```python
pi@Model3B:~ $ crontab -l
0 * * * * /usr/bin/python3 /home/pi/www/cameraTransfer.py 2>&1 | logger -t cameraTransfer
0 * * * * /usr/bin/python3 /home/pi/www/piTransfer.py 2>&1 | logger -t piTransfer

15 * * * * /usr/bin/python3 /home/pi/www/cameraTransfer.py copyNow 2>&1 | logger -t cameraTransfer
45 * * * * /usr/bin/python3 /home/pi/www/piTransfer.py copyNow 2>&1 | logger -t piTransfer
```

Note the trick is the addition of the 'copyNow' switch which forces the script to always copy/transfer, ignoring the value set in the web interface and read from the ini file.

> If you're using Nano as your editor, a quick way to copy a line is ^K then ^U. That deletes the line your cursor is on and reinstates it - but it leaves a copy on the 'clipboard' (to borrow a Windows term). Navigate to where you want the line copied and ^U again - but don't forget to change the time and add the copyNow switch.


## Can I pause the shooting schedule during the day (e.g. at lunchtime)?

The browser interface and the underlying code in both the Pi and Arduino don't allow two time schedules per day, nor one schedule with a break for lunch, and it would require a significant re-write to accommodate this.

That being said, a "lunchtime kludge" exists in the Arduino code (from v4.0.1) that will deliver this functionality. As it's fixed in the Arduino it's not something that can be changed from the Pi or through the browser interface, so turning it on or off, or changing the duration of the lunch break will necessitate opening the intvlm8r case and connecting a programming cable to the Arduino. The Pi isn't aware if the "lunchtime kludge" is active, so its calculations of shots per day will be inaccurate as a result, although "Last Shot" and "Next Shot" will always show the correct values.

The "lunchtime kludge" is commented-out by default. If you want to pause shooting for lunch, just un-comment the final five lines shown below (the "if" loop) by deleting the double slashes ('//') at the start of each line. Set the value of `if (nextHour == 12)` to the hour that the lunch break starts, and then set `nextHour = 13;` and `nextShot = 59;` to be one minute before you want shooting to resume. (In this example, a 2-hour lunch break starts at noon.)

```
// Lunchtime kludge
  // Un-comment this code and set nextHour and nextShot values as appropriate
  //  if (nextHour == 12)
  //  {
  //     nextHour = 13;
  //     nextShot = 59;
  //  }
```

If you only want to break for an hour, you can delete the `nextHour = 13;` line altogether and leave the nextShot minute at 59. If you only want a 30 minute lunch, delete the `nextHour = 13;` line (or leave it commented-out), change `nextShot` to 29, and the shooting schedule will recommence from 30 minutes past the current hour.

> This code runs at the start of the lunch break and tricks the intvlm8r into thinking it's already taken the shots that it would have during lunch. It then sets the next alarm time - the next shot to be taken - for the time immediately after lunch.

## Does the intvlm8r support Daylight Saving Time?

It depends.

If your intvlm8r is running off-grid, disconnected from the outside world, it relies on the battery-backed red ["DeadOn RTC"](https://www.sparkfun.com/products/10160) board as the master real-time clock, which is in itself not aware of timezone and thus when to adjust for DST. In such a config, manual intervention will be required as you enter and return from DST.

DST is catered for automatically if the intvlm8r has network connectivity, although this assumes you set the correct timezone in [setup step 8](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/step1-setup-the-Pi.md) and answered Yes to the NTP question:

```python
NTP Step. Does the Pi have network connectivity? [Y/n]:
```

If the Pi is set to always run, a cron job that fires every day at midnight will perform a sync of the time and date from the Pi to the Arduino. Here's an example of that from the /home/pi/setTime.log file:

```python
2021/06/14 00:00:02 systemd-timesyncd = active. The Pi takes its time from NTP. Updating the Arduino to follow Pi time
2021/06/14 00:00:02 Response code = 200
2021/06/14 00:00:02 This is what I received: <p>Set Arduino datetime to 20210614000002</p>
2021/06/14 00:00:02 New Arduino time is 20210614000002
```

## Can I install the intvlm8r under another user, not 'pi'?

Yes. Just create your new user (with `sudo adduser newusername`) before you start the install process.

By default a new user can't `sudo` things without needing to provide their password, which breaks the setTime script. To address this, run `sudo visudo` and add this line to the *bottom* of the file:

```
newusername  ALL=(ALL) NOPASSWD:ALL
```

This lets 'newusername' execute ALL commands without needing to constantly re-type their password. I'd like to be able to tighten it up, but haven't been able to find the right command/syntax for the script to be albe to run correctly - and it's not for a lack of trying.


<br>
<br>

[Top](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/FAQ.md)
