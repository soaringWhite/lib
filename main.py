from data_loader import DataLoader
from factor_calculator import FactorCalculator
from factor_analysis import FactorAnalysis

def main(database_path, query='SELECT * FROM data', adjust_price=False, factor_col=None, save_dir='results'):
    """
    主函数
    :param database_path: SQLite 数据库文件路径
    :param query: 自定义的 SQL 查询语句
    :param adjust_price: 是否进行复权处理
    :param factor_col: 指定分析的因子列名（如果为 None，则分析所有因子）
    :param save_dir: 结果保存目录
    """
    # 加载数据
    data_loader = DataLoader(database_path)
    try:
        data = data_loader.load_data(query)

        # 计算因子
        factor_calculator = FactorCalculator(data, adjust_price=adjust_price)
        factors_df = factor_calculator.calculate_factors()

        # 因子分析与可视化
        factor_analysis = FactorAnalysis(factors_df)

        # 分析单个因子或所有因子
        if factor_col is not None:
            factor_analysis.analyze_factor(factor_col, save_dir)
        else:
            factor_analysis.analyze_all_factors(save_dir)
    finally:
        # 关闭数据库连接
        data_loader.close()

if __name__ == "__main__":
    # 示例：传入 SQLite 数据库文件路径和自定义查询语句
    database_path = "E:\\data1\\L1_Day_data.sqlite3"
    custom_query = "SELECT * FROM day_data_zb"
    adjust_price = True  # 是否进行复权处理
    factor_col = None  # 指定分析的因子列名（如果为 None，则分析所有因子）
    save_dir = "E:\\show\\day"  # 结果保存目录

    # 调用主函数
    main(database_path, custom_query, adjust_price, factor_col, save_dir)
