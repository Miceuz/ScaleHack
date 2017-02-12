#include "HX711.h"
#include "FilterCascade.h"

String content = "";

HX711 scale;

#define DOUT 9
#define SCK 11

double r = 18.15;

void setup() {
  pinMode(10, OUTPUT);
  digitalWrite(10, LOW);
  pinMode(8, OUTPUT);
  digitalWrite(8, HIGH);
  
  Serial.begin(9600);
  scale.begin(DOUT, SCK);

  //scale.set_scale();
  scale.tare();				        
}

unsigned char heaviness[] = {2,2};
FilterCascade filtered =  FilterCascade(2, heaviness);

void loop() {
  
  Serial.println(filtered.apply(scale.get_units())/r);
  while(Serial.available()) {
    char c = Serial.read();
    if('\n' == c) {
      unsigned int n = content.toInt();
      content = String("");
      if(0 == n) {
        scale.tare();
      } else {
        //scale.set_scale(1);
        double t = scale.get_units(10);
        r = t/n;
        //scale.set_scale(r);
      }
    } else {
      content.concat(c);
    }
  }
}
