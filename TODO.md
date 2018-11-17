# TODO

At this early stage in the project, there's a lot of room for feature growth.

Obvious improvements include:
* add (document) support for other camera models/brands
* design a PCB
* improve/enhance the web UI:
    * Add <a href="https://flask-login.readthedocs.io/en/latest/" target="_blank">flask-login</a> for security and session management
    * improve the CSS for better device/browser compatibility
    * add some more validity checking of the inputs (JS?)
    * add SSL support in the Pi
* add upload options for the photos. (You'll see we've catered for them in the HTML and Python, but they're undeveloped at the moment). Upload to a cloud service?
* add some Azure IoT-style telemetry, so you can remotely monitor it. Generate an alarm if it stops taking photos or fails to report in.

<br><br> 

Some supporting notes are on the [CONTRIBUTING.md](CONTRIBUTING.md) page.