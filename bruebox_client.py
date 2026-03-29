# bruebox_client.py
import requests
import xml.etree.ElementTree as ET

NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
NS_BRU  = "http://www.glory.co.jp/bruebox.xsd"


class BrueBoxClient:
    def __init__(self, ip_address="192.168.0.25"):
        self.ip_address = ip_address
        self.url = f"http://{ip_address}/axis2/services/BrueBoxService"
        self.session_id = None
        self.log_callback = None
        self.http = requests.Session()

    # -------------------------------
    # Dynamic IP assignment
    # -------------------------------
    def set_ip(self, ip):
        self.ip_address = ip
        self.url = f"http://{ip}/axis2/services/BrueBoxService"
        if self.log_callback:
            self.log_callback(f"✅ IP set to: {self.url}", "blue")

    # -------------------------------
    # Internal logger
    # -------------------------------
    def _log(self, msg, color="black"):
        if self.log_callback:
            self.log_callback(msg, color)

    # -------------------------------
    # POST Helper (FULL LOGGING)
    # -------------------------------
    def _post(self, action, xml, *, timeout=(2.0, 30.0)):

        # ✅ REQUEST LOGS
        self._log("========== REQUEST ==========", "blue")
        self._log(f"SOAPAction: {action}", "blue")
        self._log(f"URL = {self.url}", "blue")

        # ✅ Log missing SessionID
        if not self.session_id or self.session_id.strip() == "":
            self._log("⚠️ Sending request WITHOUT SessionID", "orange")

        self._log(xml, "blue")

        headers = {
            "Content-Type": "text/xml; charset=UTF-8",
            "SOAPAction": action
        }

        try:
            resp = self.http.post(
                self.url,
                data=xml.encode("utf-8"),
                headers=headers,
                timeout=timeout
            )
            resp.raise_for_status()
            text = resp.text
        except Exception as e:
            self._log(f"HTTP error: {e}", "red")
            return None

        # ✅ RESPONSE LOGS
        self._log("========== RESPONSE ==========", "green")
        self._log(text, "green")
        self._log("===================================================================", "black")

        return text

    # -------------------------------
    # Extract text inside <tag>
    # -------------------------------
    def _get_text(self, xml, tag):
        if not xml:
            return None
        try:
            root = ET.fromstring(xml)
        except:
            return None
        for elem in root.iter():
            if elem.tag.endswith(tag):
                return (elem.text or "").strip()
        return None

    # -------------------------------
    # Extract n:result="*"
    # -------------------------------
    def _get_result(self, xml, tag):
        if not xml:
            return None
        try:
            root = ET.fromstring(xml)
        except:
            return None

        for elem in root.iter():
            if elem.tag.endswith(tag):
                for k, v in elem.attrib.items():
                    if k.split("}")[-1] == "result":
                        result = v

                        # Results Codes 
                        if result == "21" and self.log_callback:
                            self.log_callback("⚠️ INVALID SESSION (result=21)", "orange")

                        if result == "5" and self.log_callback:
                            self.log_callback("⚠️ Device NOT OCCUPIED (result=5)", "orange")

                        if result == "11" and self.log_callback:
                            self.log_callback("⚠️ INVALID REQUEST (result=11)", "orange")

                        return result

        return None

    # ======================================================================
    # OPEN
    # ======================================================================
    def open(self):
        xml = f"""<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="{NS_SOAP}" xmlns:bru="{NS_BRU}">
  <soapenv:Header/>
  <soapenv:Body>
    <bru:OpenRequest>
      <bru:SeqNo>OpenTest</bru:SeqNo>
      <bru:User>POS</bru:User>
      <bru:UserPwd>POS</bru:UserPwd>
      <bru:DeviceName>POS</bru:DeviceName>
    </bru:OpenRequest>
  </soapenv:Body>
</soapenv:Envelope>"""

        resp = self._post("OpenOperation", xml, timeout=(2.0, 8.0))
        sid = self._get_text(resp, "SessionID")

        self.session_id = sid or ""
        return self.session_id, resp

    # ======================================================================
    # OCCUPY
    # ======================================================================
    def occupy(self):
        xml = f"""<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="{NS_SOAP}" xmlns:bru="{NS_BRU}">
  <soapenv:Header/>
  <soapenv:Body>
    <bru:OccupyRequest>
      <bru:SeqNo>OccupyTest</bru:SeqNo>
      <bru:SessionID>{self.session_id}</bru:SessionID>
    </bru:OccupyRequest>
  </soapenv:Body>
</soapenv:Envelope>"""

        resp = self._post("OccupyOperation", xml, timeout=(2.0, 8.0))
        return self._get_result(resp, "OccupyResponse"), resp

    # ======================================================================
    # RELEASE
    # ======================================================================
    def release(self):
        xml = f"""<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="{NS_SOAP}" xmlns:bru="{NS_BRU}">
  <soapenv:Header/>
  <soapenv:Body>
    <bru:ReleaseRequest>
      <bru:SeqNo>ReleaseTest</bru:SeqNo>
      <bru:SessionID>{self.session_id}</bru:SessionID>
    </bru:ReleaseRequest>
  </soapenv:Body>
</soapenv:Envelope>"""

        resp = self._post("ReleaseOperation", xml, timeout=(2.0, 8.0))
        return self._get_result(resp, "ReleaseResponse"), resp

    # ======================================================================
    # CLOSE
    # ======================================================================
    def close(self):
        xml = f"""<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="{NS_SOAP}" xmlns:bru="{NS_BRU}">
  <soapenv:Header/>
  <soapenv:Body>
    <bru:CloseRequest>
      <bru:SeqNo>CloseTest</bru:SeqNo>
      <bru:SessionID>{self.session_id}</bru:SessionID>
    </bru:CloseRequest>
  </soapenv:Body>
</soapenv:Envelope>"""

        resp = self._post("CloseOperation", xml, timeout=(2.0, 8.0))
        return self._get_result(resp, "CloseResponse"), resp

    # ======================================================================
    # STATUS (SILENT MODE SUPPORTED)
    # ======================================================================
    def status(self, seq="StatusTest", silent=False):

        xml = f"""<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="{NS_SOAP}" xmlns:bru="{NS_BRU}">
  <soapenv:Header/>
  <soapenv:Body>
    <bru:StatusRequest>
      <bru:SeqNo>{seq}</bru:SeqNo>
      <bru:SessionID>{self.session_id}</bru:SessionID>
      <bru:Option bru:type="1"/>
      <bru:RequireVerification bru:type="1"/>
    </bru:StatusRequest>
  </soapenv:Body>
</soapenv:Envelope>"""

        if silent:
            # ✅ silent mode bypasses _post() → NO LOGS
            try:
                resp = self.http.post(
                    self.url,
                    data=xml.encode("utf-8"),
                    headers={"Content-Type": "text/xml; charset=UTF-8", "SOAPAction": "GetStatus"},
                    timeout=(2.0, 8.0)
                )
                return self._get_result(resp.text, "StatusResponse"), resp.text
            except:
                return None, None

        # ✅ Normal logged mode for manual GetStatus button
        resp = self._post("GetStatus", xml, timeout=(2.0, 8.0))
        return self._get_result(resp, "StatusResponse"), resp

    # ======================================================================
    # CHANGE REQUEST
    # ======================================================================
    def change(self, amount, seqno="ChangeTest", req_id=""):
        xml = f"""<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="{NS_SOAP}" xmlns:bru="{NS_BRU}">
  <soapenv:Header/>
  <soapenv:Body>
    <bru:ChangeRequest>
      <bru:Id>{req_id}</bru:Id>
      <bru:SeqNo>{seqno}</bru:SeqNo>
      <bru:SessionID>{self.session_id}</bru:SessionID>
      <bru:Amount>{amount}</bru:Amount>
    </bru:ChangeRequest>
  </soapenv:Body>
</soapenv:Envelope>"""

        resp = self._post("ChangeOperation", xml, timeout=(2.0, 200.0))
        return self._get_result(resp, "ChangeResponse"), resp

    # ======================================================================
    # RESET
    # ======================================================================
    def reset(self, seqno="ResetTest"):

        xml = f"""<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="{NS_SOAP}" xmlns:bru="{NS_BRU}">
  <soapenv:Header/>
  <soapenv:Body>
    <bru:ResetRequest>
      <bru:SeqNo>{seqno}</bru:SeqNo>
      <bru:SessionID>{self.session_id}</bru:SessionID>
    </bru:ResetRequest>
  </soapenv:Body>
</soapenv:Envelope>"""

        resp = self._post("ResetOperation", xml, timeout=(2.0, 300.0))
        return self._get_result(resp, "ResetResponse"), resp

    # ======================================================================
    # CHANGE CANCEL
    # ======================================================================
    def cancel_change(self, seqno="CancelTest", req_id="", option_type="1"):

        xml = f"""<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="{NS_SOAP}" xmlns:bru="{NS_BRU}">
  <soapenv:Header/>
  <soapenv:Body>
    <bru:ChangeCancelRequest>
      <bru:Id>{req_id}</bru:Id>
      <bru:SeqNo>{seqno}</bru:SeqNo>
      <bru:SessionID>{self.session_id}</bru:SessionID>
      <Option bru:type="{option_type}"/>
    </bru:ChangeCancelRequest>
  </soapenv:Body>
</soapenv:Envelope>"""

        resp = self._post("ChangeCancelOperation", xml, timeout=(5.0, 120.0))
        return self._get_result(resp, "ChangeCancelResponse"), resp