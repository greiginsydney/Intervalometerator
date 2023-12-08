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
*/
// Last updated/changed in version 4.6.0:
// - added 'shootFast'
char version[6] = "4.6.0";
/*****************************************************************************/
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
//#define V_SENSE_PIN    15 // Analog input, reads battery voltage (D15 = A1 = PC1)
                          // Commented-out until the battery hardware is finalised
                          // Spare ADCs: A6 = 20, A7 = 21

#define DS3234_REGISTER_CONTROL 0x0E
#define DS3234_REGISTER_STATUS  0x0F

//////////////////////////////////
//   EEPROM memory allocations  //
//////////////////////////////////
#define MEMInterval          0x00
#define MEMAlarm2            0x01
#define MEMShootDays         0x02
#define MEMStartHour         0x03
#define MEMEndHour           0x04
#define MEMWakePiHour        0x05
#define MEMWakePiDuration    0x06
#define MEMTempMin           0x07  // Changed from int (2 bytes) to int8_t (1 byte - signed) in 4.5.0
#define MEMTempMax           0x08  // "
#define MEM24Temp0           0x09  // Saved value for midnight.
#define MEM24Temp23          0x20  // Not actually used in code: it's here for me to know the last memory location I've used
#define MEMShootFastInterval 0x21

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
volatile bool   resetAlarm2Flag  = false; //

bool   LastRunningState = LOW;  // Used in loop() to tell for a falling Edge of the Pi state
bool   LastMaintState = HIGH;   // Used in loop() to tell if the maint/debug jumper has been removed
bool   LastRtcIrqState = LOW;   // Used in loop() to help protect against "stuck" issues
bool   readVbatteryFlag = LOW;  // Used in loop() to trigger a battery read

byte   ShootDays = 0b11111110;  // Default shoot days (Mon-Sun). Only used if we power up with a flat clock battery
byte   todayAsBits = 0;         // Used in Loop() to determine if we will shoot today
byte   StartHour = 00;          // Default start hour
byte   EndHour   = 23;          // Default end hour
byte   interval  = 15;          // Default spacing between photos. Defaults to a photo every 15 minutes
byte   shootFastInterval = 0;   // Spacing between photos when in 'shootFast' mode, multiple shots per minute
byte   shootFastCount = 0;      // The number of shots remaining in this 'shootFast' interval (this minute). (Global so it can be killed by setInterval if necessary)
byte   WakePiHour = 25;         // At what hour each day do we wake the Pi. Hour in 24-hour time. Changeable from the Pi
byte   WakePiDuration = 30;     // This is how long we leave the Pi awake for. Changeable from the Pi
byte   PiShutdownMinute = 0;    // The value pushed to Alarm2 after the Pi wakes up. This becomes the time we'll shut it down
byte   VoltageReadingCounter=0; // A global, so the asynch voltmeter loop knows how many times it's been called.

String newTimeDate = "";        // A new time and date sent by the Pi
String newInterval = "";        // A new interval sent by the Pi
String newWakePiTime = "";      // A new time and duration sent by the Pi

char sendToPi[32];              // This is the string we send to the Pi when it asks for data
char LastShotMsg[6] = "19999";  // Sent to the Pi. Is "<d><hh><mm>" where d is Sunday=1...
char NextShotMsg[6] = "19999";  // Sent to the Pi. Same as above
char Intervalstring[8];         // Sent to the Pi. Is "<d><startHour><EndHour><Interval>"
char TemperaturesString[16];    // Sent to the Pi. Is "<CurrentTemp>,<MaxTemp>,<MinTemp>"

int8_t DailyTemps[25];          // 24 temperature readings, one per hour. The offset is the reading for that hour. A signed byte
char VoltageString[24];         // Twenty-four hours' worth of readings, indexed by the hour. The value is the voltage * 10. (e.g. 12.0V is saved as "120")

int  VoltageReading = 0;        // This is the sum of the 8 voltage readings taken, to be averaged and converted to a byte

//////////////////////////////////
//            SETUP             //
//////////////////////////////////

void setup()
{
  // Use the Serial monitor to view time/date output
  // LEAVE ALL THE SERIAL LINES COMMENTED-OUT IN PRODUCTION.
  // They're left here for short-term debugging use ONLY
  //Serial.begin(9600);
  //Serial.println( F(""));
  //Serial.println( F("Hello. I've just booted"));

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

  //Serial.println( F("SRAM said "));
  //Serial.println(MemTest,BIN);
  //Test to see if this is a VIRGIN COLD start, or if the clock is running OK & we have values in the registers?
  // From cold the two alarms will NOT be set (1 in their respective bits)
  if (MemTest & 0x03 == 3)
  {
    //Serial.println( F("HEALTHY"));
    FlashLed(4); //Healthy boot
    interval          = EEPROM.read(MEMInterval);
    ShootDays         = EEPROM.read(MEMShootDays);
    StartHour         = EEPROM.read(MEMStartHour);
    EndHour           = EEPROM.read(MEMEndHour);
    WakePiHour        = EEPROM.read(MEMWakePiHour);
    WakePiDuration    = EEPROM.read(MEMWakePiDuration);

    for (int i = 0; i <= 23; i++)
    {
      // Temperature readings:
      DailyTemps[i] = EEPROM.read(MEM24Temp0 + i);
      //Serial.println( "  Temp[" + String(i) + "] = " + String(DailyTemps[i]));
    }
    //Serial.println( F("Values from EEPROM are: "));
    //Serial.println( "  start hour = " + String(StartHour));
    //Serial.println( "  end hour   = " + String(EndHour));
    //Serial.println( "  interval   = " + String(interval));
    //Serial.println( "  wakePi     = " + String(WakePiHour) + " and run for " + String(WakePiDuration) + " minutes.");
  }
  else
  {
    // This is our first power-up from failure.
    // There's no info in the clock & because of this we can't trust the EEPROM values
    //Serial.println( F("UNHEALTHY"));
    FlashLed(8); //Unhealthy boot
    rtc.set24Hour(); // Force 24-hour mode to be sure (even though that's its default anyway)
    // Default to 12:00:01 pm, January 1, 2018:
    setTimeDate("20180101120001");
    EEPROM.update(MEMShootDays, ShootDays);
    EEPROM.update(MEMStartHour, StartHour);
    EEPROM.update(MEMEndHour, EndHour);
    EEPROM.update(MEMInterval, interval);
    EEPROM.update(MEMWakePiHour, WakePiHour);
    EEPROM.update(MEMWakePiDuration, WakePiDuration);
    EEPROM.update(MEMTempMin, (int8_t)127); //Initialise to extremes, so next pass they'll be overwritten with valid values
    EEPROM.update(MEMTempMax, (int8_t)-128);

    //Initalise the temperature array to dummy values:
    for (int i = 0; i <= 23; i++)
    {
      // TODO: Do we need to initialise the temperature EPROM values here too?
      DailyTemps[i] = (int8_t)-128;
    }
    //Serial.println("Default values burnt to RAM are interval = " + String(interval));
  }

  if (interval > 60)
  {
    shootFastInterval = interval - 60;
  }
  else
  {
    shootFastInterval = 0;
  }

  UpdateTempMinMax("", -1); // Reset or initialise the temperature readings on boot
  
  //Initalise the VM array:
  for (int i = 0; i <= 23; i++)
  {
    #ifdef V_SENSE_PIN
      VoltageString[i] = byte(10); // Flush the array. "10" is our zero value. The offset will be corrected in the Pi.
    #else
      VoltageString[i] = byte(255); // Load the array with a magic number. The Pi will read this as "vm not equipped" and suppress the display.
    #endif
  }
  readVbatteryFlag = true;  // Take a battery reading on boot

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
  //Serial.println(F("Wake Camera\r\n"));

  digitalWrite(WAKE_PIN, HIGH); // Wake the camera up
  DelaymS(400);
  digitalWrite(WAKE_PIN, LOW); //
}


void TakePhoto()
{
  //Serial.println( F("Take Photo\r\n"));
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

  byte tempInterval = interval; //Global 'interval' might also include the offset 'shootFast' values we need to retain and handle carefully
 
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

  if (tempInterval > 60)
  {
    tempInterval = 1; //If shootFast, we set alarm 1 for every minute
  }
 
  do
  {
    nextShot++;
  } while (nextShot % tempInterval != 0);

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

  if (StartHour < EndHour)
  {
    //Normal daytime shoot, or 24hr operation
    //Serial.println("Trad daytime shoot");
    if (nextHour < StartHour)
    {
      //We haven't yet started for the day:
      nextHour = StartHour; //Reset the alarm to restart later today
      nextShot = 0;
    }
    else if (nextHour >= EndHour)
    {
      //We've finished for today:
      nextHour = StartHour; //Reset the alarm to restart next shooting day
      nextShot = 0;
      nextDay++;
    }
    else
    {
      //Serial.println(" - we're in the shooting window. (Daytime shoot)");
    }
  }
  else
  {
    //Shoot through midnight
    //Serial.println("STM");
    if ((nextHour >= EndHour) && (nextHour < StartHour))
    {
        //We haven't yet started for the day:
        //Serial.println(" - we haven't started for the day yet");
        nextHour = StartHour;
        nextShot = 0;
    }
    else
    {
      //Serial.println(" - we're in the shooting window - STM");
    }
  }

  if (nextDay == 8) nextDay = 1; //Correct in case the day has wrapped around the week

  //Run the various tests to determine if we keep shooting or jump to the next shooting day:
  while (true)
  {
    byte yesterday = nextDay - 1;                 //Subtract back to yesterday
    if (yesterday == 0) yesterday = 7;            //Wrap around the week if required
    byte prevShootDay = 0b0000001 << (yesterday); //Sunday = bit 1 to align with clock's day ordering
    byte nextShootDay = 0b0000001 << (nextDay);   //Sunday = bit 1 to align with clock's day ordering

    if (StartHour > EndHour)
    {
      //STM
      //Serial.println("STM in the day calculation");
      if (nextHour < EndHour)
      {
        //It's after midnight, so we've rolled into the next day. Should we be shooting or not?
        //Serial.println(" - today is " + String(nextDay) + ", yesterday was " + String(yesterday) + "\r\n");
        if (prevShootDay & ShootDays)
        {
          //Serial.println(" - yesterday was a shooting day, so our next shot is *today*. Keep shooting\r\n");
          break;
        }
        else
        {
          nextHour = StartHour; // Yesterday wasn't a shooting day, so we won't shoot until the next startHour
          nextShot = 0;
          //Continue - drop to the nextShootDay test below.
        }
      }
    }

    //If we get to here, run this while loop and then break:
    while (!(nextShootDay & ShootDays))
    {
      nextShot = 0; //Next shot isn't today, so reset this to the top of the hour
      nextHour = StartHour; //... and at StartHour
      nextDay++;
      if (nextDay == 8) nextDay = 1;
      nextShootDay = 0b0000001 << (nextDay);
    }
    break;
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
      PiShutdownMinute = rtc.getMinute() + WakePiDuration + 1; // If rtc.secs=59 you're short-changed a minute, so I add a bonus one
      if (PiShutdownMinute >= 60)
      {
        PiShutdownMinute -= 60 ; // So shutdown will be in the NEXT hour. Save this value for later. Alarm2 will be at minute=0
      }
      else
      {
        AlarmMinute = PiShutdownMinute; // Shutdown is in THIS hour. Set this minute as the alarm2 time.
      }
    }
    else
    {
      if (PiShutdownMinute < 60) { AlarmMinute = PiShutdownMinute; } // We're now in the 'next hour' referred to above. Set alarm2
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
  //Serial.println("Timestamp " + now);
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

  //Serial.println("Day = " + String(dayOfWeek));

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
  StartHour = (Validate (StartHour,    incoming.substring(1, 3).toInt(), 00, 23));
  EndHour   = (Validate (EndHour,      incoming.substring(3, 5).toInt(), 01, 24));
  interval  = (Validate (interval,     incoming.substring(5, 7).toInt(), 00, 90));

  if (interval > 60)
  {
    shootFastInterval = interval - 60;
  }
  else
  {
    shootFastInterval = 0;
    shootFastCount    = 0; // Kills any shootFast sequence underway
  }

  EEPROM.update(MEMShootDays,          ShootDays);
  EEPROM.update(MEMStartHour,          StartHour);
  EEPROM.update(MEMEndHour,            EndHour);
  EEPROM.update(MEMInterval,           interval);
  EEPROM.update(MEMShootFastInterval,  shootFastInterval);

  //This is prepared as a string here in preparation for the next time the Pi requests confirmation:
  sprintf(Intervalstring, "%c%02d%02d%02d", ShootDays, StartHour, EndHour, interval);
  //Serial.println("Set interval ends. StartHour = " + String(StartHour) + ", EndHour = " + String(EndHour) + " & interval = " + String(interval));
}


void SetWakePiTime(String NewTimeDuration)
{

  //Serial.println(" - New WakePi time = " + String(NewTimeDuration));
  if (NewTimeDuration.length() != 4) return;

  WakePiHour     = (Validate (WakePiHour,     NewTimeDuration.substring(0, 2).toInt(), 00, 25));
  WakePiDuration = (Validate (WakePiDuration, NewTimeDuration.substring(2, 4).toInt(), 05, 60));

  EEPROM.update(MEMWakePiHour,     WakePiHour);
  EEPROM.update(MEMWakePiDuration, WakePiDuration);

  SetAlarm2(HIGH);
}


int Validate (int CurrentValue, int NewValue, int LowerValue, int UpperValue)
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
void UpdateTempMinMax(String resetOption, int thisHour)
{
  float tempy = rtc.temperature();
  tempy < 0 ? tempy -= 0.5 : tempy += 0.5; // Need to cater for negative temps. Round all numbers away from zero
  int8_t roundedTemp = round(tempy*10)/10.0; // Rounds the temp to a whole digit
  int8_t currentMin;
  int8_t currentMax;
  EEPROM.get(MEMTempMin, currentMin);
  EEPROM.get(MEMTempMax, currentMax);

  if (resetOption == "Min" || roundedTemp  < currentMin)
  {
    EEPROM.update(MEMTempMin, roundedTemp);
    currentMin = roundedTemp;
  }
  if (resetOption == "Max" || roundedTemp  > currentMax)
  {
    EEPROM.update(MEMTempMax, roundedTemp);
    currentMax = roundedTemp;
  }

  //Only update the hour-based readings if we've been called by the Alarm2 handler:
  if (thisHour != -1)
  {
    //Serial.println("Alarm 2 temp read: Hour = " + String(thisHour) + ", temp = " + String(roundedTemp)  + "\r\n");
    DailyTemps[thisHour] = roundedTemp;
    EEPROM.update(MEM24Temp0 + thisHour, roundedTemp); // Back it up to EEPROM
  }

  sprintf(TemperaturesString, "%d,%d,%d", roundedTemp, currentMax, currentMin);
  //Serial.println("Temps [current, max, min]: " + String(TemperaturesString) + "\r\n");
  return;
}


// Called repeatedly at the top of every hour to read the battery voltage
// Loops 8 times, each time reading the battery voltage. On the last loop it averages the values, stores the result in an array, and resets its flags.
void UpdateVoltage()
{
  #ifdef V_SENSE_PIN
    if (VoltageReadingCounter < 8)
    {
      VoltageReading += analogRead(V_SENSE_PIN);
      Serial.println("Voltage read #" + String(VoltageReadingCounter) + " = " + String(VoltageReading));
      VoltageReadingCounter += 1;
      //DelaymS (1000);
    }
    else
    {
      int thisHour = rtc.getHour();
      float averageVolts = VoltageReading / 8;            // Average the 8 different readings
      VoltageReading = (int)((averageVolts * 183) / 1024); // Convert 0-1023 to 0-"180" (18.0) Volts. (We'll add the decimal in the Pi)
      VoltageReading += 10;                                // Add an offset to allow transfer as bytes. (Preventing 0v being NULL is the issue addressed here).
      //Clamp valid voltages to a range of 0-18.0V (even though a reading anywhere near zero isn't possible)
      if ((VoltageReading < 10) || (VoltageReading > 190))
      {
        VoltageReading = 10;
        Serial.println( "YES!! Trapped an invalid voltage read at hour = " + String(thisHour));
      }
      VoltageString[thisHour] = byte(VoltageReading);      // Insert this voltage reading in the array
      //EEPROM.write(MEM24Volt0 + thisHour, byte(VoltageReading));
      Serial.println("Final Voltage read = " + String(VoltageReading) + " Volts");
      //Serial.println("Voltage string     = " + String(VoltageString));
      Serial.println("Voltage string len = " + String(strlen(VoltageString)));
      
      readVbatteryFlag = false;  // OK, all done, reset the flag.
      VoltageReading = 0;
      VoltageReadingCounter = 0; // Reset the counter for next time.
    }
  #else
    readVbatteryFlag = false;    // Nothing to do here. Reset the flag.
  #endif
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
  //Serial.println(" Receive fired. " + String(howMany) + " bytes expected");

  while (Wire.available())
  {
    char c = Wire.read(); // receive byte as a character
    //Discard any incoming nulls:
    if ( c != 0)
    {
      incoming += c;
    }
  }
  //Serial.println("Incoming = >" + incoming + "<");
  if (howMany == 1)
  {
    // These values require a response:
    if (incoming == "0")
    {
      //It wants to know the date:
      rtc.update(); //This updates the registers
      sprintf(sendToPi, "20%02d%02d%02d", rtc.year(), rtc.month(), rtc.date());
    }
    else if (incoming == "1")
    {
      //It wants to know the time:
      sprintf(sendToPi, "%02d%02d%02d", rtc.hour(), rtc.minute(), rtc.second());
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
    else if (incoming == "6")
    {
      //It wants to know my version number:
      sprintf(sendToPi, version);
    }
    else if (incoming == "7")
    {
      //It wants to know the last 24 hours' temp's:
      for (int i = 0; i <= 23; i++)
      {
        sendToPi[i] = DailyTemps[i];
      }
      sendToPi[24] = '\0'; //Perhaps a formality?
    }
    else if (incoming == "8")
    {
      // It wants to know the last 24 hours' voltages:
      for (int i = 0; i <= 23; i++)
      {
         sendToPi[i] = VoltageString[i];
      }
      sendToPi[24] = '\0'; //Perhaps a formality?
    }
    else if (incoming == "9")
    {
      //It wants to know how long until shutdown:
      sprintf(sendToPi, "%02d", PiShutdownMinute);
    }
    else
    {
      //Unknown request:
      sprintf(sendToPi, "Bad request - %d", (int)incoming[0]);
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
  else if (incoming == "EX")
  {
    resetAlarm2Flag = true;
  }
}


// callback for sending data
void sendData()
{
  int sent = Wire.write((byte *) &sendToPi, 32);
  //Serial.println(" - SENT = " + String(sent) + " bytes");
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
  // - as long as shootFastCount > 0 
  // - continuously, whenever the Pi is powered-up
  // ... otherwise we go back to sleep at the end of the loop and wait for the next interrupt

  static unsigned long sfTimerStart;              // This is the time at which the last shootFast photo was taken
 
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
    //Serial.println( F(" - ALARM   fired"));
    printTime();
    rtc.update();
    if (rtc.alarm1())
    {
      //Serial.println( F(" - ALARM 1 fired"));
      todayAsBits = 0b0000001 << (rtc.day()); //Sunday = bit 1 to align with clock's day ordering
      if ((todayAsBits & ShootDays) && (rtc.hour() >= StartHour))
      {
        //So it's a ShootDay and either before midnight on an STM shoot, or otherwise within the duration for a daytime shoot
        TakePhoto();
        if (interval > 60)
        {
          //Serial.println( F(" - shootFast triggered"));
          sfTimerStart = millis(); // Start the timer
          shootFastCount = 60 / (interval - 60);
          shootFastCount -= 1; // Decrement for the one we just took. Elsewhere, loop() will do the rest.
        }
      }
      else if ((StartHour > EndHour) && (rtc.hour() < EndHour))
      {
        //Is it post-midnight on an overnight shoot, and today ISN'T a shooting day, but yesterday was?
        byte yesterdayAsBits = todayAsBits >> 1;
        if (yesterdayAsBits == 0b0000001) yesterdayAsBits = 0b1000000;
        if (yesterdayAsBits & ShootDays)
        {
          TakePhoto();
          if (interval > 60)
          {
            //Serial.println( F(" - shootFast triggered"));
            sfTimerStart = millis(); // Start the timer 
            shootFastCount = 60 / (interval - 60);
            shootFastCount -= 1; // Decrement for the one we just took. Elsewhere, loop() will do the rest.
          }
        }
        else
        {
          //Serial.println( F(" - alarm1 overnight handling says NO GO"));
        }
      }
      else
      {
          //Serial.println( F(" - Nope, the hour/minute might be good, but it's not a shoot day"));
      }
      SetAlarm1(); // Re-set the alarm
    }
    DelaymS(100);
    if (rtc.alarm2())
    {
      //Serial.println( F(" - ALARM 2 fired"));
      if (rtc.minute() == 0)
      {
        UpdateTempMinMax("", rtc.hour());  // Runs at the top of the hour, 24x7
        readVbatteryFlag = HIGH;           // Trigger the battery reading process
      }
      if ((rtc.minute() == 0) && (rtc.hour() == WakePiHour))
      {
        //Serial.println(" -           " + String(rtc.hour()) + ":" + String(rtc.minute()) + "       WAKING the Pi");
        //Serial.println( F(" - WAKING the Pi via ALARM 2. WakePi set TRUE"));
        WakePi = true; //Actioned elsewhere in loop()
      }
      else if ((rtc.minute() == PiShutdownMinute))
      {
        // Safety net: don't want rogue code turning the Pi off if it's meant to be always on
        if (WakePiHour != 25)
        {
          //Serial.println(" - ALARM 2 fired @ PiShutdownMinute " + String(rtc.hour()) + ":" + String(rtc.minute()) + ".");
          //Serial.println( F(" - Initiated a Pi shutdown"));
          digitalWrite(PI_SHUTDOWN, LOW); // Instruct the Pi to shutdown
          PiShutdownMinute = 120;         // Reset to an invalid/magic number.
        }
      }
      SetAlarm2(LOW);
    }
    ALARM = false;
  }

  if (shootFastCount > 0)
  {
    if ((millis() - sfTimerStart) > long(shootFastInterval * 1000))
    {
      sfTimerStart = millis(); // Restart for next shot
      TakePhoto();
      shootFastCount -= 1;
    }
  }
  else
  {
    shootFastCount = 0; // Just in case it's somehow < 0
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
    //Serial.println( F(" - WAKE PI fired"));
    LastRunningState = LOW; // This serves to extend the run timer if the Pi is already running when this fires.
                            // It's both a feature and also a safety-net to make sure the shutdown timer is set.
    digitalWrite(PI_SHUTDOWN, HIGH); // Make sure the shutdown pin is high before we turn it on
    digitalWrite(PI_POWER, HIGH); // Turn the Pi on.
    //Serial.println( F("The Pi has just been powered on"));
    WakePi = false; // We can reset the flag now.
    SLEEP = false;  // We won't sleep while the Pi is on.
  }

  if (resetArduinoFlag == true)
  {
    //Serial.println( F("ResetArduinoFlag set."));
    if (bitRead(PINB, 0) == HIGH) //PI_RUNNING (Pin 8) is read as PORTB bit *0*
    {
      digitalWrite(PI_SHUTDOWN, LOW); // Instruct the Pi to shutdown
      //Serial.println( F(" - Telling the Pi to shutdown"));
    }
    else
    {
      //Serial.println( F(" - Resetting the Arduino"));
      resetArduinoFlag = false;
      digitalWrite(PI_POWER, LOW); // Turn the Pi off. May be redundant, but as softReset is ambiguous, best be on the safe side.
      DelaymS(1000);               // Just to be sure the above has 'taken'
      softReset();
    }
  }

  if (getTempsFlag == true)
  {
    UpdateTempMinMax("", -1);
    getTempsFlag = false;
  }

  if (resetTempMinFlag == true)
  {
    UpdateTempMinMax("Min", -1);
    resetTempMinFlag = false;
  }

  if (resetTempMaxFlag == true)
  {
    UpdateTempMinMax("Max", -1);
    resetTempMaxFlag = false;
  }

  if (readVbatteryFlag == true)
  {
    UpdateVoltage();
  }

  if (resetAlarm2Flag == true)
  {
    SetAlarm2(HIGH);
    resetAlarm2Flag = false;
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
      // This is a rising edge - the Pi's just woken up.
      // Set alarm2 in readiness to put it to sleep:
      //Serial.println("LastRunningState WAS low, and PI_RUNNING went HIGH. The Pi has just woken up");
      SetAlarm2(HIGH);
      LastRunningState = HIGH;
    }
  }


  //By the time we reach this point through the loop we'll have:
  // - taken any photo that's required
  // - serviced any housekeeping alarm
  // - actioned any changes pushed via the Pi
  // ... so now provided: 
  //    - the Pi isn't running, 
  //    - ALARM isn't still set,
  //    - we're not still mid-way through a voltage reading loop
  //   ... we can sleep!

  if ((bitRead(PORTD, PI_POWER) == LOW) && (ALARM == false) && (resetArduinoFlag == false) && (shootFastCount == 0))
  {
    // The Pi is powered-off. It's safe for us to sleep
    //Serial.println( F(" - About to sleep"));
    SLEEP = true;
  }

  if (SLEEP == true)
  {
    //Serial.println( F(" - SLEEP"));
    //Serial.println( F(""));
    //DelaymS(2000); //Only enabled when Debugging, to ensure println messages are written before we sleep.
    SLEEP = false; //Reset the flag BEFORE we power-down, otherwise we risk looping
    bitWrite(PORTD, LED_PIN, LOW); //Make sure the LED's off before going to sleep
    LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF); //SLEEP_FOREVER will only be woken by an IRQ
    // ni-ni!
  }
}
