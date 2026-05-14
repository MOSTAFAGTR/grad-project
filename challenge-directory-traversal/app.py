from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)
BASE_DIR = Path("files")


def _seed_files() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    report = BASE_DIR / "report.txt"
    if not report.exists():
        report.write_text("Quarterly report contents", encoding="utf-8")


_seed_files()


@app.route("/file")
def read_file():
    filename = request.args.get("name", "")
    if not filename:
        return jsonify({"error": "name is required"}), 400

    # Vulnerable on purpose: direct concatenation with user path.
    file_path = BASE_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        return jsonify({"error": "file not found"}), 404

    content = file_path.read_text(encoding="utf-8", errors="ignore")
    return jsonify({"content": content}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
