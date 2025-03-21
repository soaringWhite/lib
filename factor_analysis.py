import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import seaborn as sns
import os
# 设置 Matplotlib 的字体为 SimHei（黑体），支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
from typing import Optional, Dict, Any



class FactorAnalysis:
    def __init__(self, factors_df: pd.DataFrame):
        """
        初始化因子分析类
        :param factors_df: 包含因子和收益的 DataFrame
        """
        self.factors_df = factors_df

    def daily_grouping(self, factor_col: str, q: int = 5) -> pd.DataFrame:
        """
        每天按因子值分组
        :param factor_col: 因子列名
        :param q: 分位数（组数）
        :return: 分组后的 DataFrame
        """
        def safe_qcut(x):
            # 如果因子值唯一或数量不足，则均分为 q 组
            if x.nunique() < q:
                # 生成唯一的边界值
                unique_values = np.sort(x.unique())
                if len(unique_values) == 1:  # 如果所有值都相同
                    return pd.Series(1, index=x.index)  # 所有值分到同一组
                bins = np.linspace(unique_values.min(), unique_values.max(), q + 1)
                bins = np.unique(bins)  # 确保边界值唯一
                if len(bins) - 1 < q:  # 如果生成的区间少于 q 个
                    return pd.Series(1, index=x.index)  # 所有值分到同一组
                return pd.cut(x, bins=bins, labels=range(1, len(bins)), duplicates='drop')
            return pd.qcut(x, q=q, labels=range(1, q + 1), duplicates='drop')

        self.factors_df['group'] = self.factors_df.groupby('date')[factor_col].transform(safe_qcut)
        return self.factors_df

    def calculate_daily_group_returns(self, factor_col: str, holding_days: int = 5) -> pd.DataFrame:
        """
        计算每天每组的平均收益
        :param factor_col: 因子列名
        :param holding_days: 持有天数（用于选择收益列）
        :return: 每天的每组平均收益
        """
        # 动态生成收益列名
        returns_col = f'returns_{holding_days}d'

        # 如果数据中不存在指定收益列，则动态生成（假设 close 列存在）
        if returns_col not in self.factors_df.columns:
            if 'close' in self.factors_df.columns:
                self.factors_df[returns_col] = self.factors_df.groupby('code')['close'].pct_change(periods=holding_days) * 100
            else:
                raise ValueError(f"未找到收益列 '{returns_col}'，且无法动态生成，请确保数据中存在 'close' 列。")

        # 每天按因子值分组
        self.daily_grouping(factor_col)

        # 计算每天每组的平均收益
        daily_group_returns = self.factors_df.groupby(['date', 'group'], observed=False)[returns_col].mean().reset_index()
        return daily_group_returns

    def calculate_cumulative_returns(self, daily_group_returns: pd.DataFrame, holding_days: int = 5) -> pd.DataFrame:
        """
        计算每组的累计收益（净值）
        :param daily_group_returns: 每天的每组平均收益
        :param holding_days: 持有天数（用于选择收益列）
        :return: 每组的累计收益
        """
        # 动态生成收益列名
        returns_col = f'returns_{holding_days}d'

        # 计算累计收益
        daily_group_returns['cumulative_returns'] = daily_group_returns.groupby('group')[returns_col].cumprod()

        # 净值从 1 开始
        daily_group_returns['cumulative_returns'] = daily_group_returns.groupby('group')['cumulative_returns'].transform(
            lambda x: x / x.iloc[0] if x.iloc[0] != 0 else x
        )
        return daily_group_returns

    def plot_cumulative_returns(self, cumulative_returns: pd.DataFrame, save_path: Optional[str] = None) -> None:
        """
        绘制净值曲线
        :param cumulative_returns: 每组的累计收益
        :param save_path: 图像保存路径（如果为 None，则不保存）
        """
        plt.figure(figsize=(12, 6))
        for group, data in cumulative_returns.groupby('group'):
            plt.plot(data['date'], data['cumulative_returns'], label=f'Group {group}')
        plt.title('Net Value Curve by Group')
        plt.xlabel('Date')
        plt.ylabel('Net Value')
        plt.legend()

        if save_path:
            plt.savefig(save_path)
        else:
            plt.close()  # 不显示图像，直接关闭

    def analyze_daily_group(self, factor_col: str, holding_days: int = 5, q: int = 5, save_dir: Optional[str] = None) -> None:
        """
        每天按因子值分组，计算每组平均收益并生成净值曲线
        :param factor_col: 因子列名
        :param holding_days: 持有天数（用于选择收益列）
        :param q: 分位数（组数）
        :param save_dir: 结果保存目录（如果为 None，则不保存）
        """
        # 计算每天每组的平均收益
        daily_group_returns = self.calculate_daily_group_returns(factor_col, holding_days)

        # 计算每组的累计收益
        cumulative_returns = self.calculate_cumulative_returns(daily_group_returns, holding_days)

        # 绘制净值曲线
        if save_dir:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            save_path = os.path.join(save_dir, f'{factor_col}_net_value_curve_{holding_days}d.png')
            self.plot_cumulative_returns(cumulative_returns, save_path=save_path)
        else:
            self.plot_cumulative_returns(cumulative_returns)

    def analyze_all_factors(self, holding_days: int = 5, save_dir: str = 'results') -> None:
        """
        分析所有因子并保存结果
        :param holding_days: 持有天数（用于选择收益列）
        :param save_dir: 结果保存目录
        """
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 获取所有因子列（排除非因子列）
        factor_cols = [col for col in self.factors_df.columns if col not in ['date', 'code', 'returns_5d', 'returns_1d']]

        # 遍历所有因子并分析
        for factor_col in factor_cols:
            self.analyze_daily_group(factor_col, holding_days=holding_days, save_dir=save_dir)



