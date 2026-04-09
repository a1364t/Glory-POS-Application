# bruebox_client.py
"""
Client for communicating with Glory BrueBox cash recycler devices via SOAP over HTTP.
Handles session management, device control, and transaction operations.
"""

import requests
import xml.etree.ElementTree as ET

# SOAP namespace constants for XML envelope and BrueBox schema
NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
NS_BRU  = "http://www.glory.co.jp/bruebox.xsd"


class BrueBoxClient:
    """
    SOAP client for Glory BrueBox cash handling devices.
    Manages HTTP connections, session state, and XML-based command execution.
    """

    def __init__(self, ip_address="192.168.0.25"):
        """
        Initialize the client with device IP address.
        
        Args:
            ip_address (str): IP address of the BrueBox device
        """
        self.ip_address = ip_address
        self.url = f"http://{ip_address}/axis2/services/BrueBoxService"
        self.session_id = None  # Current session ID from device
        self.log_callback = None  # Callback function for logging messages
        self.http = requests.Session()  # Persistent HTTP session for connection reuse

    # -------------------------------
    # Dynamic IP assignment
    # -------------------------------
    def set_ip(self, ip):
        """
        Update the device IP address and reconstruct the service URL.
        
        Args:
            ip (str): New IP address for the device
        """
        self.ip_address = ip
        self.url = f"http://{ip}/axis2/services/BrueBoxService"
        if self.log_callback:
            self.log_callback(f"✅ IP set to: {self.url}", "blue")

    # -------------------------------
    # Internal logger
    # -------------------------------
    def _log(self, msg, color="black"):
        """
        Internal logging method that calls the configured callback.
        
        Args:
            msg (str): Message to log
            color (str): Color for the message display
        """
        if self.log_callback:
            self.log_callback(msg, color)

    # -------------------------------
    # POST Helper (FULL LOGGING)
    # -------------------------------
    def _post(self, action, xml, *, timeout=(2.0, 30.0)):
        """
        Send SOAP request to the device and handle response.
        Includes comprehensive logging for debugging.
        
        Args:
            action (str): SOAPAction header value
            xml (str): SOAP XML request body
            timeout (tuple): (connect_timeout, read_timeout) in seconds
            
        Returns:
            str: XML response text, or None on error
        """

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
        """
        Parse XML response and extract text content from specified tag.
        
        Args:
            xml (str): XML response string
            tag (str): Tag name to search for
            
        Returns:
            str: Text content of the tag, or None if not found
        """
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
        """
        Parse XML response and extract result code from specified response tag.
        Includes logging for common error codes.
        
        Args:
            xml (str): XML response string
            tag (str): Response tag name to search for
            
        Returns:
            str: Result code attribute value, or None if not found
        """
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
    # OPEN - Establish connection and get session ID
    # ======================================================================
    def open(self):
        """
        Open a new session with the BrueBox device.
        This must be called before other operations.
        
        Returns:
            tuple: (session_id, response_xml) - Session ID on success, None on failure
        """
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
    # OCCUPY - Lock device for exclusive use
    # ======================================================================
    def occupy(self):
        """
        Occupy the device for exclusive access by this session.
        Required before performing transactions.
        
        Returns:
            tuple: (result_code, response_xml) - "0" on success
        """
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
    # RELEASE - Unlock device from exclusive use
    # ======================================================================
    def release(self):
        """
        Release the device from exclusive access.
        Allows other sessions to occupy the device.
        
        Returns:
            tuple: (result_code, response_xml) - "0" on success
        """
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
    # CLOSE - End the session
    # ======================================================================
    def close(self):
        """
        Close the current session with the device.
        Cleans up resources and allows new sessions.
        
        Returns:
            tuple: (result_code, response_xml) - "0" on success
        """
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
    # STATUS - Check device status
    # ======================================================================
    def status(self, seq="StatusTest", silent=False):
        """
        Query the current status of the BrueBox device.
        
        Args:
            seq (str): Sequence number for the request
            silent (bool): If True, suppress logging (used for heartbeat)
            
        Returns:
            tuple: (result_code, response_xml) - "0" indicates device is ready
        """

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
            # Silent mode bypasses logging for background status checks
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

        # Normal logged mode for manual status checks
        resp = self._post("GetStatus", xml, timeout=(2.0, 8.0))
        return self._get_result(resp, "StatusResponse"), resp

    # ======================================================================
    # CHANGE REQUEST - Deposit or dispense cash
    # ======================================================================
    def change(self, amount, seqno="ChangeTest", req_id=""):
        """
        Perform a cash transaction (deposit or dispense).
        
        Args:
            amount (int): Amount in cents (positive for deposit, negative for dispense)
            seqno (str): Sequence number for the request
            req_id (str): Request ID for tracking
            
        Returns:
            tuple: (result_code, response_xml) - "0" on success
        """
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
    # RESET - Reset device to initial state
    # ======================================================================
    def reset(self, seqno="ResetTest"):
        """
        Reset the BrueBox device to its initial state.
        Clears any pending operations or errors.
        
        Args:
            seqno (str): Sequence number for the request
            
        Returns:
            tuple: (result_code, response_xml) - "0" on success
        """

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
    # CHANGE CANCEL - Cancel current transaction
    # ======================================================================
    def cancel_change(self, seqno="CancelTest", req_id="", option_type="1"):
        """
        Cancel the current cash transaction in progress.
        
        Args:
            seqno (str): Sequence number for the request
            req_id (str): Request ID of the transaction to cancel
            option_type (str): Option type for cancel operation
            
        Returns:
            tuple: (result_code, response_xml) - "0" on success
        """

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