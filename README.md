#Scale hack

##Rationale
Electornic scales could be bought online for several bucks, but any scales that could be connected to a computer is a lot more expensive. The idea of this project is to create a compact and cheap solution that could be used to hack any conventional consumer-grade scales to make them connected. 

##Solution

 * [HX711](http://www.ebay.com/itm/HX711-Weighing-Sensor-Dual-Channel-24-Bit-Precision-A-D-Module-Pressure-Sensor-/161264280835) - a 24 bit delta sigma ADC with integrated instrumentation amplifier is a chip specifically designed for digitising grain-gauge bridges.
 * A goto solution for any quick and dirty hack - an Arduino clone sourced from ebay.
 * Arduino library used: https://github.com/bogde/HX711
 * HC-05 Bluetooth dongle of the same origin

###Cost analysis

Component | Cost 
----------|---------
HX711     | $0.99
Arduino Nano | $2.73
HC-05 | $0.76
*Total* | $4.48

