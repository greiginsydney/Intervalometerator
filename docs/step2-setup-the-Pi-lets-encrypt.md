# Setup the Pi for Let's Encrypt SSL Certificates

## Starting from scratch?
Jump to [setup the Pi](/docs/step1-setup-the-Pi.md).


## Security
Before doing this, make sure that you have setup your firewall so that ports 80 and 443 - and ONLY ports 80 and 443 - are exposed to the Internet. You will need to have created a public DNS entry to point to the public IP address the Pi uses. These instructions assume that you have a static IP address.

Be 100% sure that you have set a secure password to connect to the Pi, changed from its well-known default "raspberry".

## Set the hostname and FQDN

1. The Pi's hostname is the first part of its Fully Qualified Domain Name (FQDN). Change it if you need to with `sudo hostname yourhostname`.
2. Add the required entries into the hosts file with `sudo nano /etc/hosts`. Add the public IP address, FQDN and hostname so the file looks like this:
```text
127.0.1.1	yourhostname
123.123.123.123	yourhostname.yourdomainname.com	yourhostname
```
3. Reboot the Pi: `sudo reboot now` and log back in after it reboots.

4. Edit the Nginx virtual host file: `sudo nano /etc/nginx/sites-available/intvlm8r` to make sure the "server_name" field reflects the new hostname, and is your intended FQDN.

5. Install certbot: `sudo apt install certbot python-certbot-nginx -y`

6. This command requests and then receives an SSL certificate from Let's Encrypt:
```text
sudo certbot --authenticator standalone --installer nginx -d yourhostname.yourdomainname.com --pre-hook "service nginx stop" --post-hook "service nginx start"
```

> Note: Certbot in the Pi Repository is not the latest version, so you need to grab the certificate in standalone mode.

7. Enter your email address when prompted: 
```text
Enter email address (used for urgent renewal and security notices):
```

8. Agree to the LetsEncrypt Terms of Service:
```text
-------------------------------------------------------------------------------
Please read the Terms of Service at
https://letsencrypt.org/documents/LE-SA-v1.2-November-15-2017.pdf. You must
agree in order to register with the ACME server at
https://acme-v01.api.letsencrypt.org/directory
-------------------------------------------------------------------------------
(A)gree/(C)ancel:
```

9. When asked if you want to use HTTPS , select Option 2: Secure.
```text
Please choose whether HTTPS access is required or optional.
-------------------------------------------------------------------------------
1: Easy - Allow both HTTP and HTTPS access to these sites
2: Secure - Make all requests redirect to secure HTTPS access
-------------------------------------------------------------------------------
Select the appropriate number [1-2] then [enter] (press 'c' to cancel): 

```

10. Hopefully, everything should be good:
```text
-------------------------------------------------------------------------------
Congratulations! You have successfully enabled https://yourhostname.yourdomainname.com

You should hostname your configuration at:
https://www.ssllabs.com/sslhostname/analyze.html?d=hostname.domainname.com
-------------------------------------------------------------------------------
```

11. Certbot will modify the Nginx virtual host config file with everything needed to work.

As the certificate will expire every 90 days, certbot has created a cron job to check twice a day. 

To test the renewal process, use the command:
`sudo certbot renew --dry-run`

You can now browse to the website securely!


## Next steps:
- [Configure the Pi as a DHCP server & WiFi Access Point (if required)](/docs/step3-setup-the-Pi-as-an-access-point.md)
> Be careful using the Pi as a WiFi AP and a Let's Encrypt certificate. The Pi must have internet access in order for the relatively short lifespan certificates to be renewed. Without this your cert will expire in-situ and your browser will show a warning each time you access the site. Consider a public certificate (e.g. from [Digicert.com](https://digicert.com)) or your private internal PKI CA (if you have one).
- Start taking photos!

<br>
<hr >


## References

- [DigitalOcean - How To Secure Nginx with Let's Encrypt on Ubuntu 18.04](https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-18-04)
- https://community.letsencrypt.org/t/solution-client-with-the-currently-selected-authenticator-does-not-support-any-combination-of-challenges-that-will-satisfy-the-ca/49983
- [Certbot user-guide](https://certbot.eff.org/docs/using.html)
