from flask import Flask, render_template, request, Response
from datetime import datetime
import csv, io, xml.etree.ElementTree as ET
import requests

app = Flask(__name__)
API_URL = "https://telemetriaws1.ana.gov.br/ServiceANA.asmx/DadosHidrometeorologicos"
TIMEOUT_SECONDS = 45
FIELD_ALIASES = {
    "station": {"codestacao", "codigoestacao", "estacao"},
    "datetime": {"datahora", "data_hora", "dataleitura", "data"},
    "rain": {"chuva", "precipitacao", "precipitação", "chuva_mm", "precipitacaomm"},
}

def local_name(tag):
    return tag.rsplit("}", 1)[-1].split(":")[-1].strip()

def clean_text(value):
    return (value or "").strip()

def parse_xml_records(xml_text):
    root = ET.fromstring(xml_text)
    records = []
    def rows_from_tree(tree):
        for node in tree.iter():
            children = [child for child in list(node) if list(child) == []]
            if not children:
                continue
            row = {local_name(child.tag).strip().lower(): clean_text(child.text) for child in children}
            if row: records.append(row)
    rows_from_tree(root)
    nested_xml = []
    for node in root.iter():
        if local_name(node.tag).lower() in {"dadoshidrometeorologicosresult", "string", "diffgram"} and node.text and node.text.strip().startswith("<"):
            nested_xml.append(node.text.strip())
    for embedded in nested_xml:
        try: rows_from_tree(ET.fromstring(embedded))
        except ET.ParseError: pass
    unique, seen = [], set()
    for row in records:
        key = tuple(sorted(row.items()))
        if key not in seen:
            seen.add(key); unique.append(row)
    return unique

def find_field(row, aliases):
    for key, value in row.items():
        if key.strip().lower() in aliases: return value
    for key, value in row.items():
        normalized = key.strip().lower().replace("_", "")
        for alias in aliases:
            if alias.replace("_", "") in normalized: return value
    return ""

def format_date_time(raw):
    if not raw: return "", ""
    value = raw.strip()
    formats = ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M", "%d/%m/%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.strftime("%d/%m/%Y"), parsed.strftime("%H:%M:%S") if "%H" in fmt else ""
        except ValueError: pass
    if "T" in value:
        date_part, time_part = value.split("T", 1); return date_part, time_part.rstrip("Z")
    if " " in value:
        date_part, time_part = value.split(" ", 1); return date_part, time_part
    return value, ""

@app.route("/", methods=["GET", "POST"])
def index():
    records, status, error = [], "Informe a estação e o período para consultar.", ""
    station = request.form.get("station", "").strip()
    start = request.form.get("start", "").strip()
    end = request.form.get("end", "").strip()
    if request.method == "POST":
        if not station.isdigit(): error = "Informe o código numérico da estação."
        else:
            try:
                start_dt = datetime.strptime(start, "%d/%m/%Y")
                end_dt = datetime.strptime(end, "%d/%m/%Y")
                if end_dt < start_dt: raise ValueError("A data final deve ser igual ou posterior à data inicial.")
            except ValueError as exc:
                error = str(exc) or "Informe datas válidas no formato DD/MM/AAAA."
            if not error:
                try:
                    response = requests.get(API_URL, params={"codEstacao": station, "dataInicio": start, "dataFim": end}, timeout=TIMEOUT_SECONDS)
                    response.raise_for_status()
                    rows = parse_xml_records(response.text)
                    rain_field_seen = False
                    for row in rows:
                        raw_dt = find_field(row, FIELD_ALIASES["datetime"])
                        rain = find_field(row, FIELD_ALIASES["rain"])
                        if rain: rain_field_seen = True
                        date_value, time_value = format_date_time(raw_dt)
                        if raw_dt and rain != "":
                            records.append({"station": find_field(row, FIELD_ALIASES["station"]) or station, "date": date_value, "time": time_value, "rain": rain})
                    if records: status = f"{len(records)} registro(s) encontrado(s)."
                    elif rows and not rain_field_seen: status = "A resposta da API não contém um campo reconhecido de chuva/precipitação. Confira os campos retornados pela estação."
                    else: status = "Nenhum registro de precipitação encontrado para o período."
                except requests.RequestException as exc: error = f"Não foi possível consultar a API da ANA: {exc}"
                except ET.ParseError: error = "A resposta recebida da API não pôde ser interpretada como XML."
                except Exception as exc: error = f"Erro inesperado durante a consulta: {exc}"
    return render_template("index.html", records=records, status=status, error=error, station=station, start=start, end=end)

@app.post("/exportar")
def exportar():
    try: payload = request.get_json(force=True)
    except Exception: return {"error": "Dados inválidos."}, 400
    records = payload.get("records", [])
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Código da estação", "Data", "Hora", "Precipitação (mm)"])
    for r in records: writer.writerow([r.get("station", ""), r.get("date", ""), r.get("time", ""), r.get("rain", "")])
    data = "\ufeff" + output.getvalue()
    return Response(data, mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=precipitacao_ana.csv"})

if __name__ == "__main__":
    # Disponível apenas neste computador; não expõe o serviço à rede local.
    app.run(host="127.0.0.1", port=5000, debug=False)
