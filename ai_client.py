# -*- coding: utf-8 -*-
"""สมอง AI ของโปรแกรม เลือกได้ 2 แบบ
1) Claude API (ต้องใช้อินเทอร์เน็ตและ API Key)
2) Ollama (รันโมเดลในเครื่องเอง ฟรี ไม่ต้องใช้อินเทอร์เน็ต)
ทุกคำถามจะแนบข้อมูลจากคลังความรู้ไปด้วย (RAG) เพื่อให้ AI ตอบตามข้อมูลที่ครูตรวจแล้ว
"""
import json
import os
import re
import urllib.request

SYSTEM_TEMPLATE = """คุณคือ "{app_name}" ผู้ช่วยสอนไมโครคอนโทรลเลอร์ของ{school} สำหรับนักเรียนมัธยมศึกษาตอนต้น
กติกา:
- ตอบเป็นภาษาไทยที่เข้าใจง่าย ประโยคสั้น
- ใช้ข้อมูลบอร์ดและอุปกรณ์ในส่วน "คลังความรู้" เป็นหลัก ถ้าข้อมูลไม่พอหรือไม่แน่ใจ ให้บอกตรง ๆ ว่าไม่แน่ใจ ห้ามเดาเลขขา
- ถ้าบอร์ดรองรับ MicroPython ให้เขียนโค้ด MicroPython ถ้าเป็น Arduino Uno/Nano/Mega ให้เขียน C++ สำหรับ Arduino IDE
- ถ้ามี "แผนการต่อขา" ให้ใช้ขาตามแผนนั้นทุกขา
- ให้โปรแกรม print ค่าที่อ่านได้ทีละบรรทัดในรูปแบบ ชื่อค่า: ตัวเลข เช่น distance_cm: 12.5 เพื่อให้แสดงกราฟเรียลไทม์ได้
- เตือนเรื่องความปลอดภัยเสมอ เช่น แรงดัน 5V กับ 3.3V ตัวต้านทานของ LED และห้ามต่อไฟบ้าน 220V โดยไม่มีครูดูแล
เมื่อเขียนโค้ด ให้ตอบในรูปแบบนี้:
```python
(โค้ดทั้งหมด)
```
## การต่อสาย
(รายการขาที่ต้องต่อ)
## คำอธิบาย
(อธิบายการทำงานทีละขั้น)"""


class AIClient:
    def __init__(self, config):
        self.config = config

    @property
    def backend(self):
        return self.config.get("ai_backend", "none")

    def available(self):
        if self.backend == "claude":
            return bool(self._claude_key())
        return self.backend == "ollama"

    def _claude_key(self):
        return self.config.get("claude_api_key") or os.environ.get("ANTHROPIC_API_KEY", "")

    def _system(self):
        return SYSTEM_TEMPLATE.format(app_name=self.config.get("app_name", "Arduino AI"),
                                      school=self.config.get("school", "โรงเรียน"))

    def _post(self, url, body, headers, timeout=120):
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                     headers={"content-type": "application/json", **headers})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    def chat(self, user_text, history=None):
        history = history or []
        messages = history + [{"role": "user", "content": user_text}]
        if self.backend == "claude":
            data = self._post("https://api.anthropic.com/v1/messages",
                              {"model": self.config.get("claude_model", "claude-sonnet-5"), "max_tokens": 2500,
                               "system": self._system(), "messages": messages},
                              {"x-api-key": self._claude_key(), "anthropic-version": "2023-06-01"})
            return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        if self.backend == "ollama":
            url = self.config.get("ollama_url", "http://localhost:11434").rstrip("/") + "/api/chat"
            data = self._post(url, {"model": self.config.get("ollama_model", "qwen2.5-coder:7b"), "stream": False,
                                    "messages": [{"role": "system", "content": self._system()}] + messages}, {}, timeout=300)
            return data.get("message", {}).get("content", "")
        raise RuntimeError("ยังไม่ได้เลือก AI ในแท็บตั้งค่า")

    def chat_with_images(self, user_text, images=None, max_tokens=6000):
        """ส่งข้อความพร้อมรูป images = [(media_type, base64), ...] คืนค่า (คำตอบ, หมายเหตุ)
        Claude อ่านรูปได้ทุกรุ่น ส่วน Ollama ต้องใช้โมเดลที่อ่านรูปได้ เช่น qwen2.5vl หรือ llava"""
        images = images or []
        if self.backend == "claude":
            content = [{"type": "image", "source": {"type": "base64", "media_type": mt, "data": b64}} for mt, b64 in images]
            content.append({"type": "text", "text": user_text})
            data = self._post("https://api.anthropic.com/v1/messages",
                              {"model": self.config.get("claude_model", "claude-sonnet-5"), "max_tokens": max_tokens,
                               "system": self._system(), "messages": [{"role": "user", "content": content}]},
                              {"x-api-key": self._claude_key(), "anthropic-version": "2023-06-01"}, timeout=240)
            return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"), ""
        if self.backend == "ollama":
            url = self.config.get("ollama_url", "http://localhost:11434").rstrip("/") + "/api/chat"
            msg = {"role": "user", "content": user_text}
            note = ""
            if images:
                msg["images"] = [b64 for _, b64 in images]
            body = {"model": self.config.get("ollama_model", "qwen2.5-coder:7b"), "stream": False,
                    "messages": [{"role": "system", "content": self._system()}, msg]}
            try:
                data = self._post(url, body, {}, timeout=600)
            except Exception:  # noqa: BLE001  โมเดลอ่านรูปไม่ได้ ลองส่งเฉพาะข้อความ
                if not images:
                    raise
                msg.pop("images")
                data = self._post(url, body, {}, timeout=600)
                note = "โมเดล Ollama ที่เลือกอ่านรูปไม่ได้ จึงวิเคราะห์จากข้อความอย่างเดียว (ถ้าต้องการให้อ่านรูป ใช้โมเดล qwen2.5vl หรือ llava)"
            return data.get("message", {}).get("content", ""), note
        raise RuntimeError("ยังไม่ได้เลือก AI ในแท็บตั้งค่า")

    # ---------- งานเฉพาะ
    def generate_code(self, command, board, plan, kb):
        wiring = "\n".join("- %s ขา %s -> บอร์ด %s" % (w["comp_name"], w["comp_pin"], w["board_pin"]) for w in plan.wiring)
        prompt = ("คลังความรู้:\n%s\n\nบอร์ดที่ใช้: %s\nแผนการต่อขา:\n%s\n\nคำสั่งของนักเรียน: %s" %
                  (kb.context_for_ai(board, plan.components), board["name"], wiring or "(ไม่มี)", command))
        return self.chat(prompt)

    def explain_error(self, error_text, code, board):
        prompt = ("บอร์ด: %s\nโค้ด:\n```\n%s\n```\nข้อความ Error:\n%s\n\nอธิบายสาเหตุเป็นภาษาไทยง่าย ๆ และบอกวิธีแก้ทีละขั้น"
                  % (board["name"], code[:4000], error_text[-2000:]))
        return self.chat(prompt)

    def ask(self, question, kb, board, history=None):
        comps = [c for c, _ in kb.detect(question)]
        prompt = "คลังความรู้:\n%s\n\nคำถาม: %s" % (kb.context_for_ai(board, comps), question)
        return self.chat(prompt, history)


def _suggest(self, goal, kb, board, detected=None):
    """ให้ AI เลือกอุปกรณ์จากคลังความรู้ แล้วเขียนเป็นคำสั่งภาษาไทยที่ตัวสร้างโค้ดเข้าใจ"""
    items = "\n".join("- %s: %s (%s)" % (c["id"], c["name_th"], c["name_en"]) for c in kb.components)
    found = ", ".join(d["comp"] for d in (detected or {}).get("i2c", []) if d.get("comp")) or "ไม่มี"
    prompt = ("นักเรียนอยากทำ: %s\nบอร์ด: %s\nอุปกรณ์ที่ตรวจพบว่าต่ออยู่: %s\nรายการอุปกรณ์ที่โรงเรียนมี (id: ชื่อ):\n%s\n\n"
              "เลือกอุปกรณ์จากรายการเท่านั้น ไม่เกิน 3 ชิ้น (เซนเซอร์ 1 ตัว และอุปกรณ์สั่งงานหรือจอ) แล้วตอบเป็น JSON อย่างเดียว\n"
              '{"components": ["id"], "command": "คำสั่งภาษาไทยสั้น ๆ ที่มีชื่ออุปกรณ์ภาษาอังกฤษและเงื่อนไขพร้อมตัวเลข", "reason": "เหตุผลสั้น ๆ"}\n'
              'ตัวอย่าง command: "อ่านระยะทางด้วย Ultrasonic HC-SR04 ถ้าใกล้กว่า 20 ซม. ให้ Buzzer ดัง"\n'
              "ถ้าต้องใช้อุปกรณ์ที่ไม่มีในรายการ ให้บอกใน reason ว่าต้องเพิ่มอุปกรณ์อะไรลงคลังความรู้"
              % (goal, board["name"], found, items))
    text = self.chat(prompt)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise RuntimeError("AI ไม่ได้ตอบเป็นรูปแบบที่อ่านได้")
    out = json.loads(m.group(0))
    ids = [i for i in out.get("components", []) if i in kb.comp_by_id]
    cmd = out.get("command", "")
    have = {c["id"] for c, _ in kb.detect(cmd)}
    missing = [kb.comp_by_id[i]["name_en"] for i in ids if i not in have]
    if missing:
        cmd = cmd + " ใช้ " + " ".join(missing)
    out["command"] = cmd
    return out


AIClient.suggest_project = _suggest


def extract_code(text):
    m = re.search(r"```(?:python|py|cpp|c\+\+|arduino)?\s*\n(.*?)```", text, re.S)
    return m.group(1).strip() + "\n" if m else ""
