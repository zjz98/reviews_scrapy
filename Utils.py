from sentence_transformers import SentenceTransformer
import torch
from Config import Config
import json
import pandas as pd
import datetime
import os



class Utils:

    def get_embedding(self, sentences):
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        train_device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        embedding = model.encode(sentences, device=train_device, show_progress_bar=True)
        return embedding


    def get_languages(self):
        languages = []
        language_file = Config.data_dir + '/repo/' + Config.name + '_language.json'
        with open(language_file, encoding='utf-8') as a:
            jsonContent = json.load(a)
            languages = jsonContent.keys()
        languages = list(languages)
        for i in range(0, len(languages)):
            language = languages[i]
            languages[i] = str(language).lower()

        return languages


    def get_project_duration(self):
        meta_file = Config.data_dir + '/repo/' + Config.name + '_meta.json'
        days = 0
        with open(meta_file, encoding='utf-8') as a:
            jsonContent = json.load(a)
            begin = jsonContent['created_at']
            end = jsonContent['updated_at']
            begin = datetime.datetime.strptime(begin, "%Y-%m-%dT%H:%M:%SZ")
            end = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
            days = (end - begin).days
        return days

    def cal_duration(self, begin, end):
        begin = datetime.datetime.strptime(begin, "%Y-%m-%dT%H:%M:%SZ")
        end = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
        days = (end - begin).days
        return days



if __name__ == '__main__':
    print()

    # begin = '2023-05-12T21:59:49Z'
    # end = '2023-05-18T22:52:23Z'
    # begin = datetime.datetime.strptime(begin, "%Y-%m-%dT%H:%M:%SZ")
    # end = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
    # days = (end - begin).days
    # print(days)

    # data_commit = pd.read_excel(Config.data_dir + '/PR_commit_info.xlsx')
    # data_commit = pd.DataFrame(data_commit)
    #
    # dic = Config.data_dir + '/commit/commitDetail'  # 遍历所有commit
    # author_list = []
    # for dir in os.listdir(dic):
    #     file_list = os.listdir(dic + '/' + str(dir))
    #     for file in file_list:
    #         with open(dic + '/' + dir + '/' + file, encoding='utf-8') as a:
    #             jsonContent = json.load(a)
    #             author_list.append(jsonContent['commit']['author']['name'])
    #
    # data_commit['author'] = author_list
    # data_commit.to_excel(Config.data_dir + '/PR_commit_info.xlsx', index=False)



