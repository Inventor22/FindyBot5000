/*
* Project: FindyBot5000
* Description: LED Driver 
* Copyright: Dustin Dobransky
*/

// Libraries
#include "defs.h"
#include "html_colors_array.h"
#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <FastLED_NeoMatrix.h>
#include <FastLED.h>
#include <Framebuffer_GFX.h>

// Constants
#define PIXEL_PIN PIN_A10
#define PIXEL_TYPE WS2812B
#define POWER_SUPPLY_RELAY_PIN PIN_A8

#define LED_ROWS (8+6)
#define LED_COLS (60)
#define LED_COLS_HALF (LED_COLS / 2)
#define PIXEL_COUNT (LED_COLS * LED_ROWS)

// The width in LEDs that a single character spans on the LED matrix
#define LED_MATRIX_CHAR_WIDTH 6

#define ON true
#define OFF false

CRGB leds[PIXEL_COUNT];

FastLED_NeoMatrix *matrix = new FastLED_NeoMatrix(
    leds, 
    LED_COLS, LED_ROWS, // Width & Height, in pixels
    1, 1, // Tile X, Tile Y
    NEO_MATRIX_TOP  + NEO_MATRIX_LEFT +
    NEO_MATRIX_ROWS + NEO_MATRIX_ZIGZAG);

// uint16_t red = matrix->Color(255, 0, 0);
// uint16_t green = matrix->Color(0, 255, 0);
// uint16_t blue = matrix->Color(0, 0, 255);
// uint16_t magenta = matrix->Color(255, 0, 255);
// uint16_t orange = matrix->Color(255, 165, 0);
// uint16_t cyan = matrix->Color(0, 255, 255);
// uint16_t purple = matrix->Color(128,0,128);
// uint16_t white = matrix->Color(255, 255, 255);

// const CRGB::HTMLColorCode colors[] = {
//     CRGB::AliceBlue,
//     CRGB::Amethyst,
//     CRGB::AntiqueWhite
// };

// CRGB::HTMLColorCode

int r(int minRand, int maxRand);

int colorSetIndex;
CRGB::HTMLColorCode *colors;
uint8_t colorCount;

int scrollPosition = matrix->width();
int scrollCount = 0;

String text = "H I ";
int textLength = 0;
int sRow = 0, sCol = 0;
bool sSet = false;

bool enableDisplay = false;
bool enableTextScrolling = false;
bool enableDebugging = true;

// Method definitions
void iterateColorThemes();
uint16_t getGradientColor(CRGB::HTMLColorCode col0, CRGB::HTMLColorCode col1, float value);
uint16_t gradientBetween(CRGB::HTMLColorCode col0, CRGB::HTMLColorCode col1, float value);
uint16_t getGreenRedValue(float value);
void gradientTest();
void welcome(const char* data);
void setDisplay(const char *data);
void setDisplay(bool state);
void setBrightness(const char *data);
void setDebugging(const char *data);
void setScrollText(const char *data);
void setStateFromText(bool& variable, const char *onOffText);
void temp();
float normalize(float value, float start, float end);
void showAllBoxesResponseHandler();
void dispayItemNotFound();
void lightBox(int row, int col, uint16_t color);
void lightBoxes(int msDelay);
uint32_t Wheel(uint8_t WheelPos);

// Program
void setup()
{
  //delay(1000);

  Serial.begin(115200);
  while (!Serial);
  
  Serial.println("FindyBot5000");

  // Start FindyBot5000 with the display off
  pinMode(POWER_SUPPLY_RELAY_PIN, OUTPUT);
  digitalWrite(POWER_SUPPLY_RELAY_PIN, OFF);
  delay(1000);

  textLength = text.length();

  FastLED.addLeds<NEOPIXEL, PIXEL_PIN>(leds, PIXEL_COUNT); 
  matrix->begin();
  matrix->setTextWrap(false);
  matrix->setBrightness(30);
  matrix->setTextColor(matrix->Color24to16(CRGB::BlueViolet));

  setDisplay(ON);

  //matrix->fillScreen(CRGB::Green);
  matrix->show();

  colorSetIndex = 0;
  colors = const_cast<CRGB::HTMLColorCode*>(colorSets[colorSetIndex]);
  colorCount = colorSetSizes[colorSetIndex];

  //gradientTest();
  //lightBoxes(0);
}

void loop()
{
  if (!enableDisplay) return;

  iterateColorThemes();
}

void iterateColorThemes() {
  for (int i = 0; i < numColorSets; i++) {
      Serial.println(i);
      colorSetIndex = i; // r(0, numColorSets-1);
      colors = const_cast<CRGB::HTMLColorCode*>(colorSets[colorSetIndex]);
      colorCount = colorSetSizes[colorSetIndex];
      lightBoxes(0);
      delay(2000);
      matrix->clear();
  }
}

// weight = 0 -> col0, weight = 0.5 -> 50/50 col0/col1, weight = 1 -> col1
uint16_t getGradientColor(CRGB::HTMLColorCode color0, CRGB::HTMLColorCode color1, float value)
{
  uint16_t col0 = matrix->Color24to16(color0);
  uint16_t col1 = matrix->Color24to16(color1);

  uint8_t red = 0, green = 0, blue = 0;
  uint8_t r = (col0 & 0xF800) >> 8;
  uint8_t g = (col0 & 0x07E0) >> 3;
  uint8_t b = (col0 & 0x1F) << 3;
  // r = (r * 255) / 31;
  // g = (g * 255) / 63;
  // b = (b * 255) / 31;

  if (r > 0) red = r;
  if (g > 0) green = g;
  if (b > 0) blue = b;

  r = (col1 & 0xF800) >> 8;
  g = (col1 & 0x07E0) >> 3;
  b = (col1 & 0x1F) << 3;

  if (r > 0) red = r;
  if (g > 0) green = g;
  if (b > 0) blue = b;

  if (red & blue) {
    red = value <= 0.5 ? 255 : (255 - 255*(value-0.5)*2);
    blue = value <= 0.5 ? 255 * (value*2) : 255;
  }
  else if (red & green) {
    red = value <= 0.5 ? 255 : (255 - 255*(value-0.5)*2);
    green = value <= 0.5 ? 255 * (value*2) : 255;
  } else { // green & blue
    green = value <= 0.5 ? 255 : (255 - 255*(value-0.5)*2);
    blue = value <= 0.5 ? 255 * (value*2) : 255;
  }
  return matrix->Color(red, green, blue);
}

uint16_t gradientBetween(CRGB::HTMLColorCode color0, CRGB::HTMLColorCode color1, float value)
{
  uint16_t col0 = matrix->Color24to16(color0);
  uint16_t col1 = matrix->Color24to16(color1);

  uint8_t r0 = (col0 & 0xF800) >> 8;
  uint8_t g0 = (col0 & 0x07E0) >> 3;
  uint8_t b0 = (col0 & 0x1F) << 3;
  r0 = (r0 * 255) / 31;
  g0 = (g0 * 255) / 63;
  b0 = (b0 * 255) / 31;

  uint8_t r1 = (col1 & 0xF800) >> 8;
  uint8_t g1 = (col1 & 0x07E0) >> 3;
  uint8_t b1 = (col1 & 0x1F) << 3;
  r1 = (r1 * 255) / 31;
  g1 = (g1 * 255) / 63;
  b1 = (b1 * 255) / 31;

  // Linearly interpolate values
  // uint8_t red = (1.0-value) * r0 + value * r1 + 0.5;
  // uint8_t green = (1.0-value) * g0 + value * g1 + 0.5;
  // uint8_t blue = (1.0-value) * b0 + value * b1 + 0.5;

  uint8_t red = (r1-r0) * value + r0;
  uint8_t green = (g1-g0) * value + g0;
  uint8_t blue = (b1-b0) * value + b0;

  return matrix->Color(red, green, blue);
}

// 0.0 = Red, 0.5 = Yellow, 1.0 = Green
uint16_t getGreenRedValue(float value)
{
  int red = value <= 0.5 ? 255 : (255 - 255*(value-0.5)*2);
  int green = value <= 0.5 ? 255 * (value*2) : 255;
  return matrix->Color(red, green, 0);
}

void gradientTest()
{
  int row = 0;

  matrix->fillScreen(0);

  for (int i = 0; i < LED_COLS; i++)
  {
    int red = min(255 * (((float)i)/LED_COLS_HALF), 255);
    int green = (i < LED_COLS_HALF) ? 255 : (255 - 255*(((float)(i - LED_COLS_HALF))/LED_COLS_HALF));
    matrix->drawPixel(i, row, matrix->Color(red, 0, 0));
    matrix->drawPixel(i, row+1, matrix->Color(0, green, 0));
    matrix->drawPixel(i, row+2, matrix->Color(red, green, 0));
  }

  for (int i = 0; i < LED_COLS; i++)
  {
    matrix->drawPixel(i, row+3, getGreenRedValue(((float)i)/LED_COLS));
  }

  for (int i = 0; i < LED_COLS; i++)
  {
    matrix->drawPixel(i, row+4, getGradientColor(CRGB::Green, CRGB::Blue, ((float)i)/LED_COLS));
    matrix->drawPixel(i, row+5, gradientBetween(CRGB::Green, CRGB::Blue, ((float)i)/LED_COLS));
    matrix->drawPixel(i, row+6, getGradientColor(CRGB::Blue, CRGB::Red, ((float)i)/LED_COLS));
    matrix->drawPixel(i, row+7, gradientBetween(CRGB::Red, CRGB::Blue, ((float)i)/LED_COLS));

    matrix->drawPixel(i, row+8, getGradientColor(CRGB::Red, CRGB::Green, ((float)i)/LED_COLS));
    matrix->drawPixel(i, row+9, gradientBetween(CRGB::Red, CRGB::Green, ((float)i)/LED_COLS));

    matrix->drawPixel(i, row+10, getGradientColor(CRGB::Cyan, CRGB::Orange, ((float)i)/LED_COLS));
    matrix->drawPixel(i, row+11, gradientBetween(CRGB::Cyan, CRGB::Orange, ((float)i)/LED_COLS));
    matrix->drawPixel(i, row+12, gradientBetween(CRGB::Purple, CRGB::Orange, ((float)i)/LED_COLS));
    matrix->drawPixel(i, row+13, gradientBetween(CRGB::White, CRGB::Blue, ((float)i)/LED_COLS));
  }

  matrix->show();

  delay(1000);
}

void welcome(const char* data)
{
  if (data == NULL) return;
  //
  // char buff[strlen(data) * 2 + 1]
  // for(int i = 0; i < strlen(data); i++)
  // {
  //   char c = data[i] <= 'Z' ? data[i] : data[i] - ('a'-'A');
  //   buff[i] = c;
  //   buff[i+1] = ' ';
  // }

  String s(data);
  s.toUpperCase();
  text = "W E L C O M E  ";

  for(uint8_t i = 0; i < s.length(); i++) {
    text += ' ';
    text += s[i];
  }

  textLength = text.length();
  enableTextScrolling = true;
  setDisplay(ON);
}

// Turn the LED matrix power supply relay on or off
void setDisplay(const char *data)
{
  if (data == NULL) return;

  if (strstr(data, "on")) {
    setDisplay(true);
  } else if (strstr(data, "off")) {
    setDisplay(false);
  }
}

// Set the brightness of the LED matrix, from 1 to 100, inclusive
void setBrightness(const char *data)
{
  if (data == NULL) return;

  String brightnessText = data;
  int brightness = brightnessText.toInt();

  if (0 < brightness && brightness <= 100) {
    matrix->setBrightness(map(brightness, 0, 100, 0, 255));
    matrix->show();
  }
}

void setDebugging(const char *data)
{
  setStateFromText(enableDebugging, data);
}

void setScrollText(const char *data)
{
  setStateFromText(enableTextScrolling, data);
}

void setStateFromText(bool& variable, const char *onOffText)
{
  if (strcmp(onOffText, "on") == 0) {
    variable = true;
  }
  else if (strcmp(onOffText, "off") == 0) {
    variable = false;
  }
}

// Normalize a number between a specific range.
// ex: normalize(0.8, 0.5, 1.0) => .8 is 3/5 between range,
// function returns 3/5 => 0.6
float normalize(float value, float start, float end)
{
    if (start == end) return value;
    return (value - start) / (end - start);
}


/* =============== HELPER FUNCTIONS =============== */

void lightBox(int row, int col, uint16_t color)
{
  //  if (!((0 <= row && row < 8 && 0 <= col && col < 16)
  //     || (8 <= row && row < 14 && 0 <= col && col < 8))) return;

  int ledCount = 0;
  int ledOffset = 0;

  if (row < 8 && col < 16) {
    ledCount = boxLedWidthByColumnTop[col];
    ledOffset = boxLedOffsetByColumnTop[col];
  } else if (row < 16 && col < 8) {
    ledCount = boxLedWidthByColumnBottom[col];
    ledOffset = boxLedOffsetByColumnBottom[col];
  } else {
    Serial.print(F("Invalid. Row: "));
    Serial.print(row);
    Serial.print(F(", Col: "));
    Serial.println(col);
    return;
  }

  //Serial.printlnf("row: %d, col: %d, count: %d, offset: %d", row, col, ledCount, ledOffset);

  //matrix->fillScreen(0);

  matrix->drawFastHLine(ledOffset, row, ledCount, color);

  // for (int i = 0; i < ledCount; i++) {
  //   matrix->drawPixel(ledOffset + i, row, color);
  // }

  matrix->show();
}

void setDisplay(bool state)
{
  if (enableDisplay == state) return;

  if (state) {
    digitalWrite(POWER_SUPPLY_RELAY_PIN, ON);
    // Give the power supply a moment to warm up if it was turned off
    // Datasheet suggests 20-50ms warm up time to support full load
    delay(250);
  } else {
    digitalWrite(POWER_SUPPLY_RELAY_PIN, OFF);
  }

  enableDisplay = state;
}

/********** TESTING FUNCTIONS **********/

// Light each led-mapped box on the organizer one by one
void lightBoxes(int msDelay)
{
  for (int row = 0; row < 8; row++) {
    for (int col = 0; col < 16; col++) {
      lightBox(row, col, matrix->Color24to16(colors[r(0, colorCount-1)]));
      if (msDelay > 0)
      {
        delay(msDelay);
      }
    }
  }

  for (int row = 8; row < 14; row++) {
    for (int col = 0; col < 8; col++) {
      lightBox(row, col, matrix->Color24to16(colors[r(0, colorCount-1)]));
      if (msDelay > 0)
      {
        delay(msDelay);
      }
    }
  }

  matrix->show();
}

// Generate a random number between minRand and maxRand
int r(int minRand, int maxRand)
{
  return rand() % (maxRand-minRand+1) + minRand;
}
