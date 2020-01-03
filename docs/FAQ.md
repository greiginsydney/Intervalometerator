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
