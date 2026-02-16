from datetime import timedelta
import pandas as pd
from datetime import date
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

MIN_DATE = date(1000, 1, 1)
MAX_DATE = date(9999, 12, 31)


def filter_by_date_range(
    data: pd.DataFrame,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> pd.DataFrame:

    if data.empty:
        return data

    required_cols = {'year', 'month', 'day'}
    if not required_cols.issubset(data.columns):
        logger.warning(f"Missing date columns: {required_cols - set(data.columns)}")
        return data

    case_ranges = data.apply(
        lambda row: _compute_case_date_range(row['year'], row['month'], row['day']),
        axis=1,
        result_type='expand'
    )
    case_ranges.columns = ['case_min', 'case_max', 'is_unknown']

    filter_min = from_date if from_date is not None else MIN_DATE
    filter_max = to_date if to_date is not None else MAX_DATE

    mask = case_ranges.apply(
        lambda row: _ranges_overlap(
            case_min=row['case_min'],
            case_max=row['case_max'],
            is_unknown=row['is_unknown'],
            filter_min=filter_min,
            filter_max=filter_max,
        ),
        axis=1
    )

    filtered = data[mask]
    logger.info(f"Date filtering: {len(data)} → {len(filtered)} rows")
    return filtered


def _compute_case_date_range(
    year: pd.Int64Dtype,
    month: pd.Int64Dtype,
    day: pd.Int64Dtype,
) -> Tuple[Optional[date], Optional[date], bool]:
    try:
        if pd.isna(year):
            return (None, None, True)

        year = int(year)

        if pd.isna(month):
            return (date(year, 1, 1), date(year, 12, 31), False)

        month = int(month)
        if not 1 <= month <= 12:
            return (date(year, 1, 1), date(year, 12, 31), False)

        if pd.isna(day):
            first_day = date(year, month, 1)
            last_day = _last_day_of_month(year, month)
            return (first_day, last_day, False)

        day = int(day)
        complete_date = date(year, month, day)
        return (complete_date, complete_date, False)
    except (ValueError, OverflowError):
        return (None, None, True)


def _last_day_of_month(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    else:
        return date(year, month + 1, 1) - timedelta(days=1)


def _ranges_overlap(
    case_min: Optional[date],
    case_max: Optional[date],
    is_unknown: bool,
    filter_min: date,
    filter_max: date,
) -> bool:

    if is_unknown:
        return True

    if case_max < filter_min:
        return False

    if case_min > filter_max:
        return False

    return True