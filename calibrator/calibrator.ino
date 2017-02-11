#include "HX711.h"

HX711 scale;

#define DOUT 9
#define SCK 11

void setup() {
  pinMode(10, OUTPUT);
  digitalWrite(10, LOW);
  pinMode(8, OUTPUT);
  digitalWrite(8, HIGH);


    
  Serial.begin(115200);
  scale.begin(DOUT, SCK);
  Serial.println("Hello.");
  delay(1000);
  Serial.print("Averaging 100 readings: ");
  Serial.println(scale.get_units(100));
  Serial.println("Entering it as offset, put 5kg object on scale, you have 5 seconds.");
  scale.tare();
  delay(5000);
  Serial.print("Averaging 100 readings: ");
  double w = scale.get_units(100);
  Serial.println(w);
  Serial.print("Scaling factor is:");  
  float s = w/5000;
  Serial.println(s);
  scale.set_scale(s);
  Serial.println("Done calibrating, weiht in grams follows");
}

void loop() {
  Serial.println(scale.get_units(10));
}
