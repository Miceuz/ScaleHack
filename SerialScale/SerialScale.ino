#include "HX711.h"

String content = "";

HX711 scale;

#define DOUT 9
#define SCK 11

void setup() {
  pinMode(10, OUTPUT);
  digitalWrite(10, LOW);
  pinMode(8, OUTPUT);
  digitalWrite(8, HIGH);
  
  Serial.begin(9600);
  scale.begin(DOUT, SCK);

  scale.set_scale(19.55);
  scale.tare();				        
}

void loop() {
  Serial.println(scale.get_units(10), 1);
  while(Serial.available()) {
    char c = Serial.read();
    if('\n' == c) {
      unsigned int n = content.toInt();
      content = String("");
      if(0 == n) {
        scale.tare();
      } else {
        scale.set_scale(1);
        double t = scale.get_units(10);
        double r = t/n;
        scale.set_scale(r);
      }
    } else {
      content.concat(c);
    }
  }
}
