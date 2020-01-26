# Setup the Pi for Let's Encrypt SSL Certificates

## Starting from scratch?
Jump to [setup the Pi](/docs/step1-setup-the-Pi.md).


## Security
Before doing this, make sure that you have setup your firewall so that ports 80 and 443 - and ONLY ports 80 and 443 - are exposed to the Internet. You will need to have created a public DNS entry to point to the public IP address the Pi uses. These instructions assume that you have a static IP address.

Be 100% sure that you have set a secure password to connect to the Pi, changed from its well-known default "raspberry", and the intvlm8r's admin login has been changed to something other than admin/password.

## Set the hostname and FQDN

1. The Pi's hostname is the first part of its Fully Qualified Domain Name (FQDN), and we need this set correctly in order to generate the certificate. By default the SSH prompt is "\<username\>@\<hostname\>:" so it's easy to see, e.g. `pi@intvlm8r:`. If you need to change it, run `sudo raspi-config`, then `(2) Network Options` and `Hostname`.

> The "FQDN" is always the full web address, something like `myintvlm8r.mydomain.com.au`, and so its hostname in this example is just `myintvlm8r`

2. Add the required entries into the hosts file with `sudo nano /etc/hosts`. Add the public IP address, FQDN and hostname so the file looks like this:
```text
127.0.1.1	myintvlm8r
123.123.123.123	myintvlm8r.mydomain.com.au myintvlm8r
```
3. Reboot the Pi: `sudo reboot now` and log back in after it reboots.

4. Edit the Nginx virtual host file: `sudo nano /etc/nginx/sites-available/intvlm8r` to make sure the "server_name" field is the FQDN.

> Be very careful here as this step is case-sensitive. The FQDN entry here and the one used in Step 6 need to match, otherwise you'll get an "Unable to install the certificate" error at the end of Step 9.

5. Install certbot: `sudo apt install certbot python-certbot-nginx -y`

6. This command requests and then receives an SSL certificate from Let's Encrypt. Don't forget to replace the example FQDN below with your own:
```text
sudo certbot --authenticator standalone --installer nginx -d myintvlm8r.mydomain.com.au --pre-hook "service nginx stop" --post-hook "service nginx start"
```

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

9. Respond to the invitation to receive news from the EFF:
```text
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Would you be willing to share your email address with the Electronic Frontier
Foundation, a founding partner of the Let's Encrypt project and the non-profit
organization that develops Certbot? We'd like to send you email about our work
encrypting the web, EFF news, campaigns, and ways to support digital freedom.
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
(Y)es/(N)o:
```

10. When asked if you want to redirect HTTP traffic, the choice is yours. It's generally expected nowadays that a website will redirect unsecured requests (those over http) to its secured https version, however if you want your intvlm8r to be a little 'hidden' (applying the principle of 'security through obscurity') you should decline the offer and choose 'no redirect':

```text
Please choose whether or not to redirect HTTP traffic to HTTPS, removing HTTP access.
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
1: No redirect - Make no further changes to the webserver configuration.
2: Redirect - Make all requests redirect to secure HTTPS access. Choose this for
new sites, or if you're confident your site works on HTTPS. You can undo this
change by editing your web server's configuration.
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Select the appropriate number [1-2] then [enter] (press 'c' to cancel): 1
```

11. Hopefully, everything should be good:
```text
-------------------------------------------------------------------------------
Congratulations! You have successfully enabled https://myintvlm8r.mydomain.com.au

You should test your configuration at:
https://www.ssllabs.com/sslhostname/analyze.html?d=hostname.domainname.com
-------------------------------------------------------------------------------
```

12. Certbot will modify the Nginx virtual host config file with everything needed to work.

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
