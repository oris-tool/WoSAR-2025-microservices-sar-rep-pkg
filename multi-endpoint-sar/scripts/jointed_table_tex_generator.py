import csv
import sys
import os


def truncate_float(val, digits=5):
    try:
        f = float(val)
        return f"{float(val):.{digits}f}"
    except Exception:
        return val


if len(sys.argv) != 2:
    print("Uso: python csv2latex_smart.py <percorso/file.csv>")
    sys.exit(1)

csv_path = sys.argv[1]
base_dir = os.path.dirname(csv_path)
base_name = os.path.splitext(os.path.basename(csv_path))[0]
tex_out = os.path.join(base_dir, base_name + "_table.tex")

# Leggi tutte le righe
rows = []
with open(csv_path, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for r in reader:
        # Troncatura numerica
        for key in ["Reliability", "Unavailability", "Aging Contribution", "Resource Usage"]:
            r[key] = truncate_float(r[key])
        r["Pool Size"] = int(r["Pool Size"])
        rows.append(r)

# Trova le righe jointed (2 righe, una per ciascun endpoint)
jointed_rows = [r for r in rows if "+" in r["Configuration"]]
if len(jointed_rows) != 2:
    print("Errore: atteso esattamente due righe jointed!")
    sys.exit(1)
endpointA = jointed_rows[0]["Endpoint"]
endpointB = jointed_rows[1]["Endpoint"]
total_pool = jointed_rows[0]["Pool Size"]
if jointed_rows[1]["Pool Size"] != total_pool:
    print("Errore: i Pool Size delle due jointed non coincidono!")
    sys.exit(1)

# Crea dizionari per accesso veloce alle righe A e B standalone
standaloneA = {
    (r["Pool Size"]): r
    for r in rows
    if r["Configuration"] == endpointA and r["Endpoint"] == endpointA
}
standaloneB = {
    (r["Pool Size"]): r
    for r in rows
    if r["Configuration"] == endpointB and r["Endpoint"] == endpointB
}

# Inizio sezione LaTeX
# latex_head = r"""\begin{table}[htb]
# \centering
# \begin{tabular}{l|ccc|ccc}
# \toprule
# Configuration & \multicolumn{3}{c|}{Endpoint %s} & \multicolumn{3}{c}{Endpoint %s} \\
#  & Reliability & Unavailability & Resource Usage & Reliability & Unavailability & Resource Usage \\
# \midrule
# """ % (
#     endpointA,
#     endpointB,
# )
# latex_head = r"""\begin{table*}[htb]
# \centering
# \begin{tabular}{lcccccc}
# \toprule
# \multirow{2}{*}{Configuration} & \multicolumn{3}{c}{\textbf{Endpoint """ + endpointA + r"""}} & \multicolumn{3}{c}{\textbf{Endpoint """ + endpointB + r"""}} \\
# \cmidrule(lr){2-7}
#    & Reliability & Unavailability & Resource Usage & Reliability & Unavailability & Resource Usage \\
# \midrule
# """

latex_head = r"""
 \begin{table*}[htb]
\centering
\begin{tabular}{lcccccccc}
\toprule
\multirow{2}{*}{Configuration} & \multicolumn{4}{c}{\textbf{Endpoint A}} & \multicolumn{4}{c}{\textbf{Endpoint B}} \\
\cmidrule(lr){2-9}
   & Reliability & Unavailability & Aging Contribution & Resource Usage & Reliability & Unavailability & Aging Contribution & Resource Usage \\
\midrule
"""




rows_latex = []

# Riga jointed
valsA = [
    jointed_rows[0][c] for c in ["Reliability", "Unavailability", "Aging Contribution", "Resource Usage"]
]
valsB = [
    jointed_rows[1][c] for c in ["Reliability", "Unavailability", "Aging Contribution", "Resource Usage"]
]
rows_latex.append("Jointed & %s & %s \\\\" % (" & ".join(valsA), " & ".join(valsB)))

# Standalone combinazioni da 1 a total_pool-1
for k in range(1, total_pool):
    if k in standaloneA and (total_pool - k) in standaloneB:
        rA = standaloneA[k]
        rB = standaloneB[total_pool - k]
        conf_descr = "%s(%d),%s(%d)" % (endpointA, k, endpointB, total_pool - k)
        valsA = [rA[c] for c in ["Reliability", "Unavailability", "Aging Contribution", "Resource Usage"]]
        valsB = [rB[c] for c in ["Reliability", "Unavailability", "Aging Contribution", "Resource Usage"]]
        rows_latex.append(
            "%s & %s & %s \\\\" % (conf_descr, " & ".join(valsA), " & ".join(valsB))
        )

latex_foot = r"""\bottomrule
\end{tabular}
\caption{Jointed and all possible standalone splits for endpoints %s and %s.}
\label{tab:endpoint_jointed_splits}
\end{table*}
""" % (
    endpointA,
    endpointB,
)

with open(tex_out, "w", encoding="utf-8") as f:
    f.write(latex_head + "\n".join(rows_latex) + "\n" + latex_foot)

print(f"Tabella avanzata generata in '{tex_out}'")
