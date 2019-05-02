// Control node wireless data processor v0.5

// Updated on 11/1/2018
// Developed by Akram Ali

#include <RFM69.h>  //  https://github.com/LowPowerLab/RFM69
#include <RFM69_ATC.h>
#include <SPI.h>

// define node parameters
#define NODEID                10// same sa above - must be unique for each node on same network (range up to 254, 255 is used for broadcast)
#define NETWORKID             10
#define GATEWAYID             1
#define GATEWAY_NETWORKID     1
#define ENCRYPTKEY            "Tt-Mh=SQ#dn#JY3_"
#define FREQUENCY             RF69_915MHZ //Match this with the version of your Moteino! (others: RF69_433MHZ, RF69_868MHZ)
#define IS_RFM69HW              //uncomment only for RFM69HW! Leave out if you have RFM69W!
#define LED                   9 // led pin

// define objects
//RFM69 radio;
RFM69_ATC radio;
char d[64];
int n = 0;
unsigned long t;

// define other global variables
int setpoint;
char dataPacket[150];
char data[100];
char _rssi[5];
String serialdata;

void setup()
{
  pinMode(10, OUTPUT); // Radio SS pin set as output
  Serial.begin(115200);
  fadeLED();
  
  radio.initialize(FREQUENCY,NODEID,NETWORKID);
#ifdef IS_RFM69HW
  radio.setHighPower(); //uncomment only for RFM69HW!
#endif
  radio.encrypt(ENCRYPTKEY);
  
  t = millis();
}

void loop()
{
  if(Serial.available() > 0)    // check if there is serial data
  {
    while(Serial.available())
    {
      char x = Serial.read();
      if (x != '!')
      {
        dataPacket[n] = x;
        n++;
      }
      else
      {
        n=0;
        radio.setNetwork(GATEWAY_NETWORKID);
        radio.sendWithRetry(GATEWAYID, dataPacket, strlen(dataPacket));  // send data, retry 5 times with delay of 100ms between each retry
        radio.setNetwork(NETWORKID);
        
        memset(dataPacket, 0, sizeof dataPacket);   // clear array
        
        digitalWrite(LED, HIGH);
        delay(5);
        digitalWrite(LED, LOW);
        break;
      }
    }
    
//    Serial.readBytes(dataPacket, n);
//    char s = Serial.read();
//    setpoint = s - 48;
//    readSensors();
//    serialdata = Serial.readString();   // kind of slow -- takes about 1 second
//    serialdata.toCharArray(dataPacket, sizeof(dataPacket));   // convert to char array
//    Serial.println(dataPacket);
    
    // send datapacket
//    radio.setNetwork(GATEWAY_NETWORKID);
//    radio.sendWithRetry(GATEWAYID, dataPacket, strlen(dataPacket));  // send data, retry 5 times with delay of 100ms between each retry
//    radio.setNetwork(NETWORKID);
//    dataPacket[0] = (char)0; // clearing first byte of char array clears the array
//    
//    digitalWrite(LED, HIGH);
//    delay(5);
//    digitalWrite(LED, LOW);
  }

  if (radio.receiveDone())
  {
    int rssi = radio.RSSI;

    if (radio.DATALEN > 0)
    {
      for (byte i = 0; i < radio.DATALEN; i++)
        data[i] = (char)radio.DATA[i];
    }

//    dtostrf(rssi, 3, 0, _rssi);
//    strcat(data, ",r:");
//    strcat(data, _rssi);

    if (radio.ACKRequested())
    {
      byte theNodeID = radio.SENDERID;
      radio.sendACK();

      Serial.println(data);
      delay(1);

      Blink(LED,5);

      memset(data, 0, sizeof data);
      memset(_rssi, 0, sizeof _rssi);
    }
  }
  
  if((unsigned long)(millis()-t) >= 30000)    // send data approximately every 30 secs
  {
    readSensors();
    Serial.println(dataPacket);
    delay(1);

    Blink(LED,5);
    memset(dataPacket, 0, sizeof dataPacket);   // clear array
    t = millis();
  }
}


void readSensors()
{
  // external temp reading
  float adc = averageADC(A0);
  float R = resistance(adc, 10000); // Replace 10,000 ohm with the actual resistance of the resistor measured using a multimeter (e.g. 9880 ohm)
  float a = steinhart_2(R);  // get temperature from thermistor using the custom Steinhart-hart equation

  // define character arrays for all variables
  char _i[3]="";
  char _a[7]="";

  // convert all flaoting point and integer variables into character arrays
  int _nodeID = (int)NODEID + 4;
  dtostrf(_nodeID, 1, 0, _i);
  dtostrf(a, 3, 2, _a);
  delay(5);

  memset(dataPacket, 0, sizeof dataPacket);   // clear array
  //dataPacket[0] = 0;  // first value of dataPacket should be a 0

  // create datapacket by combining all character arrays into a large character array
  strcat(dataPacket, "i:");
  strcat(dataPacket, _i);
  strcat(dataPacket, ",a:");
  strcat(dataPacket, _a);
  delay(5);
}


void Blink(byte PIN, int DELAY_MS)
{
  pinMode(PIN, OUTPUT);
  digitalWrite(PIN,HIGH);
  delay(DELAY_MS);
  digitalWrite(PIN,LOW);
}


// Averaging ADC values to counter noise in readings  *********************************************
float averageADC(int pin)
{
  float sum=0.0;
  for(int i=0;i<5;i++)
  {
     sum = sum + analogRead(pin);
  }
  float average = sum/5.0;
  return average;
}

// Get resistance ****************************************************************
float resistance(float adc, int true_R)
{
  float R = true_R/(1023.0/adc-1.0);   // convert 10-bit reading into resistance
//  float ADCvalue = adc*(8.192/3.3);  // Vcc = 8.192 on GAIN_ONE setting, Arduino Vcc = 3.3V in this case
//  float R = 10000/(65535/ADCvalue-1);  // 65535 refers to 16-bit number
  return R;
}


// Get temperature from Steinhart equation (10K Precision Epoxy Thermistor - 3950 NTC) *****************
float steinhart_2(float R)
{
  float steinhart;
  steinhart = R / 10000;     // (R/Ro)
  steinhart = log(steinhart);                  // ln(R/Ro)
  steinhart /= 3950.0;                   // 1/B * ln(R/Ro)
  steinhart += 1.0 / (25.0 + 273.15); // + (1/To)
  steinhart = 1.0 / steinhart;                 // Invert
  steinhart -= 273.15;                         // convert to C

  return steinhart;
}


// Fade LED *****************************************
void fadeLED()
{
  int brightness = 0;
  int fadeAmount = 5;
  for(int i=0; i<510; i=i+5)  // 255 is max analog value, 255 * 2 = 510
  {
    analogWrite(LED, brightness);  // pin 9 is LED
  
    // change the brightness for next time through the loop:
    brightness = brightness + fadeAmount;  // increment brightness level by 5 each time (0 is lowest, 255 is highest)
  
    // reverse the direction of the fading at the ends of the fade:
    if (brightness <= 0 || brightness >= 255)
    {
      fadeAmount = -fadeAmount;
    }
    // wait for 20-30 milliseconds to see the dimming effect
    delay(10);
  }
  digitalWrite(LED, LOW); // switch LED off at the end of fade
}

// bruh
