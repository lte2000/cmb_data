from typing import Dict

from bs4 import BeautifulSoup
import pandas as pd
import os
import re
import matplotlib.pyplot as plt
import matplotlib as mpl
import requests
import glob

class cmb_licai(object):
    def __init__(self, product_type, product_code, **kwargs):
        self.product_type = product_type
        self.product_code = product_code
        self.offline_dir = "{}_{}".format(self.product_type, self.product_code)
        self.page_count = 1

    def get_page_count(self, soup):
        pageText_list = soup.find_all("span", class_="pageText")
        if len(pageText_list) != 3:
            raise Exception('Unexpected count of <span class="pageText">: {}'.format(len(pageText_list)))
        match = re.match("\d+\s*/\s*(\d+)", pageText_list[2].text)
        if match:
            total_page = match.group(1)
        else:
            raise Exception('Unexpected content of <span class="pageText">: {}'.format(pageText_list[2].text))
        return int(total_page)

    def get_record_count(self, soup):
        pageText_list = soup.find_all("span", class_="pageText")
        if len(pageText_list) != 3:
            raise Exception('Unexpected count of <span class="pageText">: {}'.format(len(pageText_list)))
        match = re.match("\s*(\d+)\s*", pageText_list[0].text)
        if match:
            total_record = match.group(1)
        else:
            raise Exception('Unexpected content of <span class="pageText">: {}'.format(pageText_list[2].text))
        return int(total_record)

    def get_offline_page_path(self, page):
        return os.path.join(self.offline_dir, "page_{:03d}.html".format(page))

    def get_excel_path(self):
        return "{}_{}.xlsx".format(self.product_type, self.product_code)

class cmb_licai_webpage(cmb_licai):
    headers = {'Accept':'*/*','Accept-Encoding':'gzip, deflate','Accept-Language':'zh-CN,zh;q=0.9','Connection':'keep-alive','User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36'}
    url_template = "http://www.cmbchina.com/cfweb/personal/prodvalue.aspx?PrdType={PrdType}&PrdCode={PrdCode}&PageNo={PageNo}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_page_count_to_get(self, max=300):
        url = self.url_template.format(PrdType=self.product_type, PrdCode=self.product_code, PageNo=1)
        res = requests.get(url, headers=self.headers).text
        soup = BeautifulSoup(res, "html.parser")
        total_page = self.get_page_count(soup)
        self.page_count = max if total_page > max else total_page

    def download_all_pages(self):
        try:
            os.mkdir(self.offline_dir)
        except FileExistsError:
            pass

        for f in glob.glob(os.path.join(self.offline_dir, "*.html")):
            os.remove(f)

        for p in range(1, self.page_count + 1):
            url = self.url_template.format(PrdType=self.product_type, PrdCode=self.product_code, PageNo=p)
            res = requests.get(url, headers=self.headers).text
            with open(self.get_offline_page_path(p), "w", encoding="utf-8") as f:
                f.write(res)

class cmb_licai_data(cmb_licai):
    all_df_list: Dict[str, pd.DataFrame]
    df_name_list = ["base", "2", "7", "20", "60", "180", "360"]

    def __init__(self, annualized_title_suffix="日年化", annualized_on_column="产品净值", date_column=3, name_column=1, **kwargs):
        super().__init__(**kwargs)
        self.annualized_title_suffix = annualized_title_suffix
        self.annualized_on_column = annualized_on_column
        self.date_column = date_column
        self.name_column = name_column
        self.all_df_list = {}
        for n in self.df_name_list:
            self.all_df_list[n] = None

    def get_offline_page_count(self):
        fn = self.get_offline_page_path(1)
        with open(fn, encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        total_page = self.get_page_count(soup)
        self.page_count = total_page

    @staticmethod
    def annualized_pct_change(series):
        dt_days = (series.index[0] - series.index[-1]).days
        return (series.iat[0] / series.iat[-1] - 1) / dt_days * 365 * 100

    @staticmethod
    def first(series):
        return series.iat[0]

    def generate_df(self):
        base_df: pd.DataFrame = None
        for p in range(1, self.page_count + 1):
            fn = self.get_offline_page_path(p)
            with open(fn, encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
            table_list = soup.find_all("table", class_="ProductTable")
            if len(table_list) == 1:
                table_value = table_list[0]
            elif len(table_list) > 1:
                table_likely = []
                for table in table_list:
                    if "id" not in table.attrs or table["id"] != "table_invest":
                        table_likely.append(table)
                if len(table_likely) != 1:
                    raise Exception("Wrong count of ProductTable (> 1)")
                table_value = table_likely[0]
            else:
                raise Exception("Wrong count of ProductTable (= 0)")

            dfs = pd.read_html(str(table_value), header=0, index_col=self.date_column)
            if base_df is None:
                base_df = dfs[0]
            else:
                new_index = [x for x in dfs[0].index if x not in base_df.index]
                base_df = base_df.append(dfs[0].reindex(index=new_index))
        try:
            base_df.index = pd.to_datetime(base_df.index, format='%Y%m%d')
        except:
            base_df.index = pd.to_datetime(base_df.index, format='%Y-%m-%d')
        base_df = base_df.sort_index()
        self.all_df_list["base"] = base_df
        for n in self.df_name_list[1:]:
            new_df = base_df.copy()
            new_df["{}{}".format(n, self.annualized_title_suffix)] = new_df[self.annualized_on_column].rolling(int(n)).agg(self.annualized_pct_change)
            self.all_df_list[n] = new_df

    def save_as_excel(self):
        excel_fn = self.get_excel_path()
        writer = pd.ExcelWriter(excel_fn,
                                engine='xlsxwriter',
                                datetime_format='yyyy-mm-dd')
        for n in self.df_name_list:
            self.all_df_list[n].sort_index(ascending=False).to_excel(writer, sheet_name=n)
        writer.save()

    def load_from_excel(self):
        self.all_df_list = {}
        excel_fn = self.get_excel_path()
        with pd.ExcelFile(excel_fn) as xls:
            for n in self.df_name_list:
                self.all_df_list[n] = pd.read_excel(xls, n, index_col=0)
