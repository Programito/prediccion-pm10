"""Exact descriptive statistics for explicitly selected numeric columns.

No Flask, pandas or sklearn dependency. Rows may be any iterable of mappings.
Numeric strings must use a decimal point; identifiers are never inferred.
"""

import math
import re
import statistics

NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", re.ASCII)


def linear_quantile(ordered_values, probability):
    if not 0 <= probability <= 1:
        raise ValueError("El cuantil debe estar entre cero y uno.")
    if not ordered_values:
        return None
    position = (len(ordered_values) - 1) * probability
    lower = math.floor(position)
    fraction = position - lower
    if fraction == 0:
        return ordered_values[lower]
    return (1 - fraction) * ordered_values[lower] + fraction * ordered_values[lower + 1]


def summarize_numeric_columns(rows, columns, *, missing_values=("", ".."), include_boxplot=False):
    """Consume rows once and calculate exact quartiles and sample deviation.

    Missing and invalid values have separate counts. Booleans and infinity are
    invalid numeric measurements; None, NaN and declared markers are missing.
    Exact quantiles retain the accepted values in memory. Inputs are not changed.
    """
    names = list(columns)
    if len(names) != len(set(names)):
        raise ValueError("Las columnas numéricas no pueden estar repetidas.")
    markers = set(missing_values)
    samples = {name: [] for name in names}
    missing = dict.fromkeys(names, 0)
    invalid = dict.fromkeys(names, 0)
    count = 0
    for row in rows:
        count += 1
        for name in names:
            original = row.get(name)
            if original is None or isinstance(original, str) and original.strip() in markers:
                missing[name] += 1
                continue
            if isinstance(original, bool):
                invalid[name] += 1
                continue
            if isinstance(original, str):
                if original.strip().casefold() in {"nan", "+nan", "-nan"}:
                    missing[name] += 1
                    continue
                if not NUMBER.fullmatch(original.strip()):
                    invalid[name] += 1
                    continue
            try:
                value = float(original)
            except (TypeError, ValueError, OverflowError):
                invalid[name] += 1
                continue
            if math.isnan(value):
                missing[name] += 1
            elif not math.isfinite(value):
                invalid[name] += 1
            else:
                samples[name].append(value)
    summaries = []
    for name in names:
        values = sorted(samples[name])
        errors = []

        def calculate(label, operation):
            try:
                value = operation()
                if math.isfinite(value):
                    return value
            except (OverflowError, ValueError):
                pass
            errors.append(label)
            return None

        summary = dict(
            name=name, valid_count=len(values), missing_count=missing[name], invalid_count=invalid[name],
            missing_pct=100 * missing[name] / count if count else None,
            minimum=values[0] if values else None, maximum=values[-1] if values else None,
            mean=calculate("mean", lambda: statistics.mean(values)) if values else None,
            p25=linear_quantile(values, .25), median=linear_quantile(values, .5), p75=linear_quantile(values, .75),
            std_dev=calculate("std_dev", lambda: statistics.stdev(values)) if len(values) > 1 else None,
            calculation_errors=errors,
        )
        if include_boxplot:
            summary["boxplot"] = tukey_boxplot(values)
        summaries.append(summary)
    return dict(row_count=count, columns=summaries, quantile_method="linear (n-1)*p", std_dev_ddof=1)


def tukey_boxplot(ordered_values):
    """Actual whisker observations inside inclusive Tukey fences; retain fliers."""
    if not ordered_values:
        return dict(lower_fence=None, upper_fence=None, whisker_low=None, whisker_high=None, outliers=[])
    q1, q3 = linear_quantile(ordered_values, .25), linear_quantile(ordered_values, .75)
    lower, upper = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    inside = [value for value in ordered_values if lower <= value <= upper]
    return dict(lower_fence=lower if math.isfinite(lower) else None,
                upper_fence=upper if math.isfinite(upper) else None,
                whisker_low=inside[0], whisker_high=inside[-1],
                outliers=[value for value in ordered_values if value < lower or value > upper])


def summarize_boxplot_groups(rows, column, *, group_by=None, label_by=None):
    """Reusable grouped box plots with the same numeric and null rules."""
    groups, labels = {}, {}
    for row in rows:
        value = row.get(group_by) if group_by else None
        key = (str(value) if value is not None and value != "" else "Sin grupo") if group_by else "all"
        groups.setdefault(key, []).append({column: row.get(column)})
        labels[key] = str(row.get(label_by) or key).strip() if label_by and group_by else key
    if not group_by and not groups:
        groups["all"] = []
    result = []
    for key in sorted(groups):
        statistics = summarize_numeric_columns(groups[key], [column], include_boxplot=True)
        result.append(dict(group=key, label=labels.get(key, "Selección completa") if group_by else "Selección completa",
                           row_count=statistics["row_count"], **statistics["columns"][0]))
    return result


def numeric_measurement_columns(columns):
    """Use the logical schema, excluding identifiers, keys and booleans."""
    return [field["name"] for field in columns
            if not field.get("isKey") and field["type"].casefold().startswith(("decimal", "entero", "proporción"))
            and not field["name"].casefold().startswith(("codigo_", "cod_"))]
