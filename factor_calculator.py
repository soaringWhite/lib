import pandas as pd
import numpy as np
import os
import importlib

def adjust_price_data(stock_data):
    """
    对价格数据进行复权处理（后复权）
    :param stock_data: 单个股票的数据
    :return: 复权后的股票数据
    """
    if 'adj_factor' not in stock_data.columns:
        raise KeyError("数据中缺少 'adj_factor' 列，无法进行复权处理。")

    # 向量化操作：对复权因子进行归一化（最新日期为 1）
    adj_factor = stock_data['adj_factor'] / stock_data['adj_factor'].iloc[-1]

    # 向量化操作：对价格列进行复权处理
    price_columns = ['open', 'high', 'low', 'close']
    for col in price_columns:
        if col in stock_data.columns:
            stock_data[col] = stock_data[col] * adj_factor

    return stock_data

def calculate_returns(stock_data, holding_days=1):
    """
    计算股票的收益（向量化操作）
    :param stock_data: 单个股票的数据
    :param holding_days: 持有天数
    :return: 收益数据
    """
    if 'close' not in stock_data.columns:
        raise KeyError("数据中缺少 'close' 列，无法计算收益。")

    # 向量化操作：计算未来价格
    future_close = stock_data['close'].shift(-holding_days)

    # 向量化操作：计算收益
    returns = (future_close - stock_data['close']) / stock_data['close']

    return returns

def calculate_factors(stock_data, factor_module_dir='factors'):
    """
    动态加载因子模块并计算因子（向量化操作）
    :param stock_data: 单个股票的数据
    :param factor_module_dir: 因子模块的目录
    :return: 包含因子数据的 DataFrame
    """
    factors = {}

    # 动态加载 factor_module_dir 目录下的所有因子模块
    for module_name in os.listdir(factor_module_dir):
        if module_name.endswith('.py') and module_name != '__init__.py':
            # 加载模块
            module = importlib.import_module(f'{factor_module_dir}.{module_name[:-3]}')
            # 调用模块中的 calculate_factor 函数
            factor_func = getattr(module, 'calculate_factor')
            # 计算因子
            factor_name = module_name[:-3]
            factors[factor_name] = factor_func(stock_data)

    return pd.DataFrame(factors)

class FactorCalculator:
    """
    因子计算器：用于批量计算股票因子
    """
    def __init__(self, data, holding_days=1, adjust_price=False):
        """
        初始化因子计算器
        :param data: 原始数据（包含多只股票的数据）
        :param holding_days: 持有天数
        :param adjust_price: 是否进行复权处理
        """
        self.data = data
        self.holding_days = holding_days
        self.adjust_price = adjust_price

    def calculate_factors(self):
        """
        批量计算所有股票的因子
        :return: 包含所有股票因子数据的 DataFrame
        """
        # 按股票分组
        grouped = self.data.groupby('code')

        # 使用列表存储所有股票的因子数据
        factors_all_stocks = []

        # 遍历每个股票，计算因子
        for code, stock_data in grouped:
            # 如果需要复权，则对价格数据进行复权处理
            if self.adjust_price:
                stock_data = adjust_price_data(stock_data)

            # 计算因子
            factors = self._calculate_factors_for_stock(stock_data)
            factors['code'] = code  # 添加股票 ID 列
            factors_all_stocks.append(factors)

        # 合并所有股票的因子数据
        return pd.concat(factors_all_stocks).reset_index(drop=True)

    def _calculate_factors_for_stock(self, stock_data):
        """
        计算单个股票的因子
        :param stock_data: 单个股票的数据
        :return: 单个股票的因子数据
        """
        # 计算收益
        returns_col = f'returns_{self.holding_days}d'
        stock_data[returns_col] = calculate_returns(stock_data, self.holding_days)

        # 动态加载因子模块并计算因子
        factors = calculate_factors(stock_data)

        # 合并收益列和因子列
        factors[returns_col] = stock_data[returns_col]

        # 确保 date 列被保留
        if 'date' in stock_data.columns:
            factors['date'] = stock_data['date']
        else:
            raise KeyError("数据中缺少 'date' 列，无法计算因子。")

        return factors

