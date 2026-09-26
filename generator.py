# -*- coding: utf-8 -*-
"""แปลงคำสั่งภาษาไทยเป็นโค้ด MicroPython (หรือ C++ สำหรับ Arduino รุ่นที่รัน Python ไม่ได้)

ทำงานแบบ "แม่แบบที่ครูตรวจสอบแล้ว" ใช้ได้โดยไม่ต้องต่ออินเทอร์เน็ต
ผลลัพธ์รวม: โค้ด แผนการต่อสาย คำเตือน และคำอธิบายภาษาไทย
"""
import re
from dataclasses import dataclass, field

# ค่าเงื่อนไขเริ่มต้น ถ้าผู้ใช้ไม่ได้บอกตัวเลข
DEFAULT_RULES = {
    "distance_cm": ("<", 20), "light": ("<", 30), "soil": ("<", 30), "gas": (">", 50),
    "temp_c": (">", 30), "humidity": (">", 80), "sound": (">", 60), "water": (">", 70),
    "touch_value": ("<", 200), "pot": (">", 50), "rain": (">", 30), "joy_x": (">", 70),
    "accel_x": (">", 0.5), "force": (">", 30), "weight_g": (">", 100),
    "ph": ("<", 5.5), "distance_mm": ("<", 200), "ir_distance_cm": ("<", 20), "obj_temp_c": (">", 37.5),
    "bpm": (">", 100), "ecg": (">", 70), "alpha1": (">", 2), "red": (">", 150),
}
DISTANCE_KEYS = ("distance_cm", "distance_mm", "ir_distance_cm")   # ค่า 0 หรือติดลบ = วัดไม่ได้
OP_WORDS = [
    (r"น้อยกว่าหรือเท่ากับ|<=", "<="), (r"มากกว่าหรือเท่ากับ|>=", ">="),
    (r"น้อยกว่า|ต่ำกว่า|ไม่ถึง|ใกล้กว่า|<", "<"), (r"มากกว่า|สูงกว่า|เกิน|ไกลกว่า|>", ">"),
]
LESS_HINTS = ["ใกล้", "มืด", "แห้ง", "ต่ำ", "น้อย"]


@dataclass
class Result:
    code: str = ""
    language: str = "micropython"
    wiring: list = field(default_factory=list)      # dict(comp, comp_pin, board_pin, kind, pin)
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    explanation: list = field(default_factory=list)
    components: list = field(default_factory=list)
    assigned: dict = field(default_factory=dict)    # comp_id -> {role: pin}
    keys: list = field(default_factory=list)        # ชื่อค่าที่บอร์ดจะ print ออกมา
    rule: dict = None                                # เงื่อนไขสำหรับโหมดจำลอง


# ------------------------------------------------------------------ ตัวช่วยอ่านตัวเลข
def extract_time_ms(text, default=1000):
    m = re.search(r"(\d+(?:\.\d+)?)\s*วินาที", text)
    if m:
        return int(float(m.group(1)) * 1000)
    m = re.search(r"(\d+)\s*(ms|มิลลิวินาที)", text)
    if m:
        return int(m.group(1))
    return default


def extract_angle(text, default=90):
    m = re.search(r"(\d+)\s*(องศา|degree|degrees|°)", text)
    if m:
        return max(0, min(180, int(m.group(1))))
    return default


def extract_rule_number(text):
    for pattern, op in OP_WORDS:
        m = re.search(r"(?:%s)\s*(-?\d+(?:\.\d+)?)" % pattern, text)
        if m:
            v = float(m.group(1))
            return op, int(v) if v.is_integer() else v
    return None, None


def pin_literal(p):
    return '"%s"' % p if isinstance(p, str) else str(p)


def board_pin_label(board, p):
    fam = board["family"]
    if isinstance(p, str):
        return p
    if fam == "rp2":
        return "GP%d" % p
    if fam == "avr":
        return "D%d" % p
    lbl = "GPIO%d" % p
    d = board.get("pin_labels", {}).get(str(p)) or board.get("pin_labels", {}).get(p)
    return "%s (%s)" % (lbl, d) if d else lbl


def power_label(board, kind):
    if kind == "gnd":
        return "GND"
    if kind == "power3":
        return "3V3" if board["family"] != "avr" else "3.3V"
    fam = board["family"]
    if fam == "avr":
        return "5V"
    if fam == "rp2":
        return "VBUS (5V)" if board.get("has_5v_pin") else "3V3"
    return "VIN (5V)" if board.get("has_5v_pin") else "3V3"


# ------------------------------------------------------------------ ตัวสร้างโค้ดหลัก
class CodeGenerator:
    def __init__(self, kb):
        self.kb = kb

    # ---------- วางแผนอุปกรณ์และขา (ใช้ทั้งโหมดแม่แบบและโหมด AI)
    def plan(self, command, board_id):
        board = self.kb.board_by_id[board_id]
        text = command.lower().strip()
        res = Result()
        found = self.kb.detect(text)
        # "วัดน้ำหนักด้วย FSR402" -> ใช้ FSR ตัวเดียว ไม่เพิ่ม HX711 ให้เอง
        ids = [c["id"] for c, _ in found]
        if "fsr402" in ids and "hx711" in ids and not any(k in text for k in ("hx711", "load cell", "loadcell", "โหลดเซล")):
            found = [(c, i) for c, i in found if c["id"] != "hx711"]
            res.warnings.append("FSR402 วัดได้แค่แรงกดโดยประมาณ ไม่ใช่น้ำหนักเป็นกรัม ถ้าต้องการชั่งจริงให้พิมพ์ \"ชั่งน้ำหนักด้วย HX711\"")
        res.components = [c for c, _ in found]
        if board["family"] == "microbit":
            res.errors.append("micro:bit ใช้ MicroPython แบบเฉพาะ แนะนำให้เขียนที่ python.microbit.org")
            return board, text, res
        if not res.components:
            return board, text, res

        # แบ่งข้อความเป็นช่วงของแต่ละอุปกรณ์ เพื่ออ่านเลขขาที่ผู้ใช้ระบุ
        spans = []
        for i, (c, pos) in enumerate(found):
            end = found[i + 1][1] if i + 1 < len(found) else len(text)
            spans.append((c, text[pos:end]))

        used = set()
        explicit = {}
        for c, seg in spans:
            ex = {}
            for role, num in re.findall(r"\b(trig|echo|in1|in2|ena|sda|scl|x|y)\s*(?:ขา|pin|gpio|gp)?\s*=?\s*(\d+)", seg):
                ex[role.upper()] = int(num)
            generic = re.findall(r"(?:ขา|pin|gpio|พิน|gp)\s*(\d+)", seg)
            analog = re.findall(r"\b(a[0-5])\b", seg)
            sig_roles = [p["role"] for p in c["pins"] if p["kind"] == "signal" and p["role"] not in ex]
            nums = [int(n) for n in generic] + [a.upper() for a in analog]
            for role, n in zip(sig_roles, nums):
                ex[role] = n
            explicit[c["id"]] = ex
            used.update(v for v in ex.values())

        onboard = "บนบอร์ด" in text
        for c in res.components:
            roles = {}
            for p in c["pins"]:
                if p["kind"] != "signal":
                    continue
                need, role = p["need"], p["role"]
                if role in explicit[c["id"]]:
                    pin = explicit[c["id"]][role]
                elif need == "i2c_sda":
                    pin = board["i2c"]["sda"] if board.get("i2c") else None
                elif need == "i2c_scl":
                    pin = board["i2c"]["scl"] if board.get("i2c") else None
                elif c["id"] == "led" and onboard and board.get("led") is not None:
                    pin = board["led"]
                else:
                    pool = board["pools"].get(need) or board["pools"].get("out" if need == "pwm" else "inp", [])
                    pin = next((x for x in pool if x not in used), None)
                    if pin is None:
                        res.errors.append("ขาของบอร์ด %s ไม่พอสำหรับ %s" % (board["name"], c["name_th"]))
                        continue
                if need not in ("i2c_sda", "i2c_scl"):
                    used.add(pin)
                roles[role] = pin
            res.assigned[c["id"]] = roles

        # แผนการต่อสาย
        for c in res.components:
            is_onboard_led = c["id"] == "led" and onboard and res.assigned["led"].get("SIG") == board.get("led")
            if is_onboard_led:
                res.explanation.append("ใช้ไฟ LED บนบอร์ด ไม่ต้องต่อสาย")
                continue
            for p in c["pins"]:
                if p["kind"] == "signal":
                    pin = res.assigned[c["id"]].get(p["role"])
                    if pin is None:
                        continue
                    res.wiring.append(dict(comp=c["id"], comp_name=c["name_en"], comp_pin=p["label"],
                                           board_pin=board_pin_label(board, pin), kind="signal", pin=pin))
                else:
                    kind = p["kind"]
                    if kind == "power5" and board["logic_v"] < 5 and not board.get("has_5v_pin"):
                        res.warnings.append("บอร์ดนี้ไม่มีขาจ่าย 5V: %s ต้องใช้แหล่งจ่ายไฟแยก" % c["name_th"])
                    res.wiring.append(dict(comp=c["id"], comp_name=c["name_en"], comp_pin=p["label"],
                                           board_pin=power_label(board, kind), kind=kind, pin=None))
            for w in c.get("warnings", []):
                if "3.3V" in w or "ESP32" in w:
                    if board["logic_v"] < 5:
                        res.warnings.append("%s: %s" % (c["name_en"], w))
                else:
                    res.warnings.append("%s: %s" % (c["name_en"], w))
        self.validate_plan(board, res)
        return board, text, res

    # ---------- ตรวจขาตามกฎของบอร์ด
    def validate_plan(self, board, res):
        if board["family"] == "avr":
            return
        adc_count = 0
        for c in res.components:
            for p in c["pins"]:
                if p["kind"] != "signal":
                    continue
                if p["need"] == "adc" and board["family"] == "esp8266":
                    adc_count += 1
                pin = res.assigned.get(c["id"], {}).get(p["role"])
                if pin is None or isinstance(pin, str):
                    continue
                name = "%s ขา %s" % (c["name_en"], p["label"])
                lbl = board_pin_label(board, pin)
                if pin in board.get("forbidden_list", []):
                    res.errors.append("%s ต่อกับ %s ไม่ได้: ขานี้ใช้กับหน่วยความจำภายในบอร์ด" % (name, lbl))
                elif board.get("valid") and pin not in board["valid"]:
                    res.errors.append("%s: บอร์ด %s ไม่มีขา %s" % (name, board["name"], lbl))
                if p["need"] in ("out", "pwm") and pin in board.get("input_only", []):
                    res.errors.append("%s เป็นขารับข้อมูลอย่างเดียว ใช้ส่งสัญญาณออกไป %s ไม่ได้" % (lbl, name))
                if p["need"] == "adc":
                    if pin not in board["pools"].get("adc", []):
                        res.errors.append("%s อ่านค่าแอนะล็อกไม่ได้ %s ต้องใช้ขา ADC เช่น %s" %
                                          (lbl, name, ", ".join(board_pin_label(board, x) for x in board["pools"]["adc"][:4])))
                    elif pin in board.get("adc2", []):
                        res.warnings.append("%s เป็นขา ADC2 อ่านค่าไม่ได้ขณะเปิด Wi-Fi" % lbl)
                if pin in board.get("strapping", []) and not (c["id"] == "led" and pin == board.get("led")):
                    res.warnings.append("%s เป็นขาที่มีผลตอนเปิดเครื่อง ถ้าบอร์ดบูตไม่ขึ้นให้ย้ายขา" % lbl)
                if pin in board.get("serial_pins", []):
                    res.warnings.append("%s ใช้สื่อสารกับคอมพิวเตอร์ อาจทำให้อัปโหลดโค้ดไม่ได้" % lbl)
        if board["family"] == "esp8266" and adc_count > 1:
            res.errors.append("ESP8266 มีขาแอนะล็อก (A0) เพียงขาเดียว ต่อเซนเซอร์แอนะล็อกได้ครั้งละ 1 ตัว")

    # ---------- สร้างโค้ด
    def generate(self, command, board_id, app_name="Arduino AI"):
        board, text, res = self.plan(command, board_id)
        if not text:
            res.code = "# กรุณาพิมพ์คำสั่ง"
            return res
        if board["family"] == "microbit":
            res.code = "# " + res.errors[0]
            return res
        if not res.components:
            res.code = HELP_TEXT
            res.explanation.append("ยังไม่พบชื่ออุปกรณ์ในคำสั่ง ลองดูตัวอย่างคำสั่งในโค้ดด้านซ้าย")
            return res
        missing = [e for e in res.errors if e.startswith("ขาของบอร์ด") or e.startswith("ESP8266 มีขา")]
        if missing:
            res.code = "# สร้างโค้ดไม่ได้\n" + "\n".join("# - " + e for e in missing) + "\n"
            return res
        if board["family"] == "avr":
            return self._generate_cpp(board, text, res)
        return self._generate_mpy(board, text, res, command, app_name)

    def _fill(self, template, comp, roles, board):
        out = template
        for role, pin in roles.items():
            var = "adc_%s_%s" % (comp["id"], role.lower())
            fam = board["family"]
            if fam == "esp8266":
                adc_setup = "%s = ADC(0)" % var
            elif fam == "esp32":
                adc_setup = "%s = ADC(Pin(%s))\n%s.atten(ADC.ATTN_11DB)" % (var, pin_literal(pin), var)
            else:
                adc_setup = "%s = ADC(Pin(%s))" % (var, pin_literal(pin))
            out = out.replace("{ADC_SETUP_%s}" % role, adc_setup)
            out = re.sub(r"\badc_%s\b" % role, var, out)
            out = out.replace("{%s}" % role, pin_literal(pin))
        return out

    def _onoff(self, comp, roles, board, which, angle):
        code = comp.get(which, "pass")
        code = code.replace("{ANGLE}", str(angle))
        if comp["id"] == "led" and roles.get("SIG") == board.get("led") and board.get("led_inverted"):
            code = comp["off"] if which == "on" else comp["on"]
        return self._fill(code, comp, roles, board)

    # ---------- โค้ดตรวจการต่อสายทีละอุปกรณ์ (รันบนบอร์ดจริง ใช้เวลาไม่กี่วินาที)
    def test_code(self, comp, roles, board):
        """คืนโค้ด MicroPython ที่พิมพ์ TEST_OK / TEST_FAIL <เหตุผล> / TEST_ASK <คำถาม>"""
        missing = [p["label"] for p in comp["pins"] if p["kind"] == "signal" and roles.get(p["role"]) is None]
        if missing:
            return "print('TEST_FAIL บอร์ดนี้ไม่มีขาว่างสำหรับ %s ขา %s')\n" % (comp["name_en"], ", ".join(missing))
        i2c_addr = {"oled": [0x3C, 0x3D], "mpu6050": [0x68, 0x69], "bmp280": [0x76, 0x77], "lcd1602": [0x27, 0x3F]}
        if comp.get("i2c_addr"):
            i2c_addr[comp["id"]] = comp["i2c_addr"]
        soft = board["family"] == "esp8266"
        if comp["id"] in i2c_addr or (comp["type"] == "info" and "SDA" in roles):
            cls = "SoftI2C" if soft else "I2C"
            mk = "SoftI2C(" if soft else "I2C(0, "
            want = i2c_addr.get(comp["id"])
            lines = ["from machine import Pin, " + cls, "try:",
                     "    i2c = %ssda=Pin(%s), scl=Pin(%s))" % (mk, pin_literal(roles.get("SDA")), pin_literal(roles.get("SCL"))),
                     "    found = i2c.scan()",
                     "    print('VALUE: address=' + str([hex(a) for a in found]))"]
            if want:
                lines += ["    if any(a in found for a in %s):" % want,
                          "        print('TEST_OK พบ %s บน I2C')" % comp["name_en"],
                          "    elif found:",
                          "        print('TEST_FAIL พบอุปกรณ์ I2C แต่ที่อยู่ไม่ตรงกับ %s')" % comp["name_en"]]
                lines += ["    else:"]
            else:
                lines += ["    if found:", "        print('TEST_OK พบอุปกรณ์ I2C')", "    else:"]
            lines += ["        print('TEST_FAIL ไม่พบอุปกรณ์ ตรวจสาย SDA SCL และไฟเลี้ยง')",
                      "except Exception as e:", "    print('TEST_FAIL', e)"]
            return "\n".join(lines) + "\n"
        if comp["type"] == "info" or not comp.get("setup"):
            return "print('TEST_ASK อุปกรณ์นี้ยังตรวจอัตโนมัติไม่ได้ ตรวจการต่อสายด้วยตาเทียบกับภาพ ต่อถูกหรือไม่')\n"
        body = list(comp.get("imports", [])) + [self._fill(comp["setup"], comp, roles, board)]
        if comp.get("helpers"):
            body.append(comp["helpers"])
        t = []
        if comp["type"] == "actuator":
            on = self._onoff(comp, roles, board, "on", 90)
            off = self._onoff(comp, roles, board, "off", 90)
            t += ["for i in range(3):"] + ["    " + l for l in on.split("\n")] + ["    time.sleep(0.5)"] + \
                 ["    " + l for l in off.split("\n")] + ["    time.sleep(0.5)"]
            t.append("print('TEST_ASK %s ทำงานเป็นจังหวะ 3 ครั้งหรือไม่')" % comp["name_th"])
        elif comp["type"] == "display":
            t.append("oled.fill(0)\noled.text('TEST OK', 0, 0)\noled.show()")
            t.append("print('TEST_ASK จอแสดงข้อความ TEST OK หรือไม่')")
        else:
            key = comp["keys"][0]
            read = self._fill(comp["read"], comp, roles, board)
            n = 30 if comp.get("bool") else 6
            wait = max(0.1 if comp.get("bool") else 0.3, comp.get("min_interval", 0))
            t += ["vals = []", "for i in range(%d):" % n] + ["    " + l for l in read.split("\n")] + \
                 ["    vals.append(%s)" % key, "    time.sleep(%s)" % _num(wait),
                  "print('VALUE: %s=' + str(vals[-1]))" % key]
            if comp["id"] == "hc_sr04":
                t += ["if max(vals) <= 0:", "    print('TEST_FAIL ไม่ได้รับเสียงสะท้อน ตรวจสาย TRIG ECHO และไฟ 5V')",
                      "else:", "    print('TEST_OK')"]
            elif comp["id"] == "ds18b20":
                t += ["print('TEST_OK' if roms else 'TEST_FAIL ไม่พบ DS18B20 ตรวจตัวต้านทาน 4.7k และสาย DATA')"]
            elif comp["id"] == "hx711":
                t += ["if hx_raw() is None:", "    print('TEST_FAIL HX711 ไม่ตอบสนอง ตรวจสาย DT SCK และไฟเลี้ยง')",
                      "else:", "    print('TEST_OK')"]
            elif comp.get("bool"):
                t += ["if len(set(vals)) > 1:", "    print('TEST_OK ค่าเปลี่ยนตามการกระตุ้น')", "else:",
                      "    print('TEST_ASK ค่าไม่เปลี่ยนเลย (%%s) ระหว่างตรวจได้ลองกระตุ้น%sหรือยัง ถ้ากระตุ้นแล้วค่ายังไม่เปลี่ยน ให้ตอบว่าไม่' %% vals[0])" % comp["name_th"]]
            elif "ADC_SETUP" in comp.get("setup", ""):
                t += ["if min(vals) == max(vals) and vals[0] in (0, 100):",
                      "    print('TEST_FAIL ค่าค้างที่ ' + str(vals[0]) + ' อาจยังไม่ได้ต่อสายสัญญาณหรือไฟเลี้ยง')",
                      "else:", "    print('TEST_OK')"]
            else:
                t.append("print('TEST_OK')")
        code = ["import time", "try:"] + ["    " + l for l in "\n".join(body + t).split("\n")] + \
               ["except Exception as e:", "    print('TEST_FAIL', e)"]
        joined = "\n".join(code)
        names = ["Pin"] + [n for n in ("PWM", "ADC", "I2C", "SoftI2C") if re.search(r"\b%s\(" % n, joined)]
        if soft and "I2C" in names:
            names[names.index("I2C")] = "SoftI2C"
            code = [l.replace("I2C(0, ", "SoftI2C(") for l in code]
        return "from machine import %s\n" % ", ".join(dict.fromkeys(names)) + "\n".join(code) + "\n"

    def _generate_mpy(self, board, text, res, command, app_name):
        comps = res.components
        sensors = [c for c in comps if c["type"] == "sensor"]
        actuators = [c for c in comps if c["type"] == "actuator"]
        displays = [c for c in comps if c["type"] == "display"]
        infos = [c for c in comps if c["type"] == "info"]
        angle = extract_angle(text)
        interval = extract_time_ms(text, default=500 if sensors else 1000)
        extra_imports, setup, helpers, start = [], [], [], []
        for c in comps:
            if c["type"] == "info":
                continue
            roles = res.assigned.get(c["id"], {})
            extra_imports += c.get("imports", [])
            for line in self._fill(c.get("setup", ""), c, roles, board).split("\n"):
                if line and line not in setup:
                    setup.append(line)
            if c.get("helpers"):
                helpers.append(c["helpers"])

        # อุปกรณ์ I2C หลายตัวใช้สายเดียวกัน: เหลือบรรทัดสร้าง i2c บรรทัดเดียว เลือกแบบความเร็วต่ำสุดเพื่อให้ทุกตัวใช้ได้
        i2c_lines = [l for l in setup if l.startswith("i2c = I2C(")]
        if len(i2c_lines) > 1:
            keep = next((l for l in i2c_lines if "freq=" in l), i2c_lines[0])
            first = setup.index(i2c_lines[0])
            setup = [l for l in setup if l not in i2c_lines]
            setup.insert(first, keep)

        body = []
        ind = "    "

        def add(block, level=1):
            for line in block.split("\n"):
                body.append(ind * level + line)

        if sensors or displays:
            for s in sensors:
                add(self._fill(s["read"], s, res.assigned[s["id"]], board))
                res.keys += s["keys"]
            for k in res.keys:
                body.append(ind + 'print("%s:", %s)' % (k, k))
            if displays and res.keys:
                add("oled.fill(0)")
                for i, k in enumerate(res.keys[:6]):
                    add('oled.text("%s: " + str(%s), 0, %d)' % (k, k, i * 10))
                add("oled.show()")
            elif displays:
                add('oled.fill(0)\noled.text("Hello!", 0, 0)\noled.show()')
            if sensors and actuators:
                s = sensors[0]
                key = s["keys"][0]
                if s.get("bool"):
                    op, thr = "==", 1
                else:
                    op, thr = extract_rule_number(text)
                    if op is None:
                        op, thr = DEFAULT_RULES.get(key, (">", 50))
                        if any(h in text for h in LESS_HINTS):
                            op = "<"
                        res.explanation.append("ไม่ได้ระบุตัวเลขในเงื่อนไข จึงใช้ค่าเริ่มต้น %s %s %s" % (key, op, thr))
                cond = "%s %s %s" % (key, op, thr)
                if key in DISTANCE_KEYS and op in ("<", "<="):
                    cond = "0 < " + cond
                res.rule = dict(key=key, op=op, thr=thr, actuators=[a["id"] for a in actuators])
                body.append(ind + "if %s:" % cond)
                for a in actuators:
                    add(self._onoff(a, res.assigned[a["id"]], board, "on", angle), 2)
                body.append(ind + "else:")
                for a in actuators:
                    add(self._onoff(a, res.assigned[a["id"]], board, "off", angle), 2)
                res.explanation.append("เงื่อนไข: ถ้า %s ให้ %s ทำงาน ไม่อย่างนั้นให้หยุด" %
                                       (cond, ", ".join(a["name_th"] for a in actuators)))
            wait = max([interval / 1000] + [c.get("min_interval", 0) for c in sensors])
            body.append(ind + "time.sleep(%s)" % _num(wait))
        else:
            blink = any(w in text for w in ["กระพริบ", "กะพริบ", "blink", "กระพิบ"])
            sweep = any(w in text for w in ["กวาด", "ไปมา", "sweep", "สลับไปมา"])
            only_on = "เปิด" in text and not blink
            only_off = "ปิด" in text.replace("เปิด", "") and not blink
            if sweep and any(a["id"] == "servo" for a in actuators):
                add("for a in range(0, 181, 10):\n    servo_angle(a)\n    time.sleep_ms(50)\nfor a in range(180, -1, -10):\n    servo_angle(a)\n    time.sleep_ms(50)")
                res.explanation.append("เซอร์โวหมุนกวาดไปมาระหว่าง 0 ถึง 180 องศา")
            elif only_off:
                for a in actuators:
                    start.append(self._onoff(a, res.assigned[a["id"]], board, "off", angle))
                add("time.sleep(1)")
            elif only_on or (actuators and all(a["id"] == "servo" for a in actuators)):
                for a in actuators:
                    start.append(self._onoff(a, res.assigned[a["id"]], board, "on", angle))
                if any(a["id"] == "servo" for a in actuators):
                    res.explanation.append("เซอร์โวหมุนไปที่ %d องศา" % angle)
                add("time.sleep(1)")
            else:
                for a in actuators:
                    add(self._onoff(a, res.assigned[a["id"]], board, "on", angle))
                add("time.sleep(%s)" % _num(interval / 1000))
                for a in actuators:
                    add(self._onoff(a, res.assigned[a["id"]], board, "off", angle))
                add("time.sleep(%s)" % _num(interval / 1000))
                res.explanation.append("ทำงานสลับเปิดปิดทุก %s วินาที" % _num(interval / 1000))

        # ประกอบโค้ด
        all_code = "\n".join(setup + helpers + body)
        machine = ["Pin"] + [n for n in ("PWM", "ADC", "I2C") if re.search(r"\b%s\(" % n, all_code)]
        if board["family"] == "esp8266" and "I2C" in machine:
            machine[machine.index("I2C")] = "SoftI2C"
            all_code = all_code.replace("I2C(0, ", "SoftI2C(")
            setup = [l.replace("I2C(0, ", "SoftI2C(") for l in setup]
        lines = ["# โค้ด MicroPython สร้างโดย %s" % app_name,
                 "# คำสั่ง: %s" % command.strip().replace("\n", " "),
                 "# บอร์ด: %s" % board["name"], "",
                 "from machine import " + ", ".join(machine), "import time"]
        for imp in extra_imports:
            if imp not in lines:
                lines.append(imp)
        lines += ["", "# ---- ตั้งค่าอุปกรณ์"] + setup
        if helpers:
            lines += ["", "# ---- ฟังก์ชันช่วย"] + "\n\n".join(helpers).split("\n")
        if start:
            lines += ["", "# ---- สั่งงานครั้งเดียวตอนเริ่ม"] + "\n".join(start).split("\n")
        lines += ["", "# ---- ทำงานวนซ้ำ", "while True:"] + body
        if infos:
            lines += ["", "# หมายเหตุ: " + ", ".join(i["name_en"] for i in infos) +
                      " ต้องติดตั้งไลบรารีเพิ่ม ดูรายละเอียดในคลังความรู้"]
        res.code = "\n".join(lines) + "\n"
        if infos and not (sensors or actuators or displays):
            res.code = self._i2c_scan_code(board, infos, res)
        for c in comps:
            res.explanation.insert(0, "%s: %s" % (c["name_th"], c["explain_th"]))
        return res

    def _i2c_scan_code(self, board, infos, res):
        sda, scl = board["i2c"]["sda"], board["i2c"]["scl"]
        cls = "SoftI2C" if board["family"] == "esp8266" else "I2C"
        head = "SoftI2C(" if cls == "SoftI2C" else "I2C(0, "
        return ("# %s ต้องใช้ไลบรารีเพิ่มเติม\n# โค้ดนี้ใช้ตรวจว่าบอร์ดมองเห็นอุปกรณ์ I2C หรือไม่\n\n"
                "from machine import Pin, %s\nimport time\n\ni2c = %ssda=Pin(%s), scl=Pin(%s))\n\n"
                "while True:\n    found = i2c.scan()\n    print(\"i2c_devices:\", len(found), [hex(a) for a in found])\n    time.sleep(2)\n"
                % (", ".join(i["name_en"] for i in infos), cls, head, pin_literal(sda), pin_literal(scl)))

    # ---------- C++ สำหรับ Arduino Uno / Nano / Mega
    def _generate_cpp(self, board, text, res):
        res.language = "cpp"
        res.warnings.insert(0, "%s รัน MicroPython ไม่ได้ จึงสร้างโค้ดภาษา C++ สำหรับ Arduino IDE แทน" % board["name"])
        inc, glob, setup, body = [], [], ["  Serial.begin(9600);"], []
        sensors = [c for c in res.components if c["type"] == "sensor"]
        actuators = [c for c in res.components if c["type"] == "actuator"]
        angle = extract_angle(text)
        interval = extract_time_ms(text, default=500 if sensors else 1000)
        unsupported = []
        keys = []
        for c in res.components:
            r = res.assigned.get(c["id"], {})
            snip = CPP.get(c["id"])
            if not snip:
                unsupported.append(c["name_en"])
                continue
            def fill(s, r=r):
                for role, pin in r.items():
                    s = s.replace("{%s}" % role, str(pin))
                return s.replace("{ANGLE}", str(angle))
            inc += [i for i in snip.get("inc", []) if i not in inc]
            glob += [fill(g) for g in snip.get("glob", [])]
            setup += ["  " + fill(s) for s in snip.get("setup", [])]
            if c["type"] == "sensor":
                body += ["  " + fill(s) for s in snip["read"]]
                keys.append(snip["key"])
                body.append('  Serial.print("%s: "); Serial.println(%s);' % (snip["key"], snip["key"]))
            c["_cpp"] = {k: fill(v) for k, v in snip.items() if k in ("on", "off")}
        if unsupported:
            res.warnings.append("โหมด C++ ยังไม่รองรับ: " + ", ".join(unsupported))
        res.keys = keys
        if sensors and actuators and keys:
            s = sensors[0]
            key = keys[0]
            op, thr = ("==", 1) if s.get("bool") else extract_rule_number(text)
            if op is None:
                op, thr = DEFAULT_RULES.get(s["keys"][0], (">", 50))
            res.rule = dict(key=s["keys"][0], op=op, thr=thr, actuators=[a["id"] for a in actuators])
            pre = "%s > 0 && " % key if key in DISTANCE_KEYS and op in ("<", "<=") else ""
            body.append("  if (%s%s %s %s) {" % (pre, key, op, thr))
            body += ["    " + a["_cpp"]["on"] for a in actuators if "_cpp" in a]
            body.append("  } else {")
            body += ["    " + a["_cpp"]["off"] for a in actuators if "_cpp" in a]
            body.append("  }")
            body.append("  delay(%d);" % interval)
        elif actuators:
            if any(w in text for w in ["กระพริบ", "กะพริบ", "blink"]) or not ("เปิด" in text or "ปิด" in text):
                body += ["  " + a["_cpp"]["on"] for a in actuators if "_cpp" in a] + ["  delay(%d);" % interval]
                body += ["  " + a["_cpp"]["off"] for a in actuators if "_cpp" in a] + ["  delay(%d);" % interval]
            else:
                which = "off" if "ปิด" in text.replace("เปิด", "") else "on"
                setup += ["  " + a["_cpp"][which] for a in actuators if "_cpp" in a]
        elif sensors:
            body.append("  delay(%d);" % interval)
        code = ["// โค้ด C++ สำหรับ %s (อัปโหลดด้วย Arduino IDE)" % board["name"]]
        code += ["#include <%s>" % i for i in inc] + [""] + glob + ["", "void setup() {"] + setup + ["}", "", "void loop() {"] + body + ["}"]
        res.code = "\n".join(code) + "\n"
        for c in res.components:
            c.pop("_cpp", None)
            res.explanation.insert(0, "%s: %s" % (c["name_th"], c["explain_th"]))
        return res


def _num(v):
    return str(int(v)) if float(v).is_integer() else ("%.2f" % v).rstrip("0")


CPP = {
    "led": dict(setup=["pinMode({SIG}, OUTPUT);"], on="digitalWrite({SIG}, HIGH);", off="digitalWrite({SIG}, LOW);"),
    "buzzer": dict(setup=["pinMode({SIG}, OUTPUT);"], on="digitalWrite({SIG}, HIGH);", off="digitalWrite({SIG}, LOW);"),
    "buzzer_passive": dict(setup=["pinMode({SIG}, OUTPUT);"], on="tone({SIG}, 1000);", off="noTone({SIG});"),
    "relay": dict(setup=["pinMode({SIG}, OUTPUT);", "digitalWrite({SIG}, HIGH);"], on="digitalWrite({SIG}, LOW);", off="digitalWrite({SIG}, HIGH);"),
    "servo": dict(inc=["Servo.h"], glob=["Servo servo;"], setup=["servo.attach({SIG});"], on="servo.write({ANGLE});", off="servo.write(0);"),
    "hc_sr04": dict(setup=["pinMode({TRIG}, OUTPUT);", "pinMode({ECHO}, INPUT);"],
                    read=["digitalWrite({TRIG}, LOW); delayMicroseconds(2);", "digitalWrite({TRIG}, HIGH); delayMicroseconds(10);",
                          "digitalWrite({TRIG}, LOW);", "float distance_cm = pulseIn({ECHO}, HIGH, 30000) * 0.0343 / 2;"], key="distance_cm"),
    "button": dict(setup=["pinMode({SIG}, INPUT_PULLUP);"], read=["int button = !digitalRead({SIG});"], key="button"),
    "pir": dict(setup=["pinMode({SIG}, INPUT);"], read=["int motion = digitalRead({SIG});"], key="motion"),
    "ir_obstacle": dict(setup=["pinMode({SIG}, INPUT);"], read=["int obstacle = !digitalRead({SIG});"], key="obstacle"),
    "flame": dict(setup=["pinMode({SIG}, INPUT);"], read=["int flame = !digitalRead({SIG});"], key="flame"),
    "hx711": dict(glob=["const int HX_DT = {DT};", "const int HX_SCK = {SCK};",
                        "float HX_SCALE = 420.0;  // ปรับค่านี้ตอน calibrate", "long hx_offset = 0;", "",
                        "long hx_raw() {",
                        "  unsigned long t = millis();",
                        "  while (digitalRead(HX_DT)) { if (millis() - t > 1000) return 0; }",
                        "  long v = 0;",
                        "  noInterrupts();",
                        "  for (int i = 0; i < 24; i++) {",
                        "    digitalWrite(HX_SCK, HIGH); delayMicroseconds(1);",
                        "    v = (v << 1) | digitalRead(HX_DT);",
                        "    digitalWrite(HX_SCK, LOW); delayMicroseconds(1);",
                        "  }",
                        "  digitalWrite(HX_SCK, HIGH); delayMicroseconds(1); digitalWrite(HX_SCK, LOW);",
                        "  interrupts();",
                        "  if (v & 0x800000) v |= 0xFF000000;",
                        "  return v;",
                        "}", "",
                        "long hx_avg(int n) { long s = 0; for (int i = 0; i < n; i++) s += hx_raw(); return s / n; }"],
                  setup=["pinMode(HX_DT, INPUT);", "pinMode(HX_SCK, OUTPUT);", "digitalWrite(HX_SCK, LOW);",
                         "delay(500);", "hx_offset = hx_avg(15);  // ตั้งศูนย์ ห้ามวางของตอนเปิดเครื่อง"],
                  read=["float weight_g = (hx_avg(5) - hx_offset) / HX_SCALE;"], key="weight_g"),
    "line_tcrt5000": dict(setup=["pinMode({SIG}, INPUT);"], read=["int on_line = digitalRead({SIG});"], key="on_line"),
    "ph_sensor": dict(glob=["const float PH_MID_V = 2.5;   // แรงดันที่ pH 7 (ปรับตอน calibrate)", "const float PH_SLOPE = 0.18;"],
                      read=["float ph = 7 + (PH_MID_V - analogRead({SIG}) * 5.0 / 1023) / PH_SLOPE;"], key="ph"),
    "sharp_ir": dict(read=["float ir_v = analogRead({SIG}) * 5.0 / 1023;",
                           "float ir_distance_cm = 27.86 * pow(ir_v < 0.3 ? 0.3 : ir_v, -1.15);"], key="ir_distance_cm"),
    "ad8232": dict(setup=["pinMode({LOP}, INPUT);", "pinMode({LOM}, INPUT);"],
                   read=["long ecg = (digitalRead({LOP}) || digitalRead({LOM})) ? 0 : analogRead({SIG}) * 100L / 1023;"], key="ecg"),
}
for _id, _key, _inv in [("ldr", "light", False), ("potentiometer", "pot", False), ("soil", "soil", True), ("rain", "rain", True),
                        ("mq2", "gas", False), ("sound", "sound", False), ("water_level", "water", False),
                        ("fsr402", "force", False)]:
    expr = "100 - analogRead({SIG}) * 100L / 1023" if _inv else "analogRead({SIG}) * 100L / 1023"
    CPP[_id] = dict(read=["long %s = %s;" % (_key, expr)], key=_key)


HELP_TEXT = """# ยังไม่พบชื่ออุปกรณ์ในคำสั่ง
#
# ตัวอย่างคำสั่งที่ใช้ได้:
#   ให้ LED ขา 4 กระพริบทุก 1 วินาที
#   ให้ไฟบนบอร์ดกระพริบทุก 0.5 วินาที
#   หมุน Servo ขา 18 ไป 45 องศา
#   อ่านระยะทางด้วยอัลตราโซนิก ถ้าใกล้กว่า 20 ซม. ให้ Buzzer ดัง
#   อ่านอุณหภูมิและความชื้นด้วย DHT11 แล้วแสดงบนจอ OLED
#   ถ้าดินแห้งน้อยกว่า 30 ให้รีเลย์เปิดปั๊มน้ำ
#   ถ้ามีคนเคลื่อนไหวให้ไฟ LED ติด
#   วัดแรงกดด้วย FSR402 ถ้าเกิน 50 ให้ LED ติด
#   ชั่งน้ำหนักด้วย HX711 แล้วแสดงบนจอ OLED
#   วัดค่า pH น้ำลายด้วย PH-4502C ถ้าน้อยกว่า 5.5 ให้ LED ติด
#   วัดไข้ด้วย MLX90614 ถ้ามากกว่า 37.5 ให้ Buzzer ดัง
#   วัดชีพจรด้วย MAX30102 แล้วแสดงบนจอ OLED
#
# ดูรายชื่ออุปกรณ์ทั้งหมดได้ที่แท็บ "คลังความรู้"
"""


# ------------------------------------------------------------------ ตรวจโค้ดที่ผู้ใช้แก้เองหรือ AI สร้าง
def check_code(code, board):
    """คืนค่า (errors, warnings)"""
    errors, warnings = [], []
    if "void setup" in code or "#include" in code:
        if board["micropython"]:
            warnings.append("โค้ดนี้เป็นภาษา C++ ของ Arduino ไม่ใช่ MicroPython รันบนบอร์ดนี้ผ่านปุ่มอัปโหลดไม่ได้")
        return errors, warnings
    try:
        compile(code, "main.py", "exec")
    except SyntaxError as e:
        errors.append("ไวยากรณ์ผิดที่บรรทัด %s: %s" % (e.lineno, e.msg))
    if board["family"] == "avr":
        warnings.append("บอร์ดนี้รัน MicroPython ไม่ได้")
        return errors, warnings
    for m in re.finditer(r"Pin\(\s*(\d+)\s*(,\s*Pin\.OUT)?", code):
        p, out = int(m.group(1)), bool(m.group(2))
        if p in board.get("forbidden_list", []):
            errors.append("ใช้ขา %s ไม่ได้ (ต่อกับหน่วยความจำภายใน)" % board_pin_label(board, p))
        elif board.get("valid") and p not in board["valid"]:
            errors.append("บอร์ดนี้ไม่มีขา %s" % board_pin_label(board, p))
        if out and p in board.get("input_only", []):
            errors.append("%s เป็นขารับข้อมูลอย่างเดียว ตั้งเป็น Pin.OUT ไม่ได้" % board_pin_label(board, p))
    if "while True" not in code:
        warnings.append("โค้ดไม่มี while True โปรแกรมจะทำงานครั้งเดียวแล้วจบ")
    return errors, warnings
