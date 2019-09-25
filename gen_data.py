from typing import Optional, Any

import matplotlib as mpl
import matplotlib.pyplot as plt
from cmb_licai import cmb_licai_data
from cmb_licai import cmb_licai_webpage

if __name__ == "__main__":
    # licai_product = [
    #     {"product_type": "TXXXX", "product_code": "103601", "annualized_title_suffix": "条净值年化", "annualized_on_column": "信托单位净值(元)", "date_column": 5},
    #     {"product_type": "TXXXX", "product_code": "103602", "annualized_title_suffix": "条净值年化", "annualized_on_column": "信托单位净值(元)", "date_column": 5},
    #     {"product_type": "TXXXX", "product_code": "103603", "annualized_title_suffix": "条净值年化", "annualized_on_column": "信托单位净值(元)", "date_column": 5}
    # ]
    # figure_filename = "comparison_卓越.png"

    licai_product = [
        {"product_type": "T0001", "product_code": "9294", "annualized_title_suffix": "条净值年化", "annualized_on_column": "产品净值", "date_column": 3},
        {"product_type": "T0001", "product_code": "107107", "annualized_title_suffix": "条净值年化", "annualized_on_column": "产品净值", "date_column": 3},
        {"product_type": "T0001", "product_code": "107109", "annualized_title_suffix": "条净值年化", "annualized_on_column": "产品净值", "date_column": 3},
        {"product_type": "T0001", "product_code": "107115", "annualized_title_suffix": "条净值年化", "annualized_on_column": "产品净值", "date_column": 3},
    ]
    figure_filename = "comparison_周周发.png"


    # download
    for index, pr in enumerate(licai_product):
        licai = cmb_licai_webpage(**pr)
        licai.set_page_count_to_get()
        licai.download_all_pages()

    # convert to excel
    for index, pr in enumerate(licai_product):
        licai = cmb_licai_data(**pr)
        licai.get_offline_page_count()
        licai.generate_df()
        licai.save_as_excel()

    # load from excel
    all_licai_list = []
    for index, pr in enumerate(licai_product):
        licai = cmb_licai_data(**pr)
        licai.load_from_excel()
        all_licai_list.append(licai)
    # for licai in all_licai_list:
    #     for n in cmb_licai_data.df_name_list:
    #         print(licai.all_df_list[n])

    # plot
    font_family = mpl.rcParams['font.family']
    font_name: list = mpl.rcParams['font.%s' % font_family[0]]
    font_name.insert(0, "Microsoft Yahei")
    mpl.rcParams['font.%s' % font_family[0]] = font_name
    num_plot = len(cmb_licai_data.df_name_list) - 1
    fig, axes_list = plt.subplots(num_plot, 1, sharex=False, figsize=(1280/100, 500/100*num_plot))
    for index, name in enumerate(cmb_licai_data.df_name_list[1:]):
        axes = axes_list[index]
        for licai in all_licai_list:
            df = licai.all_df_list[name]
            axes.plot(df.index, df["{}{}".format(name, licai.annualized_title_suffix)], label=df.iat[0, licai.name_column])
        axes.legend()
        axes.minorticks_on()
        axes.grid(True, which="major", axis="both")
        axes.grid(True, which="minor", axis="y", linestyle=":")
        axes.set_title("{}{}".format(name, licai.annualized_title_suffix))
    #plt.show()
    plt.suptitle("净值年化对比图", fontsize=20, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(figure_filename)