# intvlm8r documentation

If you're new to the intvlm8r, there's plenty of documentation to whet your whistle.

## Background reading

The [Design Decisions](https://github.com/greiginsydney/Intervalometerator/wiki/Design-Decisions) page goes into lots of detail about all the decisions we made getting the intvlm8r to this stage.

Check out the [Circuit diagram (PDF)](/docs/intvlm8r_v11.11_circuit.pdf) and [PCB Component layout (PDF)](/docs/intvlm8r_v11.11_comp.pdf).

## Installation steps

1. [Setup the Pi](/docs/step1-setup-the-Pi.md) - start here to connect to the Pi and commence the installation.

2a. [Setup the Pi lets encrypt](/docs/step2-setup-the-Pi-lets-encrypt.md) - this covers how to add an SSL certificate from Let's Encrypt.

2b. [Setup the Pi public or private pki](/docs/step2-setup-the-Pi-public-or-private-pki.md) - or here's how to add a private or public certificate.

3. [Setup the Pi as an access point](/docs/step3-setup-the-Pi-as-an-access-point.md) - if you don't have a Wi-Fi network, the Pi/intvlm8r can become one for you.

4. [Setup upload options](/docs/step4-setup-upload-options.md) - this covers off the requirements and steps so the intvlm8r can upload images to some popular cloud destinations.
 
5. [PCB Assembly](/docs/step5-pcb-assembly.md) - walks you through the process of assembling the PCB.

6. [Program the Arduino](/docs/step6-program-the-Arduino.md) - an overview of how to program the Arduino.

7. [Bench testing](/docs/step7-bench-testing.md) - test it out!

8. [Case assembly](/docs/step8-case-assembly.md) - assembling the completed intvlm8r into a Pelican case.

9. [Setup heartbeating](/docs/setup-heartbeating.md) - setup remote monitoring, so you'll know the intvlm8r is OK.

## Debugging / troubleshooting

- [Troubleshooting](/docs/troubleshooting.md).
- There's also some additional info in [Advanced Config](/docs/advancedConfig.md).
- The [Frequently Asked Questions](/docs/FAQ.md) page is mostly answers to the "how do I...?" questions existing users ask.

## Upgrading

The upgrade process is the same as a fresh installation. The setup script detects the presence of an existing version and reacts accordingly.

Read more on the [Upgrade](/docs/upgrade.md) page.

<br>
