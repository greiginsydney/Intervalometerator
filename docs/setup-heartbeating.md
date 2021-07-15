"In computer science, a heartbeat is a periodic signal generated by hardware or software to indicate normal operation or to synchronize other parts of a computer system." - [Wikipedia](https://en.wikipedia.org/wiki/Heartbeat_(computing))

# Heartbeating

- [Overview](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/setup-heartbeating.md#setup-heartbeating)
- [Setup Heartbeating](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/setup-heartbeating.md#setup-heartbeating)
- [Setup "Dead Man’s Snitch"](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/setup-heartbeating.md#setup-dead-mans-snitch)

<hr />

## Overview

The intvlm8r can be set to send a periodic "check in" message (a heartbeat) to a remote web address. The remote service then generates an alert when a regularly-scheduled poll/heartbeat has been missed.

Any web address can be used for this: the onus is on the receiving service to identify the intvlm8r (typically through the use of a dedicated URL), log the heartbeats and determine when a heartbeat has been missed.

When enabled, the intvlm8r will send a heartbeat when the Pi is started or rebooted, and then a regular shedule, with options of 5, 10, 15, 20, 30 or 60 minutes. The user can also manually trigger a heartbeat from the /monitoring page, which is typically only used when setting up or debugging this feature.

The regular heartbeating process exercises multiple components of the intvlm8r as a way of ensuring that the failure of a critical component will result in the failure of the hearteat. A timer service triggers the execution of `heartbeat.py` every five minutes. This script runs, querying `intvlm8r.ini` to determine if it's time to initiate a heartbeat (and that a valid URL has been set). If a heartbeat is due, it generates an internal web call to the /heartbeat page. In responding to this request, the intvlm8r then passes the request to Celery to make the web call to the heartbeat url. Should any of these components be in a failed state, the heartbeat will not be sent and the monitoring service will trigger an alarm.

After each heartbeat is generated, the received web result is checked. If a "success" [status code](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes) wasn't received the intvlm8r will attempt a second heartbeat. 

To minimise log bloat (as it executes every five minutes) heartbeat.py logs only its last execution attempt to `heartbeat.log`. The intvlm8r logs the success/failure of heartbeat attempts to `gunicorn.error`, and the last result is stored in `hbresults.txt`, which is then shown on the /monitoring page.

The heartbeating service shown in this example is "Dead Man's Snitch", however any equivalent service can be used. "Dead Man's Snitch" offers a free tier, as well as multiple paid options. (We have no commercial relationship with "Dead Man's Snitch".)
<br/>
<hr />

[Top](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/setup-heartbeating.md#setup-heartbeating)
<hr/>

## Setup Heartbeating

Heartbeating is enabled from the new `Remote monitoring` option on the hamburger menu:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/125580526-8d235030-c38f-4517-9d25-a0037d760b89.png" width="40%">
</p>

The `Apply` and `Heartbeat now` buttons are interlocked. If you make a change on this page the Apply button will be enabled, prompting you to save the change. Only once a change has been saved will the `Heartbeat now` button be enabled.

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/125580029-c95dea9d-07b1-4d8c-a50f-dd199ffdf504.png" width="50%">
</p>

The heartbeat URL is checked for validity as you type. Invalid URLs will be shown with a red border around the field, and the buttons will be disabled:
<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/125581105-274363a2-889d-4a26-8dc0-16ef9d8657e2.png" width="50%">
</p>

Heartbeating will automatically commence the next time the minute is divisible by the selected frequency value, and always at the top of the hour.

[Top](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/setup-heartbeating.md#setup-heartbeating)
<hr/>

## Setup "Dead Man’s Snitch"

1. Browse to [https://deadmanssnitch.com/](https://deadmanssnitch.com/)
2. Click the "SIGN UP" button in the top right corner & create yourself an account. Once you've done that you'll be automatically taken through the steps to setup your "plan" and create your first Snitch.
3. On the page "Choose a plan for your new Case", scroll to the bottom and click the button to select the "NO FRILLS FREE PLAN", or lash out with one of the paid options.
4. On the page "New Snitch", give it a name and select the Interval. (Note in this example of the free plan, some of the advanced options are greyed out):

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/125729615-697d65d8-965d-431f-b759-8bae4222d8a0.png" width="80%">
</p>

5. Click SAVE.

6. You're done! It's that simple!!

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/125729700-48c43ae9-32c9-4f49-86b8-dae9047ed364.png" width="80%">
</p>

7. Copy "Your Unique Snitch URL" and paste it into the URL field on the intvlm8r. Don't worry about losing it, you can always return to Dead Man's Snitch and retrieve it.

8. Before you get distracted, don't forget to respond to the confirmation e-mail in your inbox:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/125730218-fad365d5-e5b3-40dc-975a-e97f3bb7a6d8.png" width="80%">
</p>

[Top](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/setup-heartbeating.md#setup-heartbeating)
<hr/>