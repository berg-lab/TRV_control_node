// Control node wireless data processor v0.5.1

// Updated on 11/6/2018
// Developed by Akram Ali

#include <RFM69.h>  //  https://github.com/LowPowerLab/RFM69
#include <SPI.h>

// define node parameters
#define NODEID                29 // same sa above - must be unique for each node on same network (range up to 254, 255 is used for broadcast)
#define NETWORKID             1
#define GATEWAYID             1
#define GATEWAY_NETWORKID     1
#define ENCRYPTKEY            "Tt-Mh=SQ#dn#JY3_"
#define FREQUENCY             RF69_915MHZ //Match this with the version of your Moteino! (others: RF69_433MHZ, RF69_868MHZ)
#define IS_RFM69HW            //uncomment only for RFM69HW! Leave out if you have RFM69W!
#define LED                   9 // led pin

// define objects
RFM69 radio;

// define other global variables
char dataPacket[100];


void setup()
{
  Serial.begin(115200);

  pinMode(LED, OUTPUT);  // pin 9 controls LED
  
  radio.initialize(FREQUENCY,NODEID,NETWORKID);
#ifdef IS_RFM69HW
  radio.setHighPower(); //uncomment only for RFM69HW!
#endif
  radio.encrypt(ENCRYPTKEY);

  fadeLED();
}

void loop()
{
  if(Serial.available() > 0)
  {
    //char d[60];
    int n = Serial.readBytesUntil('$', dataPacket, 60);
    if(n>0)
      dataPacket[n]='\0';  // terminate string with NULL
    delay(1);
    Serial.println(dataPacket);
    radio.sendWithRetry(GATEWAYID, dataPacket, strlen(dataPacket));  // send data
    delay(1);
    
    memset(dataPacket, 0, sizeof dataPacket);   // clear array
    Blink(LED,5);
  }
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
