import sqlite3
import pandas as pd

class DataLoader:
    def __init__(self, database_path):
        """
        初始化 SQLite 数据库连接
        :param database_path: SQLite 数据库文件路径
        """
        self.con = sqlite3.connect(database_path)

    def load_data(self, query='SELECT * FROM data'):
        """
        从数据库加载数据
        :param query: SQL 查询语句
        :return: 加载的数据（DataFrame）
        """
        return pd.read_sql_query(query, con=self.con)

    def close(self):
        """
        关闭数据库连接
        """
        self.con.close()
