import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="Plot reliability vs workload for different aging rates.")
    parser.add_argument("csv_path", help="Percorso al file CSV con i dati")
    args = parser.parse_args()

    df = pd.read_csv(args.csv_path)
    aging_rates = sorted(df["Aging Rate"].unique())

    plt.figure(figsize=(10, 6))

    for ar in aging_rates:
        mask = df["Aging Rate"] == ar
        plt.plot(
            df[mask]["Arrival Rate"],
            df[mask]["Unreliability"],
            marker="o",
            label=f"Aging Rate = {ar}"
        )

    plt.xlabel("Arrival Rate (Workload)")
    plt.ylabel("Unreliability")
    plt.title("Unreliability vs Workload for different Aging Rates")
    plt.legend(title="Aging Rate")
    plt.grid(True, which='both', linestyle='--', alpha=0.6)
    plt.tight_layout()

    # Path della cartella dove si trova il file CSV
    csv_dir = os.path.dirname(os.path.abspath(args.csv_path))
    output_path = os.path.join(csv_dir, "reliability_vs_workload.png")

    plt.savefig(output_path, dpi=300)
    print(f"Grafico salvato come: {output_path}")

    plt.show()

if __name__ == "__main__":
    main()