# Setup the Pi for a public or private PKI certificate

## Starting from scratch?
Jump to [setup the Pi.md](/docs/step1-setup-the-Pi.md)


## Security
Before doing this, make sure that you have setup your firewall so that ports 80 and 443 - and ONLY ports 80 and 443 - are exposed to the Internet. You will need to have created a public DNS entry to point to the public IP address the Pi uses. These instructions assume that you have a static IP address.

Be 100% sure that you have set a secure password to connect to the Pi, changed from its well-known default "raspberry".

## Set the hostname and FQDN

1. The Pi's hostname is the first part of its Fully Qualified Domain Name (FQDN). Change it if you need to with `sudo hostname yourhostname`.
2. Add the required entries into the hosts file with `sudo nano /etc/hosts`. Add the public IP address, FQDN and hostname so the file looks like this:
```text
127.0.0.1	yourhostname
123.123.123.123	yourhostname.yourdomainname.com	yourhostname
```
3. Reboot the Pi: `sudo reboot now` and log back in after it reboots.

4. Navigate to the nginx folder, and we'll create a new sub-holder to house the certs:
`cd /etc/nginx && sudo mkdir ssl && cd ssl`

4. Create a temporary config file with the details required on the certificate: `sudo nano csrwithsan.cnf`

5. Paste the following into the file, replacing with your own values as appropriate of course:
```text
[ req ]
prompt             = no
default_bits       = 2048
distinguished_name = req_distinguished_name
req_extensions     = req_ext
[ req_distinguished_name ]
countryName                = AU
stateOrProvinceName        = New South Wales
localityName               = Sydney
organizationName           = greiginsydney
commonName                 = yourhostname.yourdomainname.com
[ req_ext ]
subjectAltName = @alt_names
[alt_names]
DNS.1   = yourhostname.yourdomainname.com
```

6. OpenSSL is used to generate a certificate signing request (CSR) that you will submit to your Certificate Authority (CA).
7. Issue this command to generate the request using the values from the config file:
```text
sudo openssl req -new -newkey rsa:2048 -nodes -out server.csr -keyout server.key -config csrwithsan.cnf
```

8. You should receive this output. Enter your country when prompted and press return:

9. All going well, this process will have dropped a server.key & server.csr file into the /etc/nginx/ssl/ directory. (If you used the Digicert Wizard, the filenames will reflect the hostname, but it's the file extensions that are the critical piece here).

10. Test the file before you continue, as you don't want to be addressing a typo retrospectively:
```
openssl req -noout -text -verify -in server.csr
```

11 The test should dump something like this to the screen. DOUBLE-check for typos in the Subject and SANs!
```text
verify OK
Certificate Request:
    Data:
        Version: 1 (0x0)
        Subject: C = AU, ST = New South Wales, L = Sydney, O = greiginsydney, CN = yourhostname.yourdomainname.com
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (2048 bit)
                Modulus:
                    00:d6:52:8e:c3:65:37:c2:e8:ec:ad:d8:4b:d3:7e:
                    9a:08:d5:b3:bf:02:70:9a:bb:88:03:57:e5:ff:c7:
                    <Lots deleted>
                    0d:0c:7d:25:88:f9:5e:aa:31:6a:40:8d:84:84:8e:
                    38:e7
                Exponent: 65537 (0x10001)
        Attributes:
        Requested Extensions:
            X509v3 Subject Alternative Name:
                DNS:yourhostname.yourdomainname.com
    Signature Algorithm: sha256WithRSAEncryption
         31:6d:d6:89:c3:4d:1d:1b:3d:93:00:15:df:38:92:7d:2e:f8:
         43:a7:ab:9b:54:98:dd:13:08:24:75:43:ca:e5:89:15:f9:04:
         <Lots deleted>
         09:2e:87:bf:f1:b3:fc:b3:46:ab:e8:b6:0d:18:33:7b:1c:10:
         8c:09:e4:3f
```

12. Copy the CSR file to your local PC and submit it to your CA to generate the certificate. If you're using a Windows-based CA, choose the "Base64 encoded" download option.

13. Copy the received file(s) to /etc/nginx/ssl/

14. If you received a .pem file from your CA, skip to step 16.

15. If you received the certificate as a .crt file and another .crt for the intermediate certificates, you need to concatenate them together into one file:
```text
cat your_domain_name.crt intermedCerts.crt >> bundle.crt
```

16. Edit the Nginx virtual host file: `sudo nano /etc/nginx/sites-available/intvlm8r` so it looks like this. If you've followed the steps from before, you should only need to add three 'ssl' lines:
```text
server {
    listen 80 default_server;
    server_name intvlm8r intvlm8r.yourdomainname.com; #Add in any aliases, separated by a space

    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/bundle.crt; # (Or the .pem or .cer file)
    ssl_certificate_key /etc/nginx/ssl/server.key;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/pi/www/intvlm8r.sock;
    }
}
```

17. Restart nginx with `sudo systemctl restart nginx`

18. You can now browse to the website securely!


## Next steps:
- [Configure the Pi as a DHCP server & WiFi Access Point (if required)](/docs/step3-setup-the-Pi-as-an-access-point.md)
- Start taking photos!

<br>
<hr >

## References

- https://www.digicert.com/csr-ssl-installation/nginx-openssl.htm
- http://nginx.org/en/docs/http/configuring_https_servers.html
- https://www.digitalocean.com/community/tutorials/how-to-create-an-ssl-certificate-on-nginx-for-ubuntu-14-04
- [Easy SAN addition](https://geekflare.com/san-ssl-certificate/)
