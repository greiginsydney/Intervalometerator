# Frequently Asked Questions

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

## My Camera and/or Pi are running low on storage. How can I delete old images?

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

