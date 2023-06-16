

import pandas as pd
from Config import Config

import os
from Scrapy import Scrapy
from FeatureProcess import FeatureProcess


if __name__ == '__main__':

    scrapy = Scrapy()
    feature_process = FeatureProcess()

    # #下载项目元数据
    # scrapy.get_meta_data()
    # scrapy.get_language_list()

    # 下载项目pr数据
    # scrapy.get_all_PR()
    # scrapy.get_PR_detail()
    # scrapy.save_PR_info()

    # 下载每个pr的commit数据
    # scrapy.get_PR_commits_list()
    # scrapy.get_PR_commits_detail()
    # scrapy.save_PR_commit_info()

    # 下载每个pr的comment数据
    # scrapy.get_PR_comments_list()
    # scrapy.save_PR_comment_info()

    # # 查看用户间的follow关系
    scrapy.get_follow_relation()
    scrapy.save_follow_relation()

    # 特征提取
    # feature_process.process_PR_feature()
    # feature_process.process_project_feature()
    # feature_process.process_author_feature()
    # feature_process.process_reviewer_feature()














