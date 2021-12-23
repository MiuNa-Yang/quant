import pandas as pd
from datetime import datetime


def corr(x, y):
    x_s = pd.Series(x)
    y_s = pd.Series(y)

    return x_s.corr(y_s)


if __name__ == "__main__":

    stk_df = pd.read_csv("data/stk_16-21.csv")
    del stk_df['Unnamed: 0']

    # 策略 每个月第一个交易日 计算因子，然后选股并持仓1个月 然后换仓
    # 2017 - 1 ~ 2021 - 10
    stkcds = []
    # # 将大的数据根据股票代码进行切分
    for df in stk_df.groupby('Stkcd'):
        df = df[1]
        name = str(df['Stkcd'].tolist()[0])
        stkcds.append(name)
        while len(name) < 6:
            name = "0" + name
        print(name)
        df['alpha15'] = df['Hiprc'].rolling(3).corr(df['Hiprc'].rolling(3))
        df.to_csv("datas/{}_16-21.csv".format(name))

    # stk_df['Trddt'] = pd.to_datetime(stk_df['Trddt'])
    #
    # years = [y for y in range(2017, 2022)]
    # months = [m for m in range(1, 13)]
    #
    # start_money = 100000
    #
    # for y in years:
    #
    #     for m in months:
    #
    #         factors = {}
    #         inds = stk_df[stk_df['Trddt' <= datetime(y, m, 1)]].index
    #
    #         for id in inds:


