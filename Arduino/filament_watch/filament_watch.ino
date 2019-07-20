#define IN1 2
#define IN2 3

// in future versions this will be stored in EEPROM or flash to will persist after reboot
String ID = "NONE"; // 4 chars - set me as needed

int last_in1;
int last_in2;
int last_code;
long pos = 0;

int directionIncrementer = 1;
bool LoopingMode = false;
int LoopTimer = 1000;

bool ResultTypeMM = false; // false reports raw counter pos, true reports calculated mm traveled (requires WheelDia to be set)
float posScaler = 1.0;
int   DPR = 2400;
float WheelDia = 23.0;

String inputString = "";
bool stringComplete = false;

inline int decode(int in1, int in2)
{
  return (in2 << 1) | (in1 ^ in2);
}

inline void isr_common(int cur_in1, int cur_in2)
{
  int cur_code = decode(cur_in1, cur_in2);

  if (cur_code != last_code)
  {
    if (((cur_code + 1) & 3) == last_code)
      pos += directionIncrementer;
    if (((cur_code - 1) & 3) == last_code)
      pos -= directionIncrementer;

    last_code = cur_code;
  }

  last_in1 = cur_in1;
  last_in2 = cur_in2;
}

void isr1()
{
  int cur_in1 = digitalRead(IN1);
  int cur_in2 = last_in2;
  isr_common(cur_in1, cur_in2);
}

void isr2()
{
  int cur_in1 = last_in1;
  int cur_in2 = digitalRead(IN2);
  isr_common(cur_in1, cur_in2);
}

void setup() {
  // put your setup code here, to run once:
  pinMode(IN1, INPUT_PULLUP);           // set pin to input
  pinMode(IN2, INPUT_PULLUP);           // set pin to input
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  

  last_in1 = digitalRead(IN1);
  last_in2 = digitalRead(IN2);
  last_code = decode(last_in1, last_in2);

  attachInterrupt(0, isr1, CHANGE);
  attachInterrupt(1, isr2, CHANGE);
}

inline float CalcPos()
{
  if (ResultTypeMM)
    return pos * posScaler;
  else
    return pos;
}

void loop() {
  delay(100);
  String ReplyStr = "";

  if (stringComplete)
  {
    // This is is what we'll reply unless overriden below
    ReplyStr = "Set " + inputString;

    if (inputString == "FINDFILAMENTWATCH")
    {
      ReplyStr = "FilamentWatchHere!";
    }
    else if (inputString == "LOOP")
    {
      LoopingMode = true;
    }
    else if (inputString == "STOPLOOP")
    {
      LoopingMode = false;
    }
    else if (inputString == "DIRCWPOSITIVE")
    {
      directionIncrementer = 1;
    }
    else if (inputString == "DIRCCWPOSITIVE")
    {
      directionIncrementer = -1;
    }
    else if (inputString == "GETPOS")
    {
      ReplyStr = "FWPos ";
      ReplyStr = ReplyStr + CalcPos();
      ReplyStr = ReplyStr + " FWPos";
    }
    else if (inputString.startsWith("LOOPTIMEMS:"))
    {
      inputString.replace("LOOPTIMEMS:", "");
      LoopTimer = inputString.toInt();
    }
    else if (inputString.startsWith("SETWHEELDIA:"))
    {
      inputString.replace("SETWHEELDIA:", "");
      WheelDia = inputString.toFloat();

      ResultTypeMM = true;

      float cir = WheelDia * PI;
      posScaler = cir / float(DPR);
      pos = 0;
    }
    else if (inputString.startsWith("SETDPR:"))
    {
      inputString.replace("SETDRP:", "");
      DPR = inputString.toInt();

      float cir = WheelDia * PI;
      posScaler = cir / float(DPR);
      pos = 0;
    }
    else if (inputString == "RESULTTYPEMM")
    {
      ResultTypeMM = true;
      pos = 0;
    }
    else if (inputString == "RESULTTYPERAW")
    {
      ResultTypeMM = false;
      pos = 0;
    }
    else if (inputString == "RESETPOS")
    {
      pos = 0;
    }
    else if (inputString == "GETID")
    {
      ReplyStr = ID;
    }
    else if (inputString == "BLINK")
    {
      pinMode(LED_BUILTIN, OUTPUT);
      for (int i = 0; i < 3; i++)
      {
        digitalWrite(LED_BUILTIN, HIGH);
        delay(300);
        digitalWrite(LED_BUILTIN, LOW);
        delay(300);
      }
    }
    else if (inputString == "HELP")
    {
      Serial.println(F("FindFilamentWatch: produces 'FilamentWatchHere!' reply"));
      Serial.println(F("Loop:              Start sending measured pos every n ms. Set interval with LoopTimeMS"));
      Serial.println(F("StopLoop:          Stops looping"));
      Serial.println(F("LoopTimeMS:[ms]    Sets loop timer interval"));
      Serial.println(F("GetPos:            Gets current position"));
      Serial.println(F("ResultTypeMM       Returned values as mm traveled, and reset mm of travel to 0"));
      Serial.println(F("ResultTypeRaw      Returned values raw position and reset position to 0"));
      Serial.println(F("SetWheelDia:[mm]   Set diameter of the wheel for mm reporting. Also sets mode to ResultTypeMM"));
      Serial.println(F("SetDPR:[mm]        Set pulses per revolution (assuming quadrature encoding). Defaults to 2400"));
      Serial.println(F("DirCWPositive:     Set clockwise rotation positive"));
      Serial.println(F("DirCCWPositive:    Set counter clockwise rotation positive"));
      Serial.println(F("ResetPos:          Set position to 0"));
      Serial.println(F("GetID:             Get the 4 char ID for this device (defualt NONE)"));
      Serial.println(F("Blink:             Flash the LED"));
      ReplyStr = "";
    }
    else
    {
      ReplyStr = "Unrecognized Command:" + inputString;
    }


    if (ReplyStr.length())
      Serial.println(ReplyStr);

    stringComplete = false;
    inputString = "";
  }


  if (LoopingMode)
  {
    // taking out the 100 ms because we always delay 100 ms in this loop
    delay(LoopTimer - 100);

    ReplyStr = "FWPos ";
    ReplyStr = ReplyStr + CalcPos();
    ReplyStr = ReplyStr + " FWPos";

    Serial.println(ReplyStr);
  }

}

void serialEvent()
{
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();

    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n')
    {
      inputString.toUpperCase();
      stringComplete = true;
    }
    else
    {
      // add it to the inputString:
      inputString += inChar;
    }

  }
}
