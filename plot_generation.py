"""
This file contains the functions that deal with plotting the timing data. The
functions in this file generate scatter plots comparing the recorded statistics
at the module and package level.
"""

import os
from typing import List, Optional
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from constants import (CB_COLORS, DEFAULT_PLOT_STYLE, MODULE_STATS_FILE,
                       PACKAGE_STATS_FILE, PACKAGE_STYLE, PLOT_STYLES,
                       PLOTS_DIR)


def latex_float(f: float) -> str:
    """
    Formats a float in scientific notation to a LaTeX formatted string.

    Args:
        f: The float to format

    Returns:
        A LaTeX formatted string representing the float
    """
    float_str = f"{f:.3g}"
    if "e" in float_str:
        base, exp = float_str.split("e")
        return rf"{base} \cdot 10^{{{exp}}}"
    else:
        return float_str


def plot_metric_vs_metric(
    df: pd.DataFrame,
    x: str,
    y: str,
    xlabel: str,
    ylabel: str,
    title: str,
    filename: str,
    guide_pcts: List[int],
    guide_label: str,
    log: Optional[bool] = False,
    module: Optional[bool] = False
) -> None:
    """
    Plots a metric against another metric. The plot is saved as a PDF in the
    `plots` directory.

    Args:
        df: The dataframe containing the data to plot
        x: The column to plot on the x-axis
        y: The column to plot on the y-axis
        xlabel: The label for the x-axis
        ylabel: The label for the y-axis
        title: The title of the plot
        filename: The name of the file to save the plot as
        guide_pcts: The percentages to plot guide lines for
        guide_label: The label for the guide lines
        log: Whether to use a log scale for the axes
        module: Whether to plot by module or package

    Returns:
        None
    """

    fig, ax = plt.subplots()

    if module:
        # For module plot, group by extension and plot each group with a different style
        for ext, ext_df in df.groupby("extension"):
            style = PLOT_STYLES.get(ext, DEFAULT_PLOT_STYLE)
            ax.scatter(ext_df[x], ext_df[y], alpha = 0.5, label = ext, **style)
    else:
        # For package plot, plot all packages with the same style
        ax.scatter(df[x], df[y], **PACKAGE_STYLE)

    if log:
        # Setting log scale for both axes
        ax.set(xscale = "log", yscale = "log")
        # Changing filename to indicate log scale
        filename = filename.replace(".", "_log.")

    # Adding grid lines and setting axis labels and title
    ax.grid(linestyle = "--", linewidth = 0.5)
    ax.set(xlabel = xlabel, ylabel = ylabel, title = title)

    # Clamping axes to the data
    ax.set_xlim(ax.get_xlim())
    ax.set_ylim(ax.get_ylim())

    # Plotting percentage guide lines for each given guide percentage
    x_vals = np.linspace(df[x].min(), df[x].max(), 100)
    # Index of the middle one or two lines, middle lines use loosely dashed style
    middle_guide = [len(guide_pcts) // 2, (len(guide_pcts) - 1) // 2]
    for idx, pct in enumerate(guide_pcts):
        pct_vals = (pct / 100) * x_vals
        linestyle = (0, (5, 10)) if idx in middle_guide else ":"
        label = f"{pct}{guide_label}" if guide_label == "%" else f"{pct:.1e}{guide_label}"
        ax.plot(x_vals, pct_vals, linestyle = linestyle, linewidth = 0.5, color = CB_COLORS["black"], label = label)

    # For graphs with parser percentage on the y-axis, add horizontal lines
    # for the average and median parser percentage
    if y == "parser_percentage":
        mean = df[y].mean()
        median = df[y].median()
        ax.axhline(y = mean, linestyle = "--", color = CB_COLORS["blue"], label = f"arith mean ({mean:.3g})")
        ax.axhline(y = median, linestyle = "--", color = CB_COLORS["green"], label = f"median ({median:.3g})")

    # Fiting a power-law relationship
    log_x = np.log(df[x])
    log_y = np.log(df[y])
    b, a = np.polyfit(log_x, log_y, 1)  # Fit log(y) = b * log(x) + a
    a_exp = np.exp(a)

    # Plotting the best fit line
    x_vals = np.linspace(df[x].min(), df[x].max(), 100)
    y_vals = a_exp * x_vals**b
    ax.plot(x_vals, y_vals, "--", color = CB_COLORS["red"],
            label=f"best-fit: $y = {latex_float(a_exp)} \\cdot x^{{{b:.3g}}}$")

    # Adding a legend
    ax.legend(fontsize = "small")

    # Creating the plots directory if it doesn't exist and saving the plot as a PDF
    os.makedirs(PLOTS_DIR, exist_ok = True)
    fig.savefig(os.path.join(PLOTS_DIR, filename), format = "pdf")


def make_module_plots() -> None:
    """
    Make plots for the module statistics. Four plots are generated:
    - Parser time vs Total time
    - Percentage of time spent on parsing vs Total time
    - Parser time vs Size
    - Percentage of time spent on parsing vs Size

    If an extension is not in the `PLOT_STYLES` dictionary, it is grouped under
    the "other" category. The plots are saved as PDFs in the `plots` directory.

    Args:
        None

    Returns:
        None
    """

    # Read the module statistics file
    df = pd.read_csv(MODULE_STATS_FILE)

    # Convert the times from milliseconds to seconds
    df["total_time"] = df["total_time"] / 1000
    df["parser_time"] = df["parser_time"] / 1000

    # Group extensions not in PLOT_STYLES under "other".
    # NOTE: comment to show all extensions with the default style
    df["extension"] = df["extension"].apply(lambda x: x if x in PLOT_STYLES else "other")

    # Define the metrics to plot. Each metric contains the parameters to be used by the
    # generic plotting function `plot_metric_vs_metric`.
    metrics = [
        ("total_time", "parser_time", "Total time (s)", "Parser time (s)",
         "module_parser_vs_total.pdf", [10, 1, 0.1], "%"),
        ("total_time", "parser_percentage", "Total time (s)", "Percentage of time spent on parsing (%)",
         "module_parser_pct_vs_total.pdf", [], ""),
        ("size", "parser_time", "Size (bytes)", "Parser time (s)",
         "module_parser_vs_size.pdf", [1e-3, 1e-4, 1e-5], " seconds/byte"),
        ("size", "parser_percentage", "Size (bytes)", "Percentage of time spent on parsing (%)",
         "module_parser_pct_vs_size.pdf", [], ""),
    ]

    # Generate the plots for each metric, both with and without log scale
    for x, y, xlabel, ylabel, filename, guide_pcts, guide_label in metrics:
        plot_metric_vs_metric(df, x, y, xlabel, ylabel, f"{ylabel} vs {xlabel} by modules",
                              filename, guide_pcts, guide_label, module = True)
        plot_metric_vs_metric(df, x, y, xlabel, ylabel, f"{ylabel} vs {xlabel} by modules",
                              filename, guide_pcts, guide_label, module = True, log = True)


def make_package_plots() -> None:
    """
    Make plots for the package statistics. Four plots are generated:
    - Parser time vs Total time
    - Percentage of time spent on parsing vs Total time
    - Parser time vs Size
    - Percentage of time spent on parsing vs Size

    The plots are saved as PDFs in the `plots` directory.

    Args:
        None

    Returns:
        None
    """

    # Read the package statistics file
    df = pd.read_csv(PACKAGE_STATS_FILE)

    # Convert the times from milliseconds to seconds
    df["total_time"] = df["total_time"] / 1000
    df["parser_time"] = df["parser_time"] / 1000

    # Define the metrics to plot. Each metric contains the parameters to be used by the
    # generic plotting function `plot_metric_vs_metric`.
    metrics = [
        ("total_time", "parser_time", "Total time (s)", "Parser time (s)",
         "package_parser_vs_total.pdf", [5, 2, 1, 0.5, 0.2], "%"),
        ("total_time", "parser_percentage", "Total time (s)", "Percentage of time spent on parsing (%)",
         "package_parser_pct_vs_total.pdf", [], ""),
        ("size", "parser_time", "Size (bytes)", "Parser time (s)",
         "package_parser_vs_size.pdf", [1e-3, 1e-4, 1e-5], " seconds/byte"),
        ("size", "parser_percentage", "Size (bytes)", "Percentage of time spent on parsing (%)",
         "package_parser_pct_vs_size.pdf", [], ""),
    ]

    # Generate the plots for each metric, both with and without log scale
    for x, y, xlabel, ylabel, filename, guide_pcts, guide_label in metrics:
        plot_metric_vs_metric(df, x, y, xlabel, ylabel, f"{ylabel} vs {xlabel} by packages",
                              filename, guide_pcts, guide_label, module = False)
        plot_metric_vs_metric(df, x, y, xlabel, ylabel, f"{ylabel} vs {xlabel} by packages",
                              filename, guide_pcts, guide_label, module = False, log = True)


def make_aggregated_plot() -> None:
    """
    Makes an aggregated plot comparing the parser time against the total time
    across all packages. The plot is saved as a PDF in the `plots` directory.

    Args:
        None

    Returns:
        None
    """

    # Read the package statistics file
    df = pd.read_csv(PACKAGE_STATS_FILE)

    # Calculates the total time and parser time across all packages in seconds
    # and the percentage of time spent on parsing
    total_time = df["total_time"].sum() / 1000
    parser_time = df["parser_time"].sum() / 1000
    parser_percentage = (parser_time / total_time) * 100

    # Create a scatter plot comparing the parser time against the total time
    # across all packages with a similar style as the package plots. Annotate
    # the point with the total and parser time and the parser percentage.
    fig, ax = plt.subplots()
    ax.scatter(total_time, parser_time, **PACKAGE_STYLE)
    ax.grid(linestyle = "--", linewidth = 0.5)
    ax.set(xlabel = "Total time (s)", ylabel = "Parser time (s)",
           title = f"Parser time vs Total time across all packages ({parser_percentage:.3g}%)")
    ax.annotate(f"{parser_time:.3g}s / {total_time:.3g}s\n({parser_percentage:.3g}%)",
                (total_time, parser_time), 
                textcoords = "offset points", xytext = (0, 10), ha = "center")

    # Saves the plot as a PDF in the `plots` directory
    filename = "aggregated_parser_vs_total.pdf"
    fig.savefig(os.path.join(PLOTS_DIR, filename), format = "pdf")
