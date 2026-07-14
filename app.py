from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Fixed high-level categories -> possible column names in uploaded file
CATEGORY_MAP = {
    "Gender":       ["gender", "sex"],
    "Quota":        ["quota"],
    "Blood Group":  ["blood group", "bloodgroup", "blood_group", "blood"],
    "Community":    ["community", "caste"],
    "Residence":    ["hosteller/dayscholar", "residence", "hosteller", "dayscholar", "stay"],
}

DATA = {"df": None}


def find_col(df, aliases):
    lower = {c.lower().strip(): c for c in df.columns}
    for a in aliases:
        if a in lower:
            return lower[a]
    return None


def build_categories(df):
    out = {}
    for label, aliases in CATEGORY_MAP.items():
        col = find_col(df, aliases)
        if col is None:
            continue
        counts = (
            df[col].dropna().astype(str).str.strip().value_counts().to_dict()
        )
        out[label] = {"column": col, "values": counts}
    return out


def df_payload(df):
    return {
        "columns": list(df.columns),
        "rows": df.fillna("").astype(str).to_dict(orient="records"),
        "total": int(len(df)),
        "categories": build_categories(df),
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file"}), 400
    path = os.path.join(UPLOAD_DIR, f.filename)
    f.save(path)
    if f.filename.lower().endswith(".csv"):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)
    df.columns = [str(c).strip() for c in df.columns]
    DATA["df"] = df
    return jsonify(df_payload(df))


@app.route("/filter")
def filter_rows():
    df = DATA["df"]
    if df is None:
        return jsonify({"error": "Upload a file first"}), 400
    label = request.args.get("category")
    value = request.args.get("value")
    aliases = CATEGORY_MAP.get(label, [])
    col = find_col(df, aliases)
    if not col:
        return jsonify({"error": "Category not found"}), 404
    sub = df[df[col].astype(str).str.strip().str.lower() == value.strip().lower()]
    return jsonify({
        "columns": list(sub.columns),
        "rows": sub.fillna("").astype(str).to_dict(orient="records"),
        "total": int(len(sub)),
    })


@app.route("/search")
def search():
    df = DATA["df"]
    if df is None:
        return jsonify({"error": "Upload a file first"}), 400
    q = (request.args.get("q") or "").strip().lower()
    field = request.args.get("field", "all")  # all | name | rollno
    if not q:
        return jsonify(df_payload(df))

    if field == "name":
        col = find_col(df, ["name", "student name", "full name"])
        mask = df[col].astype(str).str.lower().str.contains(q, na=False) if col else False
    elif field == "rollno":
        col = find_col(df, ["roll no", "rollno", "roll number", "register no", "reg no"])
        mask = df[col].astype(str).str.lower().str.contains(q, na=False) if col else False
    else:
        mask = df.apply(lambda r: r.astype(str).str.lower().str.contains(q, na=False).any(), axis=1)

    sub = df[mask] if hasattr(mask, "any") else df.iloc[0:0]
    return jsonify({
        "columns": list(sub.columns),
        "rows": sub.fillna("").astype(str).to_dict(orient="records"),
        "total": int(len(sub)),
    })


if __name__ == "__main__":
    app.run(debug=True)
