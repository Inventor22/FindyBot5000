#include <FastLED.h>

#define POWER_SUPPLY_RELAY_PIN PIN_A8
#define PIXEL_PIN PIN_A10      // Data pin connected to the WS2812B strip
#define NUM_LEDS   10    // Number of LEDs in the strip
#define LED_COLOR  CRGB::Red

CRGB leds[NUM_LEDS];

void setAllLEDs(const CRGB &color);

void setup() {
  pinMode(POWER_SUPPLY_RELAY_PIN, OUTPUT);
  digitalWrite(POWER_SUPPLY_RELAY_PIN, true);
  delay(1000);

  FastLED.addLeds<WS2812B, PIXEL_PIN, BGR>(leds, NUM_LEDS);
  FastLED.setBrightness(30);

  setAllLEDs(LED_COLOR);
  FastLED.show();
}

void loop() {
}

void setAllLEDs(const CRGB &color) {
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = color;
  }
}