/******************************************************************************
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License 
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied 
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see 
<http://www.gnu.org/licenses/>.

This script is part of the Intervalometerator project, a time-lapse camera controller for DSLRs:
https://github.com/greiginsydney/Intervalometerator
https://greiginsydney.com/intvlm8r
https://intvlm8r.com
 
References:
 https://github.com/sparkfun/SparkFun_DS3234_RTC_Arduino_Library
 https://www.hackster.io/aardweeno/controlling-an-arduino-from-a-pi3-using-i2c-59817b
 
Last updated/changed in version:
4.0.2
*****************************************************************************/
#include <SPI.h>   // SPI - The underlying comms to talk to the clock
#include <Wire.h>  // I2C - to talk to the Pi
#include <EEPROM.h>
#include <SparkFunDS3234RTC.h>
#include <LowPower.h>

//////////////////////////////////
//        Pin Definitions       //
//////////////////////////////////
#define DS13074_CS_PIN 10 // DeadOn RTC Chip-select pin
#define RTC_IRQ_PIN     2 // DeadOn RTC SQW/interrupt pin
#define REED_IRQ_PIN    3 // Low wakes the Arduino & signals it to wake the Pi
#define WAKE_PIN        4 // High wakes the cammera ("half press")
#define FIRE_PIN        5 // High takes a photo
#define LED_PIN         6 // Monitor LED
#define PI_POWER        7 // Take High to enable the Pi's power (output)
#define PI_RUNNING      8 // The Pi takes this High when it's running (input)
#define PI_SHUTDOWN     9 // Take low to initiate a shutdown in the Pi
#define MAINT_PIN      14 // Take low to enable Maintenance Mode (D14 = A0 = PC0)

#define DS3234_REGISTER_CONTROL 0x0E
#define DS3234_REGISTER_STATUS  0x0F

//////////////////////////////////
//   EEPROM memory allocations  //
//////////////////////////////////
#define MEMInterval   0x00
#define MEMAlarm2     0x01
#define MEMShootDays  0x02
#define MEMStartHour  0x03
#define MEMEndHour    0x04
#define MEMWakePiHour 0x05
#define MEMWakePiDuration 0x06
#define MEMTempMin    0x07  //2 bytes to store an int.
#define MEMTempMax    0x09  // "

//////////////////////////////////
//          I2C SETUP           //
//////////////////////////////////
#define SLAVE_ADDRESS 0x04


//////////////////////////////////
//    Declare some variables    //
//////////////////////////////////
volatile bool   SLEEP = false;  //
volatile bool   ALARM = false;  //
volatile bool   WakePi = true;  // Defaults true. Turns the Pi on (for at least WakePiDuration) when the Arduino powers-up
volatile bool   wakeCameraFlag  = false; // These flags are all set in the I2C ISR
volatile bool   setIntervalFlag = false; //
volatile bool   setTimeDateFlag = false; //
volatile bool   setWakePiFlag   = false; //
volatile bool   resetArduinoFlag = false; //
volatile bool   resetTempMinFlag = false; //
volatile bool   resetTempMaxFlag = false; //
volatile bool   getTempsFlag     = false; //

bool   LastRunningState = LOW;  // Used in loop() to tell for a falling Edge of the Pi state
bool   LastMaintState = HIGH;   // Used in loop() to tell if the maint/debug jumper has been removed
bool   LastRtcIrqState = LOW;   // Used in loop() to help protect against "stuck" issues
byte   ShootDays = 0b11111110;  // Default shoot days (Mon-Sun). Only used if we power up with a flat clock battery
byte   todayAsBits = 0;         // Used in Loop() to determine if we will shoot today.
byte   StartHour = 00;          // Default start hour.
byte   EndHour   = 23;          // Default end hour.
byte   interval  = 15;          // Default spacing between photos. Defaults to a photo every 15 minutes
byte   WakePiHour = 14;         // At what hour each day do we wake the Pi. Hour in 24-hour time. Changeable from the Pi
byte   WakePiDuration = 30;     // This is how long we leave the Pi awake for. Changeable from the Pi
byte   PiShutdownMinute = 0;    // The value pushed to Alarm2 after the Pi wakes up. This becomes the time we'll shut it down.

String newTimeDate = "";        // A new time and date sent by the Pi
String newInterval = "";        // A new interval sent by the Pi
String newWakePiTime = "";      // A new time and duration sent by the Pi

char sendToPi[32];              // This is the string we send to the Pi when it asks for data
char LastShotMsg[6] = "19999";  // Sent to the Pi. Is "<d><hh><mm>" where d is Sunday=1...
char NextShotMsg[6] = "19999";  // Sent to the Pi. Same as above.
char Intervalstring[8];         // Sent to the Pi. Is "<d><startHour><EndHour><Interval>"
char TemperaturesString[16];    // Sent to the Pi. Is "<CurrentTemp>,<MaxTemp>,<MinTemp>"


//////////////////////////////////
//            SETUP             //
//////////////////////////////////

void setup()
{
  // Use the Serial monitor to view time/date output
  // LEAVE ALL THE SERIAL LINES COMMENTED-OUT IN PRODUCTION.
  // They're left here for short-term debugging use ONLY
  //Serial.begin(9600);
  //Serial.println("");
  //Serial.println("Hello. I've just booted");
  
  // initialize i2c as slave
  Wire.begin(SLAVE_ADDRESS);
  // define callbacks for i2c communication
  Wire.onReceive(receiveEvent);
  Wire.onRequest(sendData);

  //Setup the IO pins for the camera interface:
  pinMode(WAKE_PIN, OUTPUT);
  pinMode(FIRE_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(WAKE_PIN, LOW); // Opto OFF
  digitalWrite(FIRE_PIN, LOW); // Opto OFF
  digitalWrite(LED_PIN, LOW);  // LED OFF

  pinMode(RTC_IRQ_PIN, INPUT);          // Clock IRQ pin. (There's an on-board physical pullup)
  pinMode(REED_IRQ_PIN, INPUT_PULLUP);  // Reed switch IRQ pin
  pinMode(MAINT_PIN, INPUT_PULLUP);     // On-board link: Take to GND to invoke maint mode

  pinMode(PI_POWER, OUTPUT);            // Take to GND to power the Pi
  pinMode(PI_RUNNING, INPUT);           // The Pi holds this high while it's running. There's an on-board physical pull-down resistor
  pinMode(PI_SHUTDOWN, OUTPUT);         // Take LOW to signal the Pi to shutdown
  digitalWrite(PI_SHUTDOWN, HIGH);      // Set this High or the Pi will never power-up
  digitalWrite(PI_POWER, LOW);          // We'll turn the Pi on at boot when we get to loop()

  // Call rtc.begin([cs]) to initialize the library
  // The chip-select pin should be sent as the only parameter
  rtc.begin(DS13074_CS_PIN);
  DelaymS (1000);

  uint8_t MemTest = rtc.readFromRegister(DS3234_REGISTER_CONTROL);

  //Serial.println("SRAM said ");
  //Serial.println(MemTest,BIN);
  //Test to see if this is a VIRGIN COLD start, or if the clock is running OK & we have values in the registers?
  // From cold the two alarms will NOT be set (1 in their respective bits)
  if (MemTest & 0x03 == 3)
  {
    //Serial.println("HEALTHY");
    FlashLed(4); //Healthy boot
    interval       = EEPROM.read(MEMInterval);
    ShootDays      = EEPROM.read(MEMShootDays);
    StartHour      = EEPROM.read(MEMStartHour);
    EndHour        = EEPROM.read(MEMEndHour);
    WakePiHour     = EEPROM.read(MEMWakePiHour);
    WakePiDuration = EEPROM.read(MEMWakePiDuration);
    //Serial.println("Values from RAM are start hour = " + String(StartHour));
    //Serial.println("Values from RAM are end hour   = " + String(EndHour));
    //Serial.println("Values from RAM are interval   = " + String(interval));
  }
  else
  {
    // This is our first power-up from failure.
    // There's no info in the clock & because of this we can't trust the EEPROM values
    //Serial.println("UNHEALTHY");
    FlashLed(8); //Unhealthy boot
    rtc.set24Hour(); // Force 24-hour mode to be sure (even though that's its default anyway)
    // Default to 12:00:01 pm, January 1, 2018:
    setTimeDate("20180101120001");
    EEPROM.write(MEMShootDays, ShootDays);
    EEPROM.write(MEMStartHour, StartHour);
    EEPROM.write(MEMEndHour, EndHour);
    EEPROM.write(MEMInterval, interval);
    EEPROM.write(MEMWakePiHour, WakePiHour);
    EEPROM.write(MEMWakePiDuration, WakePiDuration);
    EEPROM.put(MEMTempMin, (int)200); //Initialise to extremes, so next pass they'll be overwritten with valid values
    EEPROM.put(MEMTempMax, (int)-200);
    //Serial.println("Default values burnt to RAM are interval = " + String(interval));
  }

  UpdateTempMinMax(""); //Reset or initialise the temperature readings on boot

  //This is prepared as a string here in preparation for the next time the Pi requests confirmation:
  sprintf(Intervalstring, "%c%02d%02d%02d", ShootDays, StartHour, EndHour, interval);

  //Serial.println("INTERVAL STRING ON LOAD = " + String(Intervalstring));
  // Update time/date values, so we can set alarms
  rtc.update();
  // Enable SQW pin as an interrupt: alarm 1 is enabled permanently, alarm 2 depends on the WakePi setting
  rtc.enableAlarmInterrupt(true, true);
  DelaymS (400); // A brief pause between enabling the alarm interrupts and doing same in the Arduino:
  attachInterrupt (digitalPinToInterrupt(RTC_IRQ_PIN), wakeisr, FALLING);  // attach interrupt handler for RTC
  attachInterrupt (digitalPinToInterrupt(REED_IRQ_PIN), REEDisr, FALLING); // attach interrupt handler for reed switch

  // Initialise the alarm
  // When Alarm1 fires we take a photo:
  SetAlarm1();

  SLEEP = false;
  ALARM = true; // Run one loop through the alarm code to clear any alarm that might already be asserted
  DelaymS (2000); //All this does is add a pause between the bootup LED signals & the two when WakePi is actioned.
}


//////////////////////////////////
//         START FUNCTIONS      //
//////////////////////////////////

void WakeCamera()
{
  //printTime();
  //Serial.println("Wake Camera\r\n");

  digitalWrite(WAKE_PIN, HIGH); // Wake the camera up
  DelaymS(400);
  digitalWrite(WAKE_PIN, LOW); //
}


void TakePhoto()
{
  //Serial.println("Take Photo\r\n");
  bitWrite(PORTD, LED_PIN, LOW); //Make sure the LED's off when we take a photo
  digitalWrite(WAKE_PIN, HIGH); // Wake the camera up
  DelaymS (800);
  digitalWrite(FIRE_PIN, HIGH); // You take photo!
  DelaymS (200);
  digitalWrite(FIRE_PIN, LOW); //
  digitalWrite(WAKE_PIN, LOW); //

  sprintf(LastShotMsg, "%d%02d%02d", rtc.getDay(), rtc.getHour(), rtc.getMinute());
}


void SetAlarm1()
{
  //printTime();

  byte nextDay  = rtc.getDay();
  byte nextShot = rtc.getMinute();
  byte nextHour = rtc.getHour();
 
  // Lunchtime kludge
  // Un-comment this code and set nextHour and nextShot values as appropriate
  //  if (nextHour == 12)
  //  {
  //     nextHour = 13;
  //     nextShot = 59;
  //  }
 
  do
  {
    nextShot++;
  } while (nextShot % interval != 0);

  if (nextShot >= 60) // Correct for wrapping around the hour
  {
    nextShot -= 60 ;
    nextHour++;
    if (nextHour >= 24) // Correct for wrapping around the day
    {
      nextHour = 0;
      nextDay++;
    }
  }

  //We haven't yet started for the day:
  if (nextHour < StartHour)
  {
    nextHour = StartHour; //Reset the alarm to restart later today
    nextShot = 0;
  }

  //We've finished for today:
  if (nextHour >= EndHour)
  {
    nextHour = StartHour; //Reset the alarm to restart next shooting day
    nextShot = 0;
    nextDay++;
  }

  if (nextDay == 8) nextDay = 1; //Correct in case the day has wrapped around the week

  byte nextShootDay = 0b0000001 << (nextDay); //Sunday = bit 1 to align with clock's day ordering
  while (!(nextShootDay & ShootDays))
  {
    nextShot = 0; //Next shot isn't today, so reset this to the top of the hour
    nextDay++;
    if (nextDay == 8) nextDay = 1;
    nextShootDay = 0b0000001 << (nextDay);
  }

  // NB: Whilst this code calculates the DAY, hour and minute for the next photo, we don't add the
  // day to the alarm, even though the RTC supports this.
  // This is a deliberate safety net. If we happen to miss an alarm for whatever reason, it will
  // fire again "tomorrow" and kick us back into sync, with the loss of only one shooting day.

  //Retention of the "next day" code here is purely for the benefit of the message on the PI's home screen.

  rtc.setAlarm1(0, nextShot, nextHour); // Alarm format is "(seconds, minute, hours)"
  //Serial.println("Set alarm 1 at " + String(nextHour) + ":" + String(nextShot) + "\r\n");
  sprintf(NextShotMsg, "%d%02d%02d", nextDay, nextHour, nextShot);
}


void SetAlarm2(bool reset)
{
  byte AlarmMinute = 0;
  
  printTime();

  if (WakePiHour == 25)
  {
    //The Pi is always running. Alarm2 is only ever needed at the top of the hour:
    AlarmMinute = 0;
  }
  else
  {
    if (reset == HIGH)
    {
      // Reset/restart the Pi Shutdown timer. Either the real time or the PiDuration has changed, or the Pi's just woken up:
      PiShutdownMinute = rtc.getMinute() + WakePiDuration;
      if (PiShutdownMinute >= 60)
      {
        PiShutdownMinute -= 60 ;
      }
      else
      {
        AlarmMinute = PiShutdownMinute;
      }
    }
    else
    {
      if (PiShutdownMinute < 60) { AlarmMinute = PiShutdownMinute; }
      // Else it defaults to 0.
    }
  }

  rtc.setAlarm2(AlarmMinute); // Alarm2 format is "(minute)" or "(minute, hours)"
  //Serial.println(" - Alarm 2 set for minute = " + String(AlarmMinute));
  //Serial.println(" - PiShutdownMinute = " + String(PiShutdownMinute));
}

void FlashLed(int flashes)
{
  for (int i = 1; i <= flashes; i++)
  {
    digitalWrite(LED_PIN, HIGH); // LED ON
    DelaymS (200);
    digitalWrite(LED_PIN, LOW); // LED OFF
    DelaymS (200);
  }
}


void printTime()
{
  String now;
  rtc.update();
  int nowHour = rtc.hour();
  int nowMin  = rtc.minute();
  int nowSec  = rtc.second();

  now = (nowHour < 10) ? '0' + String(nowHour) : String(nowHour);
  now += ":";
  now += (nowMin < 10) ? '0' + String(nowMin) : String(nowMin);
  now += ":";
  now += (nowSec < 10) ? '0' + String(nowSec) : String(nowSec);
  if (rtc.is12Hour()) // If we're in 12-hour mode
  {
    now += (rtc.pm()) ? " PM" : " AM"; // Returns true if PM
  }
  //Serial.print(now + "\r\n");
}


void setTimeDate(String newTime)
{
  //Serial.println("### - New Time = " + newTime);
  int yyyy;
  int mm;
  int dd;
  int hh;
  int minut;
  int ss;

  yyyy  = newTime.substring(0, 4).toInt();
  mm    = newTime.substring(4, 6).toInt();
  dd    = newTime.substring(6, 8).toInt();
  hh    = newTime.substring(8, 10).toInt();
  minut = newTime.substring(10, 12).toInt();
  ss    = newTime.substring(12, 14).toInt();

  int dayOfWeek = getDayOfWeek(yyyy, mm, dd);

  //The clock only wants to see the year as 2 digits!
  yyyy = yyyy - 2000;

  rtc.setTime(ss, minut, hh, dayOfWeek, dd, mm, yyyy);

  //Serial.print("Day = " + String(dayOfWeek) + "\r\n");

  SetAlarm2(HIGH);
}


int getDayOfWeek (int yyyy, int m, int d)
{
  // Thank you Erik: https://www.hackster.io/erikuchama/day-of-the-week-calculator-cde704

  //int m;          // Month Entry
  //int d;          // Day Entry
  int yy;         // Last 2 digits of the year (ie 2016 would be 16)
  //int yyyy;       // Year Entry
  int c;          // Century (ie 2016 would be 20)
  int mTable;     // Month value based on calculation table
  int SummedDate; // Add values combined in prep for Mod7 calc
  int DoW;        // Day of the week value (0-6)
  int leap;       // Leap Year or not
  int cTable;     // Century value based on calculation table

  // Leap Year Calculation
  if ((fmod(yyyy, 4) == 0 && fmod(yyyy, 100) != 0) || (fmod(yyyy, 400) == 0))
  {
    leap = 1;
  }
  else
  {
    leap = 0;
  }

  // Limit results to year 1900-2299 (to save memory)
  while (yyyy > 2299)
  {
    yyyy = yyyy - 400;
  }
  while (yyyy < 1900)
  {
    yyyy = yyyy + 400;
  }

  // Calculating century
  c = yyyy / 100;

  // Calculating two digit year
  yy = fmod(yyyy, 100);

  // Century value based on Table
  if (c == 19) {
    cTable = 1;
  }
  if (c == 20) {
    cTable = 0;
  }
  if (c == 21) {
    cTable = 5;
  }
  if (c == 22) {
    cTable = 3;
  }

  // Jan and Feb calculations affected by leap years
  if (m == 1)
  { if (leap == 1) {
      mTable = 6;
    }
    else          {
      mTable = 0;
    }
  }
  if (m == 2)
  { if (leap == 1) {
      mTable = 2;
    }
    else          {
      mTable = 3;
    }
  }
  // Other months not affected and have set values
  if (m == 10)           {
    mTable = 0;
  }
  if (m == 8)            {
    mTable = 2;
  }
  if (m == 3 || m == 11) {
    mTable = 3;
  }
  if (m == 4 || m == 7)  {
    mTable = 6;
  }
  if (m == 5)            {
    mTable = 1;
  }
  if (m == 6)            {
    mTable = 4;
  }
  if (m == 9 || m == 12) {
    mTable = 5;
  }

  // Enter the data into the formula
  SummedDate = d + mTable + yy + (yy / 4) + cTable;

  // Find remainder
  DoW = fmod(SummedDate, 7);

  //Adjust for the DS3234's view of the week. (This code reports Sat=0 but clock wants Sat=7):
  if (DoW == 0) DoW = 7;
  return DoW;
}


void setInterval(String incoming)
{
  //Serial.println("Set interval called with value = " + incoming);

  if (incoming.length() != 7) return;

  ShootDays = incoming.charAt(0);
  StartHour = (ValidateIncoming (StartHour,    incoming.substring(1, 3).toInt(), 00, 23));
  EndHour   = (ValidateIncoming (EndHour,      incoming.substring(3, 5).toInt(), 01, 24));
  interval  = (ValidateIncoming (interval, incoming.substring(5, 7).toInt(), 00, 60));

  EEPROM.write(MEMShootDays, ShootDays);
  EEPROM.write(MEMStartHour, StartHour);
  EEPROM.write(MEMEndHour,   EndHour);
  EEPROM.write(MEMInterval,  interval);

  //This is prepared as a string here in preparation for the next time the Pi requests confirmation:
  sprintf(Intervalstring, "%c%02d%02d%02d", ShootDays, StartHour, EndHour, interval);
  //Serial.println("Set interval ends. StartHour = " + String(StartHour) + ", EndHour = " + String(EndHour) + " & interval = " + String(interval));
}


void SetWakePiTime(String NewTimeDuration)
{
  byte PiShutdownAlarm;
  
  //Serial.println(" - New WakePi time = " + String(NewTimeDuration));
  if (NewTimeDuration.length() != 4) return;

  WakePiHour     = (ValidateIncoming (WakePiHour,     NewTimeDuration.substring(0, 2).toInt(), 00, 25));
  WakePiDuration = (ValidateIncoming (WakePiDuration, NewTimeDuration.substring(2, 4).toInt(), 05, 60));

  EEPROM.write(MEMWakePiHour,     WakePiHour);
  EEPROM.write(MEMWakePiDuration, WakePiDuration);
 
  SetAlarm2(HIGH);
}


int ValidateIncoming (int CurrentValue, int NewValue, int LowerValue, int UpperValue)
{
  if (NewValue > UpperValue)
  {
    //Serial.println("Nope, didn't like " + String(NewValue) + ", sticking with " + String(CurrentValue) + "\r\n");
    return CurrentValue;
  }
  if (NewValue < LowerValue)
  {
    //Serial.println("Nope, didn't like " + String(NewValue) + ", sticking with " + String(CurrentValue) + "\r\n");
    return CurrentValue;
  }
  return NewValue;
}


void DelaymS(int pauseFor)
{
  unsigned long entryTime = millis();
  unsigned long currentTime = millis();

  while (currentTime - entryTime < (long)pauseFor)
  {
    currentTime = millis();
  }
}


// Called once on boot and every hour thereafter, as Alarm2 fires
// Also called by the Pi as a precursor to requesting the temps be fed back to it.
void UpdateTempMinMax(String resetOption)
{
  float tempy = rtc.temperature();
  tempy < 0 ? tempy -= 0.5 : tempy += 0.5; // Need to cater for negative temps. Round all numbers away from zero
  int roundedTemp = round(tempy*10)/10.0; // Rounds the temp to a whole digit
  int currentMin;
  int currentMax;
  EEPROM.get(MEMTempMin, currentMin);
  EEPROM.get(MEMTempMax, currentMax);
  if (isnan(currentMin)) { currentMin = 200 ; }
  if (isnan(currentMax)) { currentMax = -200 ; }
  if (resetOption == "Min" || roundedTemp  < currentMin)
  {
    EEPROM.put(MEMTempMin, roundedTemp);
    currentMin = roundedTemp;
  }
  if (resetOption == "Max" || roundedTemp  > currentMax)
  {
    EEPROM.put(MEMTempMax, roundedTemp); 
    currentMax = roundedTemp;
  }
  sprintf(TemperaturesString, "%d,%d,%d", roundedTemp, currentMax, currentMin);
  TemperaturesString[strlen(TemperaturesString)+1] = '\0'; //Add a null terminator as strlen will vary
  //Serial.println(String(TemperaturesString) + "\r\n");
  return;
}

void softReset()
{
  asm volatile ("  jmp 0");
}


//////////////////////////////////
//         END FUNCTIONS        //
//////////////////////////////////


//////////////////////////////////
//           START ISRs         //
//////////////////////////////////

// Fires when the RTC has an alarm. Wake the Arduino if it was snoozing.
void wakeisr()
{
  //detachInterrupt(digitalPinToInterrupt(RTC_IRQ_PIN));
  ALARM = true;
  SLEEP = false;
}


// Fires when a local user wants to wake the Pi (out of schedule)
void REEDisr()
{
  WakePi = true;
  SLEEP = false;
}


// Fires when the Pi has something to say.
// This is an ISR. The goal is to do the absolute minimum here. Set flags as necessary and
// let code in 'loop()' action them.
//
void receiveEvent(int howMany) {
  String incoming = "";
  char tempTime[9];
  char tempDate[9];
  if (howMany == 0) return; //Probably not actually used in this implementation
  //Serial.print(" Receive fired. " + String(howMany) + " bytes expected\r\n");

  while (Wire.available())
  {
    char c = Wire.read(); // receive byte as a character
    //Discard any incoming nulls:
    if ( c != 0)
    {
      incoming += c;
    }
  }
  //Serial.print("Incoming = >" + incoming + "<\r\n");
  if (howMany == 1)
  {
    // These values require a response:
    if (incoming == "0")
    {
      //It wants to know the date:
      rtc.update(); //This updates the registers
      sprintf(sendToPi, "20%02d%02d%02d", rtc.year(), rtc.month(), rtc.date());
      //strcpy(sendToPi, getMyDate(tempDate));
    }
    else if (incoming == "1")
    {
      //It wants to know the time:
      //tempTime = getMyTime();
      sprintf(sendToPi, "%02d%02d%02d", rtc.hour(), rtc.minute(), rtc.second());
      //strcpy(sendToPi, tempTime);
    }
    else if (incoming == "2")
    {
      //It wants to know the last & next shots
      sprintf(sendToPi, "%s:%s", LastShotMsg, NextShotMsg);
      //Serial.println(" - NEXT/LAST= " + String(sendToPi));
    }
    else if (incoming == "3")
    {
      //It wants to know the days, hours and interval:
      strcpy(sendToPi, Intervalstring);
      //Serial.println(" - INTERVAL REQ'd = " + String(sendToPi));
    }
    else if (incoming == "4")
    {
      //It wants to know the temperature values:
      sprintf(sendToPi, TemperaturesString); 
    }
    else if (incoming == "5")
    {
      //It wants to know the Pi on time and duration:
      sprintf(sendToPi, "%02d%02d", WakePiHour, WakePiDuration);
    }
    return; //Requests have all been responded to. OK to exit the ISR
  }

  //These requests all require an action. Most of these set a flag here and let loop() do the work:
  if (incoming == "WC")
  {
    wakeCameraFlag = true;
  }
  else if (incoming.startsWith("ST="))
  {
    newTimeDate = incoming.substring(3);
    setTimeDateFlag = true;
  }
  else if (incoming.startsWith("SI=")) //e.g. "SI=15"
  {
    newInterval = (incoming.substring(3));
    setIntervalFlag = true;
  }
  else if (incoming.startsWith("SP=")) //e.g. "SP=1815" to wake @ 18:00 for 15 minutes
  {
    newWakePiTime = (incoming.substring(3));
    setWakePiFlag = true;
  }
  else if (incoming == "RA")
  {
    resetArduinoFlag = true;
  }
  else if (incoming == "GT")
  {
    getTempsFlag = true;
  }
  else if (incoming == "RN")
  {
    resetTempMinFlag = true;
  }
  else if (incoming == "RX")
  {
    resetTempMaxFlag = true;
  }
}


// callback for sending data
void sendData()
{
  //Serial.println(" - SENT = " + String(sendToPi));
  Wire.write((byte *) &sendToPi, sizeof(sendToPi));
}


//////////////////////////////////
//             END ISRs         //
//////////////////////////////////


void loop()
{
  // loop runs:
  // - on power-up
  // - when the RTC fires an alarm, and then stays looping until the alarm flag is reset
  // - when the "wake Pi" reed switch is detected, which triggers the Pi to turn on
  // - continuously, whenever the Pi is powered-up
  // ... otherwise we go back to sleep at the end of the loop and wait for the next interrupt

  //Debug loop: Toggle the LED each pass through here (if we're awake)
  if (bitRead(PINC, 0) == LOW) // A0, the Maint header is read as PORTC bit *0*
  {
    PORTD ^= bit(PORTD6); //aka "LED_PIN"
    LastMaintState = LOW;
  }
  else
  {
    if (LastMaintState == LOW)
    {
      bitWrite(PORTD, LED_PIN, LOW); //Make sure the LED's off if we're not in Maint mode
      LastMaintState = HIGH;
    }
  }

  if (ALARM == true)
  {
    //bitWrite(PORTD, LED_PIN, ON); //DEBUG: Turn the LED on. Remove this line when in operation to minimise current drain.
    //Serial.println(" - ALARM   fired");
    printTime();
    if (rtc.alarm1())
    {
      //Serial.println(" - ALARM 1 fired");
      todayAsBits = 0b0000001 << (rtc.getDay()); //Sunday = bit 1 to align with clock's day ordering
      if (todayAsBits && ShootDays)
      {
        TakePhoto();
      }
      SetAlarm1(); // Re-set the alarm
    }
    DelaymS(100);
    if (rtc.alarm2())
    {
      //Serial.println(" - ALARM 2 fired");
      rtc.update();
      if  (rtc.minute() == 0) { UpdateTempMinMax(""); }  // Runs at the top of the hour, 24x7
      if ((rtc.minute() == 0) && (rtc.hour() == WakePiHour))
      {
        //Serial.println(" -           " + String(rtc.hour()) + ":" + String(rtc.minute()) + "       WAKING the Pi");
        //Serial.println(" - WAKING the Pi via ALARM 2. WakePi set TRUE");
        WakePi = true; //Actioned elsewhere in loop()
      }
      else if ((rtc.minute() == PiShutdownMinute))
      {
        // Safety net: don't want rogue code turning the Pi off if it's meant to be always on
        if (WakePiHour != 25)
        {
          //Serial.println(" - ALARM 2 fired @ PiShutdownMinute " + String(rtc.hour()) + ":" + String(rtc.minute()) + ".");
          //Serial.println(" - Initiated a Pi shutdown");
          digitalWrite(PI_SHUTDOWN, LOW); // Instruct the Pi to shutdown
          PiShutdownMinute = 61;  // Reset to an invalid value.
        }
      }
      SetAlarm2(LOW);
    }
    ALARM = false;
  }

  if (setTimeDateFlag == true)
  {
    setTimeDate(newTimeDate);
    SetAlarm1(); // Re-set the alarm
    setTimeDateFlag = false;
  }

  if (setIntervalFlag == true)
  {
    setInterval(newInterval);
    SetAlarm1(); // Re-set the alarm
    setIntervalFlag = false;
  }

  if (wakeCameraFlag == true)
  {
    WakeCamera(); // Wake up!
    wakeCameraFlag = false;
  }

  if (setWakePiFlag == true)
  {
    SetWakePiTime(newWakePiTime); // What time do we wake the Pi?
    setWakePiFlag = false;
  }

  if (WakePi == true)
  {
    FlashLed(2);
    //Serial.println(" - WAKE PI fired");
    LastRunningState = LOW; //This serves to extend the run timer if the Pi is already running when this fires.
                            // It's both a feature and also a safety-net to make sure the shutdown timer is set.
    digitalWrite(PI_SHUTDOWN, HIGH); // Make sure the shutdown pin is high before we turn it on
    digitalWrite(PI_POWER, HIGH); // Turn the Pi on.
    //Serial.println("The Pi has just been powered on");
    WakePi = false; //We can reset the flag now.
    SLEEP = false;  //We won't sleep while the Pi is on.
  }

  if (resetArduinoFlag == true)
  {
    //Serial.println("ResetArduinoFlag set.");
    if (bitRead(PINB, 0) == HIGH) //PI_RUNNING (Pin 8) is read as PORTB bit *0*
    {
      digitalWrite(PI_SHUTDOWN, LOW); // Instruct the Pi to shutdown
      //Serial.println(" - Telling the Pi to shutdown");
    }
    else
    {
      //Serial.println(" - Resetting the Arduino");
      resetArduinoFlag = false;
      digitalWrite(PI_POWER, LOW); // Turn the Pi off. May be redundant, but as softReset is ambiguous, best be on the safe side.
      DelaymS(1000); //Just to be sure the above has 'taken'
      softReset();
    }
  }

  if (getTempsFlag == true)
  {
    UpdateTempMinMax("");
    getTempsFlag = false;
  }

  if (resetTempMinFlag == true)
  {
    UpdateTempMinMax("Min");
    resetTempMinFlag = false;
  }

  if (resetTempMaxFlag == true)
  {
    UpdateTempMinMax("Max");
    resetTempMaxFlag = false;
  }
  
  if (bitRead(PINB, 0) == LOW) //PI_RUNNING (Pin 8) is read as PORTB bit *0*. LOW means the Pi has gone to sleep
  {
    // Only remove power if we've prevously taken PI_SHUTDOWN (Pin 9) LOW *and* now PI_RUNNING has gone LOW:
    if ((LastRunningState == HIGH) && (bitRead(PORTB, 1) == LOW)) 
    {
      //This is a falling edge - the Pi has just gone to sleep.
      //Serial.println(" - PI_RUNNING went LOW");
      //Serial.println("LastRunningState WAS high, and PI_RUNNING went LOW. (The Pi has gone to sleep)");
      DelaymS(2000); //Just to be sure
      digitalWrite(PI_POWER, LOW);    // Turn the Pi off.
      digitalWrite(PI_SHUTDOWN, LOW); // This should already be low.
      SetAlarm2(LOW);
    }
    LastRunningState = LOW;
  }
  else
  {
    if (LastRunningState == LOW)
    {
      //This is a rising edge - the Pi's just woken up.
      //Set alarm2 in readiness to put it to sleep:
      //Serial.println("LastRunningState WAS low, and PI_RUNNING went HIGH. The Pi has just woken up");
      SetAlarm2(HIGH);
      LastRunningState = HIGH;
    }
  }

  //By the time we reach this point through the loop we'll have:
  // - taken any photo that's required
  // - serviced any housekeeping alarm
  // - made any changes pushed via the Pi
  // .. so now provided the Pi isn't running and ALARM isn't still set, we can sleep!

  if ((bitRead(PORTD, PI_POWER) == LOW) && (ALARM == false) && (resetArduinoFlag == false))
  {
    // The Pi is powered-off. It's safe for us to sleep
    //Serial.println(" - About to sleep");
    SLEEP = true;
  }

  if (SLEEP == true)
  {
    //Serial.println(" - SLEEP");
    //Serial.println("");
    //DelaymS(2000); //Only enabled when Debugging, to ensure println messages are written before we sleep.
    SLEEP = false; //Reset the flag BEFORE we power-down, otherwise we risk looping
    bitWrite(PORTD, LED_PIN, LOW); //Make sure the LED's off before going to sleep
    LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF); //SLEEP_FOREVER will only be woken by an IRQ
    // ni-ni!
  }
}
