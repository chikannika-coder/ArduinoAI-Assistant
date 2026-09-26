# -*- coding: utf-8 -*-
"""ตัวช่วยวิเคราะห์ข้อมูลอุปกรณ์ใหม่ (ใช้ในหน้าต่าง "เพิ่มอุปกรณ์ใหม่")

- อ่านไฟล์ที่ครูแนบ: รูปภาพ, ข้อความ/โค้ด (.ino .py .txt .md .csv) และเอกสาร Word (.docx) พร้อมรูปในเอกสาร
- เตรียมรูปส่งให้ AI (ย่อและแปลงเป็น base64)
- สร้างคำสั่ง (prompt) ให้ AI ตอบเป็นข้อมูลอุปกรณ์ตามรูปแบบของคลังความรู้
- วิเคราะห์แบบออฟไลน์ (ไม่ใช้ AI) จากโค้ด Arduino / MicroPython ด้วยกฎง่าย ๆ
"""
import base64
import io
import json
import os
import re
import tempfile
import zipfile

IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
TEXT_EXT = (".ino", ".py", ".txt", ".md", ".csv", ".h", ".cpp", ".c", ".json")
MAX_TEXT = 12000        # ตัวอักษรสูงสุดที่ส่งให้ AI
MAX_IMAGES = 5


# ------------------------------------------------------------------ อ่านไฟล์แนบ
def read_docx(path):
    """อ่านข้อความและรูปจากไฟล์ Word โดยไม่ต้องติดตั้งไลบรารีเพิ่ม คืนค่า (ข้อความ, [ไฟล์รูปชั่วคราว])"""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
        xml = re.sub(r"</w:p>", "\n", xml)
        xml = re.sub(r"<w:tab/>", "\t", xml)
        xml = re.sub(r"<w:br/>", "\n", xml)
        text = "".join(a or b for a, b in re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>|(\n|\t)", xml))
        for a, b in (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'"), ("&amp;", "&")):
            text = text.replace(a, b)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        images = []
        media = sorted(n for n in z.namelist() if n.startswith("word/media/") and n.lower().endswith(IMAGE_EXT))
        if media:
            tmp = tempfile.mkdtemp(prefix="arduinoai_docx_")
            for n in media:
                dst = os.path.join(tmp, os.path.basename(n))
                with open(dst, "wb") as f:
                    f.write(z.read(n))
                images.append(dst)
    return text, images


def read_attachment(path):
    """คืนค่า (ข้อความ, [รูป]) จากไฟล์ใดก็ได้ที่รองรับ"""
    low = path.lower()
    if low.endswith(IMAGE_EXT):
        return "", [path]
    if low.endswith(".docx"):
        return read_docx(path)
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8", "cp874", "tis-620", "latin-1"):
        try:
            return raw.decode(enc), []
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace"), []


def image_b64(path, max_side=1024):
    """ย่อรูปแล้วแปลงเป็น (media_type, base64) สำหรับส่งให้ AI"""
    try:
        from PIL import Image, ImageOps
        im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        im.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=85)
        return "image/jpeg", base64.b64encode(buf.getvalue()).decode("ascii")
    except ImportError:
        low = path.lower()
        mt = "image/png" if low.endswith(".png") else "image/jpeg" if low.endswith((".jpg", ".jpeg")) else \
             "image/gif" if low.endswith(".gif") else "image/webp" if low.endswith(".webp") else None
        if not mt or os.path.getsize(path) > 4_000_000:
            raise RuntimeError("ต้องติดตั้ง Pillow ก่อนจึงจะส่งรูปนี้ให้ AI ได้ (ดับเบิลคลิก install.bat)")
        with open(path, "rb") as f:
            return mt, base64.b64encode(f.read()).decode("ascii")


# ------------------------------------------------------------------ คำสั่งสำหรับ AI
SCHEMA_TH = """รูปแบบข้อมูลอุปกรณ์ของโปรแกรม (JSON):
{
 "id": "รหัสภาษาอังกฤษตัวเล็ก ไม่มีช่องว่าง เช่น vl53l0x",
 "name_th": "ชื่อภาษาไทย", "name_en": "ชื่อภาษาอังกฤษ", "category": "หมวด เช่น แสง ระยะทาง สุขภาพ",
 "type": "sensor | actuator | info",
 "keywords": ["คำเฉพาะของอุปกรณ์ก่อน เช่น รหัสรุ่น", "คำไทยที่นักเรียนอาจพิมพ์"],
 "voltage": "เช่น 3.3V-5V",
 "pins": [{"label": "VCC", "kind": "power3"}, {"label": "GND", "kind": "gnd"},
          {"label": "AO", "kind": "signal", "need": "adc", "role": "SIG"}],
 "imports": ["import ... (ถ้าต้องใช้ นอกเหนือจาก machine และ time)"],
 "setup": "โค้ดตั้งค่า MicroPython", "helpers": "ฟังก์ชันช่วย (ถ้ามี)",
 "read": "โค้ดอ่านค่า (sensor) ต้องกำหนดตัวแปรทุกชื่อใน keys",
 "on": "โค้ดสั่งเปิด (actuator)", "off": "โค้ดสั่งปิด (actuator)",
 "keys": ["ชื่อค่าที่อ่านได้ ภาษาอังกฤษตัวเล็ก เช่น distance_mm"],
 "sim": [ค่าต่ำสุด, ค่าสูงสุด, "float" หรือ "bool"],
 "i2c_addr": [ที่อยู่ I2C เป็นตัวเลขฐานสิบ เช่น 41 สำหรับ 0x29] (เฉพาะอุปกรณ์ I2C),
 "library": "ชื่อแพ็กเกจ mip (ถ้าจำเป็นจริง ๆ ไม่อย่างนั้นเว้นว่าง)",
 "explain_th": "อธิบายหลักการทำงาน 1-2 ประโยคสำหรับนักเรียน ม.ต้น",
 "warnings": ["คำเตือนด้านแรงดันและความปลอดภัย"]
}
กติกาการเขียนโค้ด (สำคัญมาก โปรแกรมจะนำไปประกอบเป็นโค้ดเต็มเอง):
- kind ของขา: power5 (ไฟ 5V), power3 (ไฟ 3.3V), gnd, signal
- need ของขาสัญญาณ: out, inp, adc, pwm, i2c_sda, i2c_scl
- role ของขาสัญญาณเป็นตัวพิมพ์ใหญ่ไม่ซ้ำกัน ขาเดียวใช้ SIG, I2C ใช้ SDA และ SCL, หลายขาแอนะล็อกใช้ CH1 CH2
- ใน setup/read/on/off ใช้ {ROLE} แทนเลขขา เช่น Pin({SIG}, Pin.IN)
- ขา ADC: เขียน {ADC_SETUP_SIG} หนึ่งบรรทัดใน setup (โปรแกรมจะแทนเป็นโค้ดสร้าง ADC ให้ถูกกับบอร์ด) แล้วอ่านด้วย adc_SIG.read_u16() (ได้ 0-65535)
- I2C: บรรทัดแรกของ setup ต้องเป็น i2c = I2C(0, sda=Pin({SDA}), scl=Pin({SCL})) พอดี แล้วใช้ตัวแปร i2c
- helpers จะไม่ถูกแทนค่า {ROLE} และ adc_ROLE ถ้าฟังก์ชันต้องใช้ขาหรือ ADC ให้สร้างตัวแปรไว้ใน setup ก่อน เช่น my_adc = adc_SIG
- ไม่ต้องเขียน import machine/time, ไม่ต้องเขียน while True, ไม่ต้อง print (โปรแกรมทำให้เอง)
- read ต้องจบภายใน 3 วินาที ห้ามวนไม่รู้จบ ใช้ MicroPython มาตรฐานเท่านั้น (ห้ามใช้ไลบรารี Arduino)
- ตั้งชื่อตัวแปรให้ขึ้นต้นด้วยรหัสอุปกรณ์ เพื่อไม่ให้ชนกับอุปกรณ์อื่น
- ถ้าไม่มีข้อมูลพอจะเขียนโค้ดอ่านค่าได้จริง ให้ใช้ type เป็น info และบอกเหตุผล ห้ามเดาเลขรีจิสเตอร์"""


def build_prompt(user_text, kb, board, form_json=None, image_count=0, fix_errors=None):
    examples = [kb.comp_by_id[i] for i in ("fsr402", "mpu6050", "hx711") if i in kb.comp_by_id]
    ex = [{k: c.get(k) for k in ("id", "name_th", "name_en", "category", "type", "keywords", "voltage", "pins", "setup",
                                  "helpers", "read", "keys", "sim", "i2c_addr", "explain_th", "warnings") if c.get(k) is not None}
          for c in examples]
    existing = "\n".join("- %s: %s | คำค้น: %s" % (c["id"], c["name_en"], ", ".join(c["keywords"][:6])) for c in kb.components)
    parts = ["ครูต้องการเพิ่มอุปกรณ์ใหม่ลงคลังความรู้ของโปรแกรมสร้างโค้ด MicroPython สำหรับนักเรียน ม.ต้น",
             "งานของคุณ: วิเคราะห์ข้อมูลที่ครูให้มา (ข้อความ%s) ว่าเป็นอุปกรณ์อะไร ทำงานอย่างไร ต่อขาอย่างไร แล้วเขียนข้อมูลอุปกรณ์ตามรูปแบบของโปรแกรม"
             % (" และรูป %d รูป" % image_count if image_count else ""),
             SCHEMA_TH,
             "ตัวอย่างอุปกรณ์ที่ใช้งานได้จริงในคลัง:\n" + json.dumps(ex, ensure_ascii=False, indent=1),
             "อุปกรณ์ที่มีในคลังแล้ว (ห้ามใช้ id ซ้ำ และคำค้นต้องไม่ซ้ำกับอุปกรณ์อื่น):\n" + existing,
             "บอร์ดที่ครูเลือกอยู่: %s (ไฟสัญญาณ %sV)" % (board["name"], board["logic_v"])]
    if form_json:
        parts.append("ข้อมูลที่ครูกรอกไว้แล้วในฟอร์ม (ใช้เป็นฐาน แก้ส่วนที่ผิด):\n" + form_json)
    parts.append("ข้อมูลจากครู:\n" + (user_text.strip()[:MAX_TEXT] if user_text.strip() else "(ไม่มีข้อความ ดูจากรูป)"))
    if fix_errors:
        parts.append("ข้อมูลที่คุณตอบรอบก่อนนำไปสร้างโค้ดแล้วมีปัญหาดังนี้ แก้ให้ถูกแล้วตอบใหม่ทั้งหมด:\n- " + "\n- ".join(fix_errors))
    parts.append("ตอบเป็นภาษาไทยตามลำดับนี้:\n"
                 "## ผลการวิเคราะห์\n(อุปกรณ์นี้คืออะไร หลักการทำงาน การต่อสายกับบอร์ด ค่าที่อ่านได้หมายถึงอะไร "
                 "ไอเดียโปรเจกต์ 2-3 ข้อ และข้อควรระวัง ถ้าในรูปหรือข้อความมีหลายอุปกรณ์ ให้บอกด้วยว่าตัวไหนมีในคลังแล้ว)\n"
                 "```json\n(ข้อมูลอุปกรณ์ 1 ชิ้นตามรูปแบบข้างบน)\n```")
    return "\n\n".join(parts)


def parse_ai_reply(text):
    """แยกคำอธิบายกับ JSON ออกจากคำตอบของ AI คืนค่า (analysis_text, comp_dict หรือ None)"""
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    raw = m.group(1) if m else None
    if raw is None:
        m2 = re.search(r"\{.*\}", text, re.S)
        raw = m2.group(0) if m2 else None
    comp = None
    if raw:
        try:
            comp = json.loads(raw)
        except json.JSONDecodeError:
            try:   # AI บางตัวใส่ comma เกินท้ายรายการ
                comp = json.loads(re.sub(r",\s*([}\]])", r"\1", raw))
            except json.JSONDecodeError:
                comp = None
    analysis = text[:m.start()] if m else text
    analysis = re.sub(r"^\s*#+\s*ผลการวิเคราะห์\s*", "", analysis).strip()
    return analysis, comp


# ------------------------------------------------------------------ วิเคราะห์แบบออฟไลน์
def known_components(text, kb):
    """หาอุปกรณ์ในคลังที่ถูกพูดถึงในข้อความยาว ๆ (คำภาษาอังกฤษต้องเป็นคำเต็ม เช่น "ir" ไม่นับใน "Wire")"""
    low = text.lower()
    out = []
    for c in kb.components:
        for kw in c["keywords"]:
            if re.fullmatch(r"[a-z0-9 ._+-]+", kw):
                if len(kw) >= 3 and re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(kw), low):
                    out.append(c)
                    break
            elif len(kw) >= 4 and kw in low:
                out.append(c)
                break
    return out


_LED_WORDS = ("LED", "BUZZER", "RELAY", "MOTOR", "SERVO", "FAN", "PUMP")


def offline_analyze(text, kb):
    """อ่านโค้ด Arduino/MicroPython หรือข้อความ แล้วเดาข้อมูลอุปกรณ์ คืนค่า (comp บางส่วน, รายงานภาษาไทย)"""
    report = []
    known = known_components(text, kb)
    if known:
        report.append("พบชื่ออุปกรณ์ที่มีในคลังความรู้แล้ว: " + ", ".join("%s (%s)" % (c["name_th"], c["id"]) for c in known))
        report.append("→ ถ้าเป็นอุปกรณ์เดียวกัน ไม่ต้องเพิ่มใหม่ พิมพ์คำสั่งที่มีคำว่า \"%s\" ได้เลย" % known[0]["keywords"][0])
    defines = dict(re.findall(r"#define\s+(\w+)\s+(A?\d+)\b", text))
    defines.update(dict(re.findall(r"(?:const\s+)?(?:int|byte|uint8_t)\s+(\w+)\s*=\s*(A?\d+)\s*;", text)))

    def resolve(x):
        x = x.strip()
        return defines.get(x, x)

    def role_name(expr, idx, total, default):
        return default if total == 1 else "CH%d" % (idx + 1)

    adc = list(dict.fromkeys(re.findall(r"analogRead\(\s*(\w+)\s*\)", text)))
    adc += [m for m in re.findall(r"ADC\(\s*(?:Pin\()?\s*(\w+)", text) if m not in adc]
    dig_in = list(dict.fromkeys(re.findall(r"digitalRead\(\s*(\w+)\s*\)", text) +
                                re.findall(r"pulseIn\(\s*(\w+)", text) +
                                re.findall(r"Pin\(\s*(\w+)\s*,\s*Pin\.IN", text)))
    dig_out = list(dict.fromkeys(re.findall(r"digitalWrite\(\s*(\w+)\s*,", text) +
                                 re.findall(r"Pin\(\s*(\w+)\s*,\s*Pin\.OUT", text)))
    pwm = list(dict.fromkeys(re.findall(r"analogWrite\(\s*(\w+)", text) + re.findall(r"\.attach\(\s*(\w+)", text) +
                             re.findall(r"PWM\(\s*Pin\(\s*(\w+)", text)))
    is_i2c = bool(re.search(r"Wire\.h|Wire\.begin|I2C\(|SoftI2C\(", text))
    onewire = re.search(r"OneWire\s*\w*\s*\(\s*(\w+)\s*\)", text)
    addrs = sorted({int(a, 16) for a in re.findall(r"0x([0-9A-Fa-f]{2})\b", text)
                    if 0x08 <= int(a, 16) <= 0x77}) if is_i2c else []
    # แยก LED/บัซเซอร์ที่อยู่ในโค้ดออก เพราะคลังมีอยู่แล้ว
    extra_out = [p for p in dig_out if any(w in p.upper() for w in _LED_WORDS)]
    dig_out = [p for p in dig_out if p not in extra_out]
    if extra_out:
        report.append("โค้ดมีอุปกรณ์สั่งงานร่วมด้วย (%s) ซึ่งมีในคลังแล้ว จึงไม่รวมไว้ในอุปกรณ์ใหม่ ใช้คำสั่งร่วมกันได้ เช่น \"... ให้ LED ติด\""
                      % ", ".join(extra_out))

    name = None
    inc = [i for i in re.findall(r"#include\s*[<\"]([\w./-]+)\.h[>\"]", text)
           if i not in ("Wire", "Arduino", "math", "SPI", "Servo", "OneWire", "DallasTemperature", "WiFi")]
    models = [m for m in re.findall(r"\b([A-Z]{2,}[A-Z0-9]*-?[A-Z0-9]*\d[A-Z0-9-]*)\b", text)
              if not re.match(r"(GPIO|ADC|PIN|CH|WROOM|ESP32|ESP8266|UTF|HTTP|ATTN|PWM|I2C|SPI|UART|USB)", m)]
    if inc:
        name = inc[0]
    elif models:
        name = models[0]
    elif defines:
        pref = [k.split("_")[0] for k in defines if "_" in k and not any(w in k.upper() for w in _LED_WORDS)]
        name = pref[0] if pref else None
    if not name:
        first = next((l.strip(" /#*-") for l in text.splitlines() if l.strip(" /#*-")), "new_sensor")
        name = first[:30]
    cid = re.sub(r"[^a-z0-9_]", "_", name.lower()).strip("_") or "new_sensor"
    if cid in kb.comp_by_id:
        report.append("รหัส \"%s\" มีในคลังแล้ว จึงตั้งรหัสใหม่เป็น \"%s_2\" (ถ้าจะแก้ของเดิม ให้ใช้ปุ่มแก้ไขในแท็บคลังความรู้แทน)" % (cid, cid))
        cid += "_2"

    labels = []
    for s in re.findall(r"Serial\.print(?:ln)?\(\s*\"([^\"]+)\"", text) + re.findall(r"print\(\s*[\"']([^\"']+)[\"']", text):
        for part in re.split(r"[,:=]", s):
            w = re.sub(r"[^a-z0-9_]", "_", part.strip().lower()).strip("_")
            if w and not w.isdigit() and len(w) < 20 and w not in labels:
                labels.append(w)

    expected = len(adc) + len(dig_in)
    if len(labels) != expected:
        labels = []          # ชื่อที่ print ไม่ตรงกับจำนวนค่าที่อ่าน ไม่ใช้ เดี๋ยวจะจับคู่ผิด
    pins, setup, read, keys, imports = [], [], [], [], []
    comp = dict(id=cid, name_en=name, name_th=name, category="", voltage="3.3V-5V")
    volt = re.findall(r"(\d(?:\.\d)?)\s*V\b", text)
    if volt:
        comp["voltage"] = "-".join(sorted(set(v + "V" for v in volt[:4]), key=lambda s: float(s[:-1])))
    only_5v = "5V" in comp["voltage"] and "3.3" not in comp["voltage"]
    pins += [dict(label="VCC", kind="power5" if only_5v else "power3", need=None, role="VCC"),
             dict(label="GND", kind="gnd", need=None, role="GND")]

    ctype = "info"
    if is_i2c:
        pins += [dict(label="SDA", kind="signal", need="i2c_sda", role="SDA"),
                 dict(label="SCL", kind="signal", need="i2c_scl", role="SCL")]
        setup.append("i2c = I2C(0, sda=Pin({SDA}), scl=Pin({SCL}))")
        if addrs:
            comp["i2c_addr"] = addrs
            a = addrs[0]
            k = labels[0] if labels else cid + "_raw"
            read.append("%s_d = i2c.readfrom(0x%02X, 2)   # TODO: แก้ตามคู่มือของอุปกรณ์\n%s = %s_d[0] << 8 | %s_d[1]"
                        % (cid, a, k, cid, cid))
            keys.append(k)
            ctype = "sensor"
            report.append("ใช้ I2C ที่อยู่ %s — โค้ดอ่านค่าเป็นแบบร่าง ต้องแก้ตามคู่มือ (datasheet)" % ", ".join("0x%02X" % x for x in addrs))
        else:
            report.append("ใช้ I2C แต่ไม่พบที่อยู่ในโค้ด ให้ดูในคู่มือ (มักอยู่ในรูป 0x..)")
    elif onewire:
        pins.append(dict(label="DATA", kind="signal", need="inp", role="SIG"))
        imports.append("import onewire, ds18x20")
        setup.append("%s_ds = ds18x20.DS18X20(onewire.OneWire(Pin({SIG})))\n%s_roms = %s_ds.scan()" % (cid, cid, cid))
        read.append("%s_ds.convert_temp()\ntime.sleep_ms(750)\ntemp_c = %s_ds.read_temp(%s_roms[0]) if %s_roms else -127"
                    % (cid, cid, cid, cid))
        keys.append("temp_c")
        ctype = "sensor"
    if adc:
        for i, a in enumerate(adc):
            role = role_name(a, i, len(adc), "SIG")
            pins.append(dict(label="%s (%s)" % ("OUT" if len(adc) == 1 else "OUT%d" % (i + 1), a), kind="signal", need="adc", role=role))
            setup.append("{ADC_SETUP_%s}" % role)
            k = labels[len(keys)] if len(labels) > len(keys) else (cid if len(adc) == 1 else "%s_ch%d" % (cid, i + 1))
            read.append("%s = adc_%s.read_u16() * 100 // 65535" % (k, role))
            keys.append(k)
        ctype = "sensor"
        report.append("พบการอ่านค่าแอนะล็อก %d ช่อง (%s) → ใช้ขา ADC ค่าที่อ่านได้ปรับเป็น 0-100"
                      % (len(adc), ", ".join("%s=%s" % (a, resolve(a)) for a in adc)))
    used = {p["role"] for p in pins}
    for i, d in enumerate(dig_in):
        role = "SIG" if "SIG" not in used else "IN%d" % (i + 1)
        used.add(role)
        pins.append(dict(label="%s (%s)" % ("DO" if role == "SIG" else role, d), kind="signal", need="inp", role=role))
        setup.append("%s_%s = Pin({%s}, Pin.IN)" % (cid, role.lower(), role))
        k = labels[len(keys)] if len(labels) > len(keys) else "%s_%s" % (cid, role.lower())
        read.append("%s = %s_%s.value()" % (k, cid, role.lower()))
        keys.append(k)
        ctype = "sensor"
    outs = dig_out + pwm
    if outs and ctype == "info":
        ctype = "actuator"
        for i, d in enumerate(outs):
            role = "SIG" if i == 0 else "OUT%d" % (i + 1)
            pins.append(dict(label="IN (%s)" % d, kind="signal", need="pwm" if d in pwm else "out", role=role))
            setup.append("%s_%s = Pin({%s}, Pin.OUT)" % (cid, role.lower(), role))
        comp["on"] = "\n".join("%s_%s.value(1)" % (cid, p["role"].lower()) for p in pins if p["kind"] == "signal")
        comp["off"] = "\n".join("%s_%s.value(0)" % (cid, p["role"].lower()) for p in pins if p["kind"] == "signal")
        report.append("พบการสั่งงานขาออก %s → ตั้งเป็นอุปกรณ์สั่งงาน (เปิด = 1, ปิด = 0)" % ", ".join(outs))
    if re.search(r"\b(FFT|DFT|arduinoFFT|fft)\b", text) or re.search(r"cos\(.*angle", text):
        report.append("โค้ดต้นฉบับคำนวณความถี่ (FFT/DFT) แบบออฟไลน์แปลงส่วนนี้ให้ไม่ได้ ให้ใช้ปุ่ม AI หรือใช้อุปกรณ์ในคลังที่ใกล้เคียง")
    comp.update(type=ctype, pins=pins, setup="\n".join(setup), keywords=[cid, name.lower()] if name.lower() != cid else [cid],
                explain_th="(กรอกคำอธิบายสั้น ๆ สำหรับนักเรียน)", warnings=[])
    if imports:
        comp["imports"] = imports
    if ctype == "sensor":
        comp["read"] = "\n".join(read)
        comp["keys"] = keys
        comp["sim"] = [0, 100, "float"]
    if ctype == "info" and not known:
        report.append("ไม่พบโค้ดที่บอกการต่อขาได้ ลองวางโค้ดตัวอย่าง Arduino ของอุปกรณ์ หรือใช้ปุ่ม \"ให้ AI วิเคราะห์\" (อ่านรูปและข้อความได้)")
    if ctype != "info":
        report.append("กรอกฟอร์มให้แล้ว: รหัส %s, ชนิด %s, ขาสัญญาณ %d ขา, ค่าที่อ่านได้: %s"
                      % (cid, ctype, sum(p["kind"] == "signal" for p in pins), ", ".join(keys) or "-"))
        report.append("ตรวจชื่อ คำค้น แรงดัน และคำอธิบายอีกครั้ง แล้วกด \"ทดลองสร้างโค้ด\"")
    return comp, "\n".join("• " + r for r in report) if report else "ไม่พบข้อมูลที่วิเคราะห์ได้"
