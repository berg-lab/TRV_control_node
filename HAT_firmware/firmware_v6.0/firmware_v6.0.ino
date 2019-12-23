// Control node wireless data processor v6.0

// Updated on 12/22/2019
// Developed by Akram Ali

#include <RFM69.h>  //  https://github.com/LowPowerLab/RFM69
#include <SPI.h>

// define node parameters
#define NODEID                40 // must be unique for each node on same network (range up to 254, 0 is broadcast)
#define NETWORKID             40
#define GATEWAYID             1
#define GATEWAY_NETWORKID     1
#define ENCRYPTKEY            "Tt-Mh=SQ#dn#JY3_"
#define FREQUENCY             RF69_915MHZ //Match this with the version of your Moteino! (others: RF69_433MHZ, RF69_868MHZ)
#define IS_RFM69HW            //uncomment only for RFM69HW! Leave out if you have RFM69W!
#define LED                   9 // led pin

// define objects
RFM69 radio;

// define other global variables
int setpoint, manual_override, pwm = 0;
char dataPacket[150]; // this is for sending incoming serial data
char data[100];
char _rssi[5];
char _i[4];
unsigned long t;

// global variables for parsing serial data
const byte numChars = 32;
char receivedChars[numChars];
char tempChars[numChars];        // temporary array for use when parsing
char messageFromPC[numChars] = {0};
boolean newData = false;

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
    recvWithStartEndMarkers();
    if (newData == true)
    {
      strcpy(tempChars, receivedChars);
          // this temporary copy is necessary to protect the original data
          //   because strtok() used in parseData() replaces the commas with \0
      parseData();
      newData = false;
      
      readSensors();
      // send datapacket to gateway
      radio.setNetwork(GATEWAY_NETWORKID);
      radio.sendWithRetry(GATEWAYID, dataPacket, strlen(dataPacket));  // send data
      radio.setNetwork(NETWORKID);

      memset(dataPacket, 0, sizeof dataPacket);   // clear array
      Blink(LED,5);
    }


  if (radio.receiveDone())
  {
    int rssi = radio.RSSI;
    int nodeID = radio.SENDERID;
    
    if (radio.DATALEN > 0)
    {
      for (byte i = 0; i < radio.DATALEN; i++)
        data[i] = (char)radio.DATA[i];
    }

    if (radio.ACKRequested())
    {
      radio.sendACK();

      dtostrf(nodeID, 1, 0, _i);
      dtostrf(rssi, 3, 0, _rssi);
      
      strcat(dataPacket, "i:");
      strcat(dataPacket, _i);  // append node ID
      strcat(dataPacket, ",");
      strcat(dataPacket, data);  // append actual data
      strcat(dataPacket, ",r:");
      strcat(dataPacket, _rssi); // append RSSI
      
      Serial.println(dataPacket);
      delay(1);

      memset(data, 0, sizeof data);   // clear array
      memset(dataPacket, 0, sizeof dataPacket);   // clear array
      memset(_rssi, 0, sizeof _rssi);

      Blink(LED,5);
    }
  }

  if((unsigned long)(millis()-t) >= 30000)    // send temp data approximately every 30 secs
  {
    getTemperature();

    // send datapacket to gateway
    int rad_nodeID = NODEID + 4;  // this is radiator node ID
    radio.setAddress(rad_nodeID);   // change node ID
    radio.setNetwork(GATEWAY_NETWORKID);  // change network ID
    radio.sendWithRetry(GATEWAYID, dataPacket, strlen(dataPacket));  // send data
    radio.setAddress(NODEID);
    radio.setNetwork(NETWORKID);

    // merge node ID in this dataPacket
    char serialData[150];
    dtostrf(rad_nodeID, 1, 0, _i);

    serialData[0] = 0;  // first value of dataPacket should be a 0
    strcat(serialData, "i:");
    strcat(serialData, _i);  // append node ID
    strcat(serialData, ",");
    strcat(serialData, dataPacket);
    delay(1);
    
    Serial.println(serialData);
    delay(1);
    
    memset(dataPacket, 0, sizeof dataPacket);   // clear array
    memset(serialData, 0, sizeof serialData);   // clear array
  
    Blink(LED,5);
    t = millis();
  }
}


void getTemperature()
{
  // external temp reading
  float adc = averageADC(A0);
  float R = resistance(adc, 10000); // Replace 10,000 ohm with the actual resistance of the resistor measured using a multimeter (e.g. 9880 ohm)
  float a = steinhart_2(R);  // get temperature from thermistor using the custom Steinhart-hart equation

  // define character arrays for all variables
  char _a[7]="";

  // convert all flaoting point and integer variables into character arrays
  dtostrf(a, 3, 2, _a);   // this function converts float into char array. 3 is minimum width, 2 is decimal precision
  delay(1);

  memset(dataPacket, 0, sizeof dataPacket);   // clear array

  // create datapacket by combining all character arrays into a large character array
  strcat(dataPacket, "a:");
  strcat(dataPacket, _a);
  delay(5);
}


void readSensors()
{
  //setpoint = 0;
  
  // define character arrays for all variables
  char _y[2];
  char _u[2];
  char _w[4];

  // convert all flaoting point and integer variables into character arrays
  dtostrf(setpoint, 1, 0, _y);
  dtostrf(manual_override, 1, 0, _u);
  dtostrf(pwm, 1, 0, _w);
  delay(5);

  memset(dataPacket, 0, sizeof dataPacket);   // clear array
  
  dataPacket[0] = 0;  // first value of dataPacket should be a 0
  // create datapacket by combining all character arrays into a large character array
  strcat(dataPacket, "y:");
  strcat(dataPacket, _y);
  strcat(dataPacket, ",u:");
  strcat(dataPacket, _u);
  strcat(dataPacket, ",w:");
  strcat(dataPacket, _w);
  delay(5);
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


void Blink(byte PIN, int DELAY_MS)
{
  pinMode(PIN, OUTPUT);
  digitalWrite(PIN,HIGH);
  delay(DELAY_MS);
  digitalWrite(PIN,LOW);
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


// Parse Data *****************************************
void parseData() {      // split the data into its parts

    char * strtokIndx; // this is used by strtok() as an index

    strtokIndx = strtok(tempChars,",");      // get the first part - the string
    setpoint = atoi(strtokIndx);     // convert this part to an integer
 
    strtokIndx = strtok(NULL, ","); // this continues where the previous call left off
    manual_override = atoi(strtokIndx);     // convert this part to an integer

    strtokIndx = strtok(NULL, ","); // this continues where the previous call left off
    pwm = atoi(strtokIndx);     // convert this part to an integer
}

// Receive serial data *****************************************
void recvWithStartEndMarkers() {
    static boolean recvInProgress = false;
    static byte ndx = 0;
    char startMarker = '<';
    char endMarker = '>';
    char rc;

    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();

        if (recvInProgress == true) {
            if (rc != endMarker) {
                receivedChars[ndx] = rc;
                ndx++;
                if (ndx >= numChars) {
                    ndx = numChars - 1;
                }
            }
            else {
                receivedChars[ndx] = '\0'; // terminate the string
                recvInProgress = false;
                ndx = 0;
                newData = true;
            }
        }

        else if (rc == startMarker) {
            recvInProgress = true;
        }
    }
}
