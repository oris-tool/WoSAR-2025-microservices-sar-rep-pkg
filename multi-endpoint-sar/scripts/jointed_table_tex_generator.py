import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from itertools import cycle
import argparse
import sys
import os
from pathlib import Path
import logging

def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def validate_csv_data(df, logger):
    """Validate CSV data structure and content"""
    required_columns = ['Endpoint', 'Configuration', 'Pool Size', 'Reliability', 'Unavailability']
    
    # Check for required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"CSV mancante delle colonne richieste: {missing_columns}")
    
    # Check for valid endpoints
    valid_endpoints = {'A', 'B'}
    actual_endpoints = set(df['Endpoint'].unique())
    if not actual_endpoints.issubset(valid_endpoints):
        logger.warning(f"Endpoint non standard trovati: {actual_endpoints - valid_endpoints}")
    
    # Check for valid reliability values (should be between 0 and 1)
    invalid_reliability = df[(df['Reliability'] < 0) | (df['Reliability'] > 1)]
    if not invalid_reliability.empty:
        logger.warning(f"Valori di Reliability fuori range [0,1] trovati: {len(invalid_reliability)} righe")
    
    # Check for negative unavailability
    negative_unavailability = df[df['Unavailability'] < 0]
    if not negative_unavailability.empty:
        logger.warning(f"Valori negativi di Unavailability trovati: {len(negative_unavailability)} righe")
    
    logger.info(f"Dataset validato: {len(df)} righe, {len(df.columns)} colonne")
    return True

def find_configuration_pairs(df, target_pool_size=None, logger=None):
    """Find configuration pairs based on pool size matching"""
    pairs = []
    configurations = df['Configuration'].unique()
    
    for config in configurations:
        if config == 'A+B':
            continue
            
        config_data = df[df['Configuration'] == config]
        endpoint_a_data = config_data[config_data['Endpoint'] == 'A']
        endpoint_b_data = config_data[config_data['Endpoint'] == 'B']
        
        # If target_pool_size is not specified, try to infer it from A+B configuration
        if target_pool_size is None:
            ab_config = df[df['Configuration'] == 'A+B']
            if not ab_config.empty:
                target_pool_size = ab_config['Pool Size'].iloc[0] * 2  # Assuming A+B has same pool size for both
            else:
                # Default fallback
                target_pool_size = 10
        
        for _, a_row in endpoint_a_data.iterrows():
            target_b_pool_size = target_pool_size - a_row['Pool Size']
            b_match = endpoint_b_data[endpoint_b_data['Pool Size'] == target_b_pool_size]
            
            if not b_match.empty:
                b_row = b_match.iloc[0]
                pair_name = f"A{a_row['Pool Size']}B{b_row['Pool Size']}"
                pairs.append({
                    'config': config,
                    'pair_name': pair_name,
                    'a_data': a_row,
                    'b_data': b_row
                })
                if logger:
                    logger.debug(f"Trovata coppia: {pair_name}")
    
    return pairs

def create_reliability_plot(csv_file_path, output_path=None, figure_size=(12, 8), 
                          output_format='pdf', dpi=300, target_pool_size=None, 
                          show_grid=True, logger=None):
    """
    Create reliability plot from CSV data
    
    Args:
        csv_file_path (str): Path to the CSV file
        output_path (str): Output path for the plot (optional)
        figure_size (tuple): Figure size as (width, height)
        output_format (str): Output format ('pdf', 'png', 'svg', etc.)
        dpi (int): Resolution for raster formats
        target_pool_size (int): Target total pool size for pairing (optional)
        show_grid (bool): Whether to show grid
        logger: Logger instance
    
    Returns:
        str: Path to the saved plot file
    """
    
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Load data
        logger.info(f"Caricamento dati da: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        logger.info(f"Dataset caricato: {len(df)} righe")
        
        # Validate data
        validate_csv_data(df, logger)
        
        # Calculate Unreliability
        df['Unreliability'] = 1 - df['Reliability']
        logger.debug("Unreliability calcolata")
        
        # Setup plot
        plt.figure(figsize=figure_size)
        logger.debug(f"Plot inizializzato con dimensioni: {figure_size}")
        
        # Colors and markers for different configurations
        colors = cycle(['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                       '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'])
        markers = cycle(['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h'])
        
        # Group by configuration
        configurations = df['Configuration'].unique()
        logger.info(f"Configurazioni trovate: {list(configurations)}")
        
        plotted_configs = []
        
        for config in configurations:
            config_data = df[df['Configuration'] == config].copy()
            color = next(colors)
            marker = next(markers)
            
            if config == 'A+B':
                # For A+B, simply connect A and B
                endpoint_a = config_data[config_data['Endpoint'] == 'A']
                endpoint_b = config_data[config_data['Endpoint'] == 'B']
                
                if not endpoint_a.empty and not endpoint_b.empty:
                    # Plot points
                    plt.scatter(endpoint_a['Unreliability'], endpoint_a['Unavailability'], 
                               color=color, marker=marker, s=100, label=f'{config} - A', alpha=0.8)
                    plt.scatter(endpoint_b['Unreliability'], endpoint_b['Unavailability'], 
                               color=color, marker=marker, s=100, label=f'{config} - B', 
                               alpha=0.8, facecolors='none', edgecolors=color, linewidth=2)
                    
                    # Connection line
                    plt.plot([endpoint_a['Unreliability'].iloc[0], endpoint_b['Unreliability'].iloc[0]], 
                            [endpoint_a['Unavailability'].iloc[0], endpoint_b['Unavailability'].iloc[0]], 
                            color=color, alpha=0.6, linestyle='-', linewidth=2)
                    
                    plotted_configs.append(config)
                    logger.debug(f"Plottata configurazione A+B")
            
            else:
                # For other configurations, pair A and B based on total pool size
                pairs = find_configuration_pairs(df[df['Configuration'] == config], 
                                               target_pool_size, logger)
                
                config_plotted = False
                for pair in pairs:
                    a_row = pair['a_data']
                    b_row = pair['b_data']
                    pair_name = pair['pair_name']
                    
                    # Plot points
                    plt.scatter(a_row['Unreliability'], a_row['Unavailability'], 
                               color=color, marker=marker, s=100, alpha=0.8)
                    plt.scatter(b_row['Unreliability'], b_row['Unavailability'], 
                               color=color, marker=marker, s=100, alpha=0.8, 
                               facecolors='none', edgecolors=color, linewidth=2)
                    
                    # Connection line
                    plt.plot([a_row['Unreliability'], b_row['Unreliability']], 
                            [a_row['Unavailability'], b_row['Unavailability']], 
                            color=color, alpha=0.6, linestyle='-', linewidth=2)
                    
                    # Label only once per configuration
                    if not config_plotted:
                        plt.scatter([], [], color=color, marker=marker, s=100, 
                                   label=f'{pair_name}', alpha=0.8)
                        config_plotted = True
                        plotted_configs.append(pair_name)
                        logger.debug(f"Plottata configurazione: {pair_name}")
        
        # Plot customization
        plt.xlabel('Unreliability', fontsize=12, fontweight='bold')
        plt.ylabel('Unavailability', fontsize=12, fontweight='bold')
        plt.title('Unreliability vs Unavailability per Configurazioni di Endpoint', 
                  fontsize=14, fontweight='bold', pad=20)
        
        # Grid
        if show_grid:
            plt.grid(True, alpha=0.3, linestyle='--')
        
        # Legend
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, 
                   fancybox=True, shadow=True, fontsize=10)
        
        # Axis formatting
        plt.ticklabel_format(style='scientific', axis='both', scilimits=(0,0))
        
        # Tight layout
        plt.tight_layout()
        
        # Determine output path
        if output_path is None:
            input_path = Path(csv_file_path)
            output_path = input_path.parent / f"{input_path.stem}_reliability_plot.{output_format}"
        
        # Save plot
        plt.savefig(output_path, format=output_format, dpi=dpi, bbox_inches='tight')
        logger.info(f"Plot salvato in: {output_path}")
        
        # Print statistics
        logger.info("=== STATISTICHE DATASET ===")
        logger.info(f"Numero totale di configurazioni: {len(configurations)}")
        logger.info(f"Configurazioni plottate: {len(plotted_configs)}")
        logger.info(f"Range Unreliability: {df['Unreliability'].min():.6f} - {df['Unreliability'].max():.6f}")
        logger.info(f"Range Unavailability: {df['Unavailability'].min():.6f} - {df['Unavailability'].max():.6f}")
        logger.info(f"Configurazioni presenti: {', '.join(configurations)}")
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Errore durante la creazione del plot: {str(e)}")
        raise

def parse_figure_size(size_str):
    """Parse figure size string like '12,8' into tuple"""
    try:
        width, height = map(float, size_str.split(','))
        return (width, height)
    except:
        raise argparse.ArgumentTypeError("Dimensioni figura devono essere nel formato 'larghezza,altezza' (es. '12,8')")

def main():
    """Main function for command-line execution"""
    parser = argparse.ArgumentParser(
        description='Genera un plot di Unreliability vs Unavailability da dati CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Esempi di utilizzo:
  %(prog)s data.csv
  %(prog)s data.csv -o output_plot.pdf
  %(prog)s data.csv -f png --dpi 300 --size 14,10
  %(prog)s data.csv --target-pool-size 16 --no-grid -v
        '''
    )
    
    # Required arguments
    parser.add_argument('csv_file', 
                       help='Path al file CSV contenente i dati di reliability')
    
    # Optional arguments
    parser.add_argument('-o', '--output', 
                       help='Path di output per il plot (default: stesso nome del CSV con suffisso)')
    
    parser.add_argument('-f', '--format', 
                       choices=['pdf', 'png', 'svg', 'jpg', 'eps'], 
                       default='pdf',
                       help='Formato di output (default: pdf)')
    
    parser.add_argument('--dpi', 
                       type=int, 
                       default=300,
                       help='Risoluzione per formati raster (default: 300)')
    
    parser.add_argument('--size', 
                       type=parse_figure_size, 
                       default=(12, 8),
                       metavar='W,H',
                       help='Dimensioni figura come larghezza,altezza (default: 12,8)')
    
    parser.add_argument('--target-pool-size', 
                       type=int,
                       help='Pool size totale target per l\'accoppiamento delle configurazioni')
    
    parser.add_argument('--no-grid', 
                       action='store_true',
                       help='Disabilita la griglia nel plot')
    
    parser.add_argument('-v', '--verbose', 
                       action='store_true',
                       help='Output verboso con informazioni di debug')
    
    parser.add_argument('--version', 
                       action='version', 
                       version='%(prog)s 1.0.0')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    try:
        # Check if input file exists
        if not os.path.exists(args.csv_file):
            logger.error(f"File CSV non trovato: {args.csv_file}")
            sys.exit(1)
        
        # Check if input file is readable
        if not os.access(args.csv_file, os.R_OK):
            logger.error(f"File CSV non leggibile: {args.csv_file}")
            sys.exit(1)
        
        logger.info("=== AVVIO ANALISI RELIABILITY ===")
        logger.info(f"File input: {args.csv_file}")
        logger.info(f"Formato output: {args.format}")
        logger.info(f"Dimensioni figura: {args.size}")
        
        # Create plot
        output_path = create_reliability_plot(
            csv_file_path=args.csv_file,
            output_path=args.output,
            figure_size=args.size,
            output_format=args.format,
            dpi=args.dpi,
            target_pool_size=args.target_pool_size,
            show_grid=not args.no_grid,
            logger=logger
        )
        
        logger.info("=== ANALISI COMPLETATA ===")
        logger.info(f"Plot salvato in: {output_path}")
        
        print(f"\n✓ Plot generato con successo!")
        print(f"📁 File salvato: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File non trovato: {e}")
        sys.exit(1)
    except pd.errors.EmptyDataError:
        logger.error("Il file CSV è vuoto")
        sys.exit(1)
    except pd.errors.ParserError as e:
        logger.error(f"Errore nel parsing del CSV: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Errore nei dati: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Errore imprevisto: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
