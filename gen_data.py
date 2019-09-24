from typing import Optional, Any

import matplotlib as mpl
import matplotlib.pyplot as plt
from cmb_licai import cmb_licai_data


if __name__ == "__main__":
    all_licai_list = {}
    for pc in ["9294", "107107", "107109", "107115"]:
        licai = cmb_licai_data(product_type="T0001", product_code=pc)
        licai.get_offline_page_count()
        licai.generate_df()
        licai.save_as_excel()
        all_licai_list[pc] = licai

    font_family = mpl.rcParams['font.family']
    font_name: list = mpl.rcParams['font.%s' % font_family[0]]
    font_name.insert(0, "Microsoft Yahei")
    mpl.rcParams['font.%s' % font_family[0]] = font_name
    for n in cmb_licai_data.df_name_list[1:]:
        plt.figure()
        for pc in ["9294", "107107", "107109", "107115"]:
            df = all_licai_list[pc].all_df_list[n]
            plt.plot(df.index, df["{}日年化".format(n)], label=df["产品名称"].iat[0])
        plt.legend()
        plt.suptitle("{}日年化".format(n))
    plt.show()