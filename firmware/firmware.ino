// Control node wireless data processor

// Updated on 4/24/2018
// Developed by Akram Ali

#include <RFM69.h>  //  https://github.com/LowPowerLab/RFM69
#include <SPI.h>

// define node parameters
#define NODEID        10 // same sa above - must be unique for each node on same network (range up to 254, 255 is used for broadcast)
#define ENCRYPTKEY "Tt-Mh=SQ#dn#JY3_"
#define GATEWAYID     1
#define NETWORKID     101
#define FREQUENCY     RF69_915MHZ //Match this with the version of your Moteino! (others: RF69_433MHZ, RF69_868MHZ)
#define IS_RFM69HW    //uncomment only for RFM69HW! Leave out if you have RFM69W!
#define LED           9 // led pin

// define objects
RFM69 radio;

// define other global variables
int setpoint;
char dataPacket[150];
char data[100];
char _rssi[5];

void setup()
{
  pinMode(10, OUTPUT); // Radio SS pin set as output
  Serial.begin(115200);
  
  radio.initialize(FREQUENCY,NODEID,NETWORKID);
#ifdef IS_RFM69HW
  radio.setHighPower(); //uncomment only for RFM69HW!
#endif
  radio.encrypt(ENCRYPTKEY);
}

void loop()
{
  if(Serial.available() > 0)
  {
    char s = Serial.read();
    setpoint = s - 48;
    readSensors();
  
    Serial.println(dataPacket);
    delay(5);
  
    // send datapacket
    radio.sendWithRetry(GATEWAYID, dataPacket, strlen(dataPacket));  // send data, retry 5 times with delay of 100ms between each retry
    dataPacket[0] = (char)0; // clearing first byte of char array clears the array
  
    digitalWrite(LED, HIGH);
    delay(5);
    digitalWrite(LED, LOW);
  }

  if (radio.receiveDone())
  {
    int rssi = radio.RSSI;

    if (radio.DATALEN > 0)
    {
      for (byte i = 0; i < radio.DATALEN; i++)
        data[i] = (char)radio.DATA[i];
    }

    dtostrf(rssi, 3, 0, _rssi);
    strcat(data, ",r:");
    strcat(data, _rssi);

    if (radio.ACKRequested())
    {
      byte theNodeID = radio.SENDERID;
      radio.sendACK();

      Serial.println(data);
      delay(1);

      memset(data, 0, sizeof data);
      memset(_rssi, 0, sizeof _rssi);

      Blink(LED,5);
    }
  }
}


void readSensors()
{
  //setpoint = 0;
  
  // define character arrays for all variables
  char _i[3];
  char _y[2];

  // convert all flaoting point and integer variables into character arrays
  dtostrf(NODEID, 1, 0, _i);
  dtostrf(setpoint, 1, 0, _y);
  delay(5);

  dataPacket[0] = 0;  // first value of dataPacket should be a 0

  // create datapacket by combining all character arrays into a large character array
  strcat(dataPacket, "i:");
  strcat(dataPacket, _i);
  strcat(dataPacket, ",y:");
  strcat(dataPacket, _y);
  delay(5);
}


void Blink(byte PIN, int DELAY_MS)
{
  pinMode(PIN, OUTPUT);
  digitalWrite(PIN,HIGH);
  delay(DELAY_MS);
  digitalWrite(PIN,LOW);
}
