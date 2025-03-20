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

class FactorAnalysis:
    def __init__(self, factors_df, holding_days=1):
        """
        初始化因子分析器
        :param factors_df: 包含因子和收益的数据
        :param holding_days: 持有天数
        """
        self.factors_df = factors_df
        self.holding_days = holding_days

    def select_factor(self, factor_col=None):
        """
        选择分析的因子
        :param factor_col: 因子列名，如果为 None 则分析所有因子
        :return: 需要分析的因子列表
        """
        # 找到所有因子列（排除收益列和标识列）
        factor_cols = [col for col in self.factors_df.columns
                       if not col.startswith('returns_')
                       and col not in ['code', 'date', 'group']]

        if factor_col is not None:
            if factor_col not in factor_cols:
                raise KeyError(f"数据中缺少 '{factor_col}' 列，请检查因子名称。")
            return [factor_col]
        return factor_cols

    def calculate_group_returns(self, factor_col):
        """
        计算指定因子的分组收益
        :param factor_col: 因子列名
        :return: 包含分组收益的 DataFrame
        """
        # 按因子值分组
        self.factors_df['group'] = pd.qcut(self.factors_df[factor_col], q=5, labels=range(1, 6))

        # 计算每组的平均收益
        group_returns = self.factors_df.groupby('group', observed=False)[f'returns_{self.holding_days}d'].mean()
        return group_returns

    def plot_group_returns(self, factor_col, save_path=None):
        """
        绘制指定因子的每组平均收益柱状图
        :param factor_col: 因子列名
        :param save_path: 图像保存路径（如果为 None，则不保存）
        """
        group_returns = self.calculate_group_returns(factor_col)

        # 绘制柱状图
        plt.figure(figsize=(10, 6))
        sns.barplot(x=group_returns.index, y=group_returns.values)
        plt.title(f"因子 {factor_col} 的每组平均收益")
        plt.xlabel("组别")
        plt.ylabel("平均收益")
        if save_path is not None:
            plt.savefig(save_path)  # 保存图像
        plt.close()  # 关闭图像，避免内存泄漏

    def plot_returns_over_time(self, factor_col, save_path=None):
        """
        绘制指定因子的每组收益随时间的变化图
        :param factor_col: 因子列名
        :param save_path: 图像保存路径（如果为 None，则不保存）
        """
        # 找到收益列的名称（列名以 'returns_' 开头）
        returns_col = None
        for col in self.factors_df.columns:
            if col.startswith('returns_'):
                returns_col = col
                break

        if returns_col is None:
            raise KeyError("找不到收益列，请检查因子计算逻辑。")

        # 检查 date 列是否存在
        if 'date' not in self.factors_df.columns:
            raise KeyError("数据中缺少 'date' 列，无法绘制收益随时间的变化。")

        # 按因子值分组
        self.factors_df['group'] = pd.qcut(self.factors_df[factor_col], q=5, labels=range(1, 6))

        # 绘制收益随时间的变化
        plt.figure(figsize=(12, 6))
        for group in sorted(self.factors_df['group'].unique()):
            group_data = self.factors_df[self.factors_df['group'] == group]
            group_data.groupby('date')[returns_col].mean().plot(label=f"组 {group}")
        plt.title(f"因子 {factor_col} 的每组收益随时间的变化")
        plt.xlabel("日期")
        plt.ylabel("收益")
        plt.legend()
        if save_path is not None:
            plt.savefig(save_path)  # 保存图像
        plt.close()  # 关闭图像，避免内存泄漏

    def analyze_factor(self, factor_col, save_dir=None):
        """
        分析单个因子
        :param factor_col: 因子列名
        :param save_dir: 结果保存目录（如果为 None，则不保存）
        """
        if save_dir is not None:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

        # 保存分组收益数据
        group_returns = self.calculate_group_returns(factor_col)
        if save_dir is not None:
            group_returns.to_csv(os.path.join(save_dir, f'{factor_col}_group_returns.csv'))

        # 绘制并保存图像
        self.plot_group_returns(factor_col, save_path=os.path.join(save_dir, f'{factor_col}_group_returns.png') if save_dir else None)
        self.plot_returns_over_time(factor_col, save_path=os.path.join(save_dir, f'{factor_col}_returns_over_time.png') if save_dir else None)

    def analyze_all_factors(self, save_dir=None):
        """
        分析所有因子
        :param save_dir: 结果保存目录（如果为 None，则不保存）
        """
        # 找到所有因子列
        factor_cols = self.select_factor()

        for factor_col in factor_cols:
            self.analyze_factor(factor_col, save_dir)
