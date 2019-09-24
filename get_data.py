from cmb_licai import cmb_licai_webpage


if __name__ == "__main__":
    for pc in ["9294", "107107", "107109", "107115"]:
        licai = cmb_licai_webpage(product_type="T0001", product_code=pc)
        licai.set_page_count_to_get()
        licai.download_all_pages()

