import pandas as pd
from app_core.tokens_colors import CLIMATE


# def make_anomaly_to_rgb(clim_range: float = CLIMATE.anomaly_range_c):
#     neutral = CLIMATE.anomaly_neutral
#     cool = CLIMATE.anomaly_cold
#     warm = CLIMATE.anomaly_warm
#
#     def interp(c_from, c_to, t: float):
#         return tuple(int(c_from[i] + t * (c_to[i] - c_from[i])) for i in range(3))
#
#     def anomaly_to_rgb(anom: float):
#         if pd.isna(anom):
#             return neutral
#
#         a = max(-clim_range, min(clim_range, anom))
#
#         if abs(a) < 0.1:
#             return neutral
#         elif a < 0:
#             t = abs(a) / clim_range
#             return interp(neutral, cool, t)
#         else:
#             t = a / clim_range
#             return interp(neutral, warm, t)
#
#     return anomaly_to_rgb


def make_year_to_alpha(
    df_cet: pd.DataFrame, alpha_min: float = 0.8, alpha_max: float = 0.95
):
    min_year = int(df_cet["year"].min())
    max_year = int(df_cet["year"].max())

    def year_to_alpha(year: int) -> float:
        if max_year == min_year:
            return alpha_max
        t = (year - min_year) / (max_year - min_year)
        return alpha_min + t * (alpha_max - alpha_min)

    return year_to_alpha
