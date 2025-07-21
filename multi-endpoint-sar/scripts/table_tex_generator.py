import csv
import sys
import os


def truncate_float(val, digits=3):
    """Restituisce il valore numerico troncato a 'digits' decimali."""
    try:
        f = float(val)
        return f"{f:.{digits}f}"
    except Exception:
        return val


if len(sys.argv) != 2:
    print("Uso: python csv2latex.py <percorso/file.csv>")
    sys.exit(1)

csv_path = sys.argv[1]
base_dir = os.path.dirname(csv_path)
base_name = os.path.splitext(os.path.basename(csv_path))[0]
tex_out = os.path.join(base_dir, base_name + ".tex")

latex_table_head = r"""\begin{table}[htb]
\centering
\begin{tabular}{l c c c c c c}
\toprule
"""

latex_table_foot = r"""\bottomrule
\end{tabular}
\caption{Table generated from CSV.}
\label{tab:model_params}
\end{table}
"""

with open(csv_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    # Usa gli header esattamente come nel file
    headers = reader.fieldnames
    latex_output = [latex_table_head]
    latex_output.append(' & '.join(headers) + r' \\')
    latex_output.append(r"\midrule")
    for row in reader:
        row_data = []
        for col in headers:
            if col in ["Reliability", "Unavailability", "Aging Contribution", "Resource Usage"]:
                val = truncate_float(row[col], 3)
            else:
                val = row[col]
            row_data.append(val)
        latex_output.append(' & '.join(row_data) + r" \\")
    latex_output.append(latex_table_foot)

latex_code = "\n".join(latex_output)

with open(tex_out, "w", encoding="utf-8") as f:
    f.write(latex_code)

print(f"Table tex genereted at '{tex_out}'")
