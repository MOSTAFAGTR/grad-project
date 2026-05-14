import xml.etree.ElementTree as ET
import re
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/parse", methods=["POST"])
def parse_xml():
    payload = request.get_json(silent=True) or {}
    xml_input = payload.get("xml", "")
    if not xml_input:
        return jsonify({"error": "xml is required"}), 400

    entity_matches = re.findall(r"<!ENTITY\s+([A-Za-z0-9_:-]+)\s+SYSTEM\s+['\"]file://([^'\"]+)['\"]>", xml_input, flags=re.IGNORECASE)
    if entity_matches:
        resolved_xml = xml_input
        extracted = ""
        for name, file_path in entity_matches:
            try:
                value = Path(file_path).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                value = ""
            resolved_xml = resolved_xml.replace(f"&{name};", value)
            extracted += value
        cleaned = re.sub(r"<!DOCTYPE[^>]*\[[\s\S]*?\]>", "", resolved_xml, flags=re.IGNORECASE)
        return jsonify(
            {
                "parsed_output": cleaned,
                "sensitive_data": extracted or None,
            }
        ), 200

    try:
        parsed = ET.fromstring(xml_input)
        return jsonify({"parsed_output": ET.tostring(parsed, encoding="unicode")}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
