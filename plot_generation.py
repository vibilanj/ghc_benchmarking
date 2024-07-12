import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from constants import (
    PLOTS_DIR, MODULE_STATS_FILE, PACKAGE_STATS_FILE,
    CB_COLORS, PLOT_STYLES, DEFAULT_PLOT_STYLE, PACKAGE_STYLE
)


def plot_metric_vs_metric(df, x, y, xlabel, ylabel, title, filename,
                          guide_pcts, guide_label, log = True, module = True):
    fig, ax = plt.subplots()

    if module:
        for ext, ext_df in df.groupby("extension"):
            style = PLOT_STYLES.get(ext, DEFAULT_PLOT_STYLE)
            ax.scatter(ext_df[x], ext_df[y], alpha = 0.5, label = ext, **style)
    else:
        ax.scatter(df[x], df[y], **PACKAGE_STYLE)

    if log is True:
        ax.set(xscale = "log", yscale = "log")

    ax.grid(linestyle = "--", linewidth = 0.5)
    ax.set(xlabel = xlabel, ylabel = ylabel, title = title)

    # Clamping axes to the data
    ax.set_xlim(ax.get_xlim())
    ax.set_ylim(ax.get_ylim())

    # Percentage guide lines
    x_vals = np.linspace(df[x].min(), df[x].max(), 100)
    for idx, pct in enumerate(guide_pcts):
        pct_vals = (pct / 100) * x_vals
        linestyle = "-." if idx % 2 == 0 else ":"
        ax.plot(x_vals, pct_vals, linestyle, color = CB_COLORS["black"], label = f"{pct}{guide_label}")
        # TODO: different colors or weights for different lines: used alternating line styles for now

    # Add horizontal lines for average and median for percentage plots
    if y == "parser_percentage":
        avg = df[y].mean()
        median = df[y].median()
        ax.axhline(y = avg, linestyle = "--", color = CB_COLORS["blue"], label = f"average ({avg:.3g})")
        ax.axhline(y = median, linestyle = "--", color = CB_COLORS["green"], label = f"median ({median:.3g})")

    # Fits a power-law relationship and plot it
    log_x = np.log(df[x])
    log_y = np.log(df[y])
    b, a = np.polyfit(log_x, log_y, 1)  # Fit log(y) = b * log(x) + a
    a_exp = np.exp(a)

    x_vals = np.linspace(df[x].min(), df[x].max(), 100)
    y_vals = a_exp * x_vals**b
    ax.plot(x_vals, y_vals, "--", color = CB_COLORS["red"],
            label=f"best-fit line $y = {a_exp:.3g}x^{{{b:.3g}}}$")

    # Adding legend
    ax.legend(fontsize = "small")

    # Saving the plot as a PDF
    if log is True:
        filename = filename.replace(".", "_log.")
    os.makedirs(PLOTS_DIR, exist_ok = True)
    fig.savefig(os.path.join(PLOTS_DIR, filename), format = "pdf")


def make_module_plots():
    df = pd.read_csv(MODULE_STATS_FILE)
    df["total_time"] = df["total_time"] / 1000
    df["parser_time"] = df["parser_time"] / 1000

    # NOTE: comment/uncomment to show all / hide other extensions
    df["extension"] = df["extension"].apply(lambda x: x if x in PLOT_STYLES else "other")

    metrics = [
        ("total_time", "parser_time", "Total time (s)", "Parser time (s)",
         "module_parser_vs_total.pdf", [0.1, 1, 10], "%"),
        ("total_time", "parser_percentage", "Total time (s)", "Percentage of time spent on parsing (%)",
         "module_parser_pct_vs_total.pdf", [], ""),
        ("size", "parser_time", "Size (bytes)", "Parser time (s)",
         "module_parser_vs_size.pdf", [1e-5, 1e-4, 1e-3], " seconds/byte"),
        ("size", "parser_percentage", "Size (bytes)", "Percentage of time spent on parsing (%)",
         "module_parser_pct_vs_size.pdf", [], ""),
    ]

    for x, y, xlabel, ylabel, filename, guide_pcts, guide_label in metrics:
        plot_metric_vs_metric(df, x, y, xlabel, ylabel, f"{ylabel} vs {xlabel} by modules",
                              filename, guide_pcts, guide_label)
        plot_metric_vs_metric(df, x, y, xlabel, ylabel, f"{ylabel} vs {xlabel} by modules",
                              filename, guide_pcts, guide_label, log = False)


def make_package_plots():
    df = pd.read_csv(PACKAGE_STATS_FILE)
    df["total_time"] = df["total_time"] / 1000
    df["parser_time"] = df["parser_time"] / 1000

    metrics = [
        ("total_time", "parser_time", "Total time (s)", "Parser time (s)",
         "package_parser_vs_total.pdf", [0.1, 1, 10], "%"),
        ("total_time", "parser_percentage", "Total time (s)", "Percentage of time spent on parsing (%)",
         "package_parser_pct_vs_total.pdf", [], ""),
        ("size", "parser_time", "Size (bytes)", "Parser time (s)",
         "package_parser_vs_size.pdf", [1e-5, 1e-4, 1e-3], " seconds/byte"),
        ("size", "parser_percentage", "Size (bytes)", "Percentage of time spent on parsing (%)",
         "package_parser_pct_vs_size.pdf", [], ""),
    ]

    for x, y, xlabel, ylabel, filename, guide_pcts, guide_label in metrics:
        plot_metric_vs_metric(df, x, y, xlabel, ylabel, f"{ylabel} vs {xlabel} by packages",
                              filename, guide_pcts, guide_label, module = False)
        plot_metric_vs_metric(df, x, y, xlabel, ylabel, f"{ylabel} vs {xlabel} by packages",
                              filename, guide_pcts, guide_label, log = False, module = False)


def make_aggregated_plot():
    df = pd.read_csv(PACKAGE_STATS_FILE)
    total_time = df["total_time"].sum() / 1000
    parser_time = df["parser_time"].sum() / 1000
    parser_percentage = (parser_time / total_time) * 100

    fig, ax = plt.subplots()
    ax.scatter(total_time, parser_time, **PACKAGE_STYLE)
    ax.grid(linestyle = "--", linewidth = 0.5)
    ax.set(xlabel = "Total time (s)", ylabel = "Parser time (s)",
           title = f"Parser time vs Total time across all packages ({parser_percentage:.3g}%)")
    ax.annotate(f"{parser_time:.3g}s / {total_time:.3g}s\n({parser_percentage:.3g}%)",
                (total_time, parser_time), 
                textcoords = "offset points", xytext = (0, 10), ha = "center")
    fig.savefig(os.path.join(PLOTS_DIR, "aggregated_parser_vs_total.pdf"), format = "pdf")


if __name__ == "__main__":
    pass