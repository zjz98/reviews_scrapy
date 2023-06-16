import json
import requests
import time
import os
import pymongo
import aiohttp
import asyncio
import os, openpyxl
import itertools
import pathlib
import random
import re
import pandas as pd
import openpyxl
import xlsxwriter
from Config import Config
import shutil


class Scrapy:

    #userAgent循环迭代器
    user_iter = itertools.cycle(Config.user_list)
    #token循环迭代器
    token_iter = itertools.cycle(Config.token_list)

    def get_meta_data(self):


        if not os.path.exists(Config.data_dir):
            os.mkdir(Config.data_dir)
        list_dir = Config.data_dir + '/repo'
        if not os.path.exists(list_dir):
            os.mkdir(list_dir)

        url = Config.repoMetaApi
        requests.adapters.DEFAULT_RETRIES = 50
        s = requests.session()
        s.keep_alive = False
        headers = {'User-Agent': next(self.user_iter), 'Authorization': 'token ' + next(self.token_iter)}
        r = s.get(url=url, headers=headers)
        file_name = list_dir + '/' + Config.name + '_meta.json'
        f = open(file_name, 'wb')
        f.write(r.content)
        f.close()
        print('已爬取项目元信息')


    def get_language_list(self):

        if not os.path.exists(Config.data_dir):
            os.mkdir(Config.data_dir)
        list_dir = Config.data_dir + '/repo'
        if not os.path.exists(list_dir):
            os.mkdir(list_dir)

        url = Config.repoLanguageApi
        requests.adapters.DEFAULT_RETRIES = 50
        s = requests.session()
        s.keep_alive = False
        headers = {'User-Agent': next(self.user_iter), 'Authorization': 'token ' + next(self.token_iter)}
        r = s.get(url=url, headers=headers)
        file_name = list_dir + '/' + Config.name + '_language.json'
        f = open(file_name, 'wb')
        f.write(r.content)
        f.close()
        print('已爬取项目语言信息')


    def get_all_PR(self):
        page = 1
        page_size = 100  # max:100
        base_url = Config.repoPRListApi

        list_dir = Config.data_dir + '/pr'
        if not os.path.exists(list_dir):
            os.mkdir(list_dir)

        list_dir = Config.data_dir + '/pr/prList'
        if not os.path.exists(list_dir):
            os.mkdir(list_dir)

        while (True):
            json_size = self.get_onePage_PR(base_url, page, page_size, list_dir)
            if int(json_size) < 100:
                print("PR列表成功写到page " + str(page))
                break
            else:
                print("成功写到page " + str(page))
                page += 1
                if Config.test and page == 5:
                    break

        print('完成PR列表的获取')


    def get_onePage_PR(self, base_url, start_number, page_size, list_dir_name) -> int:
        try:
            requests.adapters.DEFAULT_RETRIES = 50
            s = requests.session()
            s.keep_alive = False

            headers = {'User-Agent': next(self.user_iter), 'Authorization': 'token ' + next(self.token_iter)}
            r = s.get(url=base_url + '?state=all&' + 'page=' + str(start_number) + '&per_page=' + str(page_size), headers=headers)
            if r.status_code != 200:
                raise Exception
            json_data = json.loads(r.content, encoding='utf-8')
            json_size = len(json_data)
            file_name = list_dir_name + '/' + str(time.time())[:10] + '.json'
            f = open(file_name, 'wb');
            f.write(r.content)
            f.close()
            return json_size
        except Exception as e:
            print("重试")
            return self.get_onePage_PR(base_url, start_number, page_size, list_dir_name)


    def get_PR_detail(self):
        prNumberList = []
        dic = Config.data_dir + '/pr/prList'
        file_list = os.listdir(dic)
        for file in file_list:
            with open(dic + '/' + file, encoding='utf-8') as a:
                jsonContent = json.load(a)
                for item in jsonContent:
                    prNumberList.append(item['number'])

        detail_dir = Config.data_dir + '/pr/prDetail'
        if not os.path.exists(detail_dir):
            os.mkdir(detail_dir)
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()
        tasks = []
        for item in prNumberList:
            targetUrl = Config.repoPRDetailApi + str(item)
            task = asyncio.ensure_future(self.download(targetUrl, detail_dir, str(item)))
            tasks.append(task)
        loop.run_until_complete(asyncio.wait(tasks))
        print('完成所有PR详细数据获取')

    # 下载数据，是一个协程任务
    async def download(self, url, dir_name, number):
        async with aiohttp.ClientSession() as session:
            file_name = dir_name + '/' + number + '.json'
            await self.fetchData(url, number, file_name, session)
            print(number + " 的数据获取完成")


    async def fetchData(self, url, number, file_name, session):
        try:
            headers = {'User-Agent': next(self.user_iter), 'Authorization': 'token ' + next(self.token_iter)}
            async with session.get(url, ssl=False, headers=headers
                                   ) as response:
                if response.status != 200:
                    raise Exception
                f = open(file_name, 'wb');
                s = await response.text();
                bytes = s.encode('utf-8')
                f.write(bytes)
                f.close()
        except Exception as e:
            await self.fetchData(url, number, file_name, session)


    def save_PR_info(self):
        data = pd.DataFrame(
            columns=['number', 'state', 'title', 'author', 'body', 'created_at', 'updated_at', 'merged_at',
                     'merged', 'comments', 'review_comments', 'commits', 'additions', 'deletions', 'changed_files'])
        dic = Config.data_dir + '/pr/prDetail'
        file_list = os.listdir(dic)
        for file in file_list:
            with open(dic + '/' + file, encoding='utf-8') as a:
                jsonContent = json.load(a)
                number = jsonContent['number']
                state = jsonContent['state']
                title = jsonContent['title']
                author = jsonContent['user']['login']
                body = jsonContent['body']
                created_at = jsonContent['created_at']
                updated_at = jsonContent['updated_at']
                merged_at = jsonContent['merged_at']
                merged = jsonContent['merged']
                comments = jsonContent['comments']
                review_comments = jsonContent['review_comments']
                commits = jsonContent['commits']
                additions = jsonContent['additions']
                deletions = jsonContent['deletions']
                changed_files = jsonContent['changed_files']
                data.loc[len(data)] = [number, state, title, author, body, created_at, updated_at, merged_at,
                     merged, comments, review_comments, commits, additions, deletions, changed_files]
        #data['created_at'].fillna(value='2020-04-24T12:34:27Z', inplace=True)
        data.to_excel(Config.data_dir + '/PR_info.xlsx', index=False)
        print('PR内容提取完成')


    def get_PR_commits_list(self):
        data = pd.read_excel(Config.data_dir + '/PR_info.xlsx')
        data = pd.DataFrame(data)
        numberList = data['number'].tolist()

        list_dir = Config.data_dir + '/commit'
        if not os.path.exists(list_dir):
            os.mkdir(list_dir)
        list_dir = Config.data_dir + '/commit/commitList'
        if not os.path.exists(list_dir):
            os.mkdir(list_dir)

        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()
        tasks = []
        for item in numberList:
            targetUrl = 'https://api.github.com/repos/' + Config.repoName + '/pulls/' + str(item) + '/commits'
            task = asyncio.ensure_future(self.download(targetUrl, list_dir, str(item)))
            tasks.append(task)
        loop.run_until_complete(asyncio.wait(tasks))
        print('done')


    def get_PR_commits_detail(self):
        data = pd.read_excel(Config.data_dir + '/PR_info.xlsx')
        data = pd.DataFrame(data)
        numberList = data['number'].tolist()

        detail_dir = Config.data_dir + '/commit/commitDetail'
        if not os.path.exists(detail_dir):
            os.mkdir(detail_dir)
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()

        tasks = []
        for item in numberList:
            dic = Config.data_dir + '/commit/commitList/' + str(item) + '.json'
            cur_download_dir = detail_dir + '/' + str(item)
            if not os.path.exists(cur_download_dir):
                os.mkdir(cur_download_dir)
            with open(dic, encoding='utf-8') as a:
                jsonContent = json.load(a)
                for item in jsonContent:
                    cur_sha = item['sha']
                    targetUrl = Config.repoCommitDetailApi + str(cur_sha)
                    task = asyncio.ensure_future(self.download(targetUrl, cur_download_dir, str(cur_sha)))
                    tasks.append(task)
        loop.run_until_complete(asyncio.wait(tasks))
        print('完成每个PR的所有commit数据获取')


    def save_PR_commit_info(self):
        data = pd.DataFrame(
            columns=['sha', 'belong_to_PR', 'author','changes', 'additions', 'deletions', 'segs', 'add_segs', 'del_segs',
                     'file_name_list', 'has_test', 'file_added', 'file_updated',
                     'file_deleted', 'test_churn', 'non_test_churn', 'directory_num', 'file_changes_list'])

        down_url_list = []
        dic = Config.data_dir + '/commit/commitDetail'  #遍历所有commit
        for dir in os.listdir(dic):
            file_list = os.listdir(dic + '/' + str(dir))
            for file in file_list:
                with open(dic + '/' + dir + '/' + file, encoding='utf-8') as a:
                    jsonContent = json.load(a)
                    sha = jsonContent['sha']
                    belong_to_PR = str(dir)
                    author = jsonContent['commit']['author']['name']
                    if jsonContent['author'] != None:
                        author = jsonContent['author']['login']
                    changes = jsonContent['stats']['total']
                    additions = jsonContent['stats']['additions']
                    deletions = jsonContent['stats']['deletions']
                    files = jsonContent['files']
                    segs = 0
                    add_segs = 0
                    del_segs = 0
                    file_added = 0
                    file_updated = 0
                    file_deleted = 0
                    has_test = 0
                    test_churn = 0
                    non_test_churn = 0
                    file_name_list = ''
                    directory_num = 0
                    file_changes_list = ''
                    for file in files:
                        if file['status'] == 'modified':
                            file_updated += 1
                        if file['status'] == 'added':
                            file_added += 1
                        if file['status'] == 'deleted':
                            file_deleted += 1
                        if 'test' in str(file['filename']):
                            has_test = 1
                            test_churn += file['changes']
                        else:
                            non_test_churn += file['changes']
                        file_name_list += ';' + file['filename']
                        if file['raw_url'] != None:
                            down_url_list.append(file['raw_url'])
                        name_split = str(file['filename']).split('/')
                        directory_num += len(name_split)
                        file_changes_list += ';' + str(file['changes'])
                        if 'patch' in file:
                            code = file['patch']
                            code_rows = str(code).split('\n')
                            for i in range(0, len(code_rows)):
                                if i == 0:
                                    continue
                                row = code_rows[i]
                                pre_row = code_rows[i - 1]
                                if (not row.startswith('-')) and (not(row.startswith('+'))):
                                    if pre_row.startswith('+'):
                                        add_segs += 1
                                    if pre_row.startswith('-'):
                                        del_segs += 1
                                if pre_row.startswith('-') and row.startswith('+'):
                                    del_segs += 1
                                if pre_row.startswith('+') and row.startswith('-'):
                                    add_segs += 1
                    segs = add_segs + del_segs
                    file_name_list = file_name_list[1:len(file_name_list)]
                    file_changes_list = file_changes_list[1:len(file_changes_list)]

                data.loc[len(data)] = [sha, belong_to_PR, author, changes, additions, deletions, segs, add_segs, del_segs,
                     file_name_list,  has_test, file_added, file_updated,
                     file_deleted, test_churn, non_test_churn, directory_num, file_changes_list]


        # 这里要先把所有commit完整文件下载下来，才能知道文件总行数，为以后计算proportion作准备
        # 注意该仓库的爬取非常不稳定，一定挂梯子并且设置重试次数

        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()
        #由于最大打开文件数限制，此处要设置协程并发数量
        sem = asyncio.Semaphore(500)
        tasks = []
        file_download_dir = Config.data_dir + '/commit/commitFiles'  #下载commit中文件的目录
        if not os.path.exists(file_download_dir):
            os.mkdir(file_download_dir)

        for url in down_url_list:
            save_name = url[len('https://github.com/' + Config.repoName + '/raw/'): len(url)]
            tmp_split = save_name.split('/')
            save_name = tmp_split[0] + '%' + tmp_split[1]
            task = asyncio.ensure_future(self.download_file(url, file_download_dir, save_name, sem))
            tasks.append(task)

        # print('下载所有commit涉及文件')
        # loop.run_until_complete(asyncio.wait(tasks))
        # print('补充commit中涉及文件的总行数（为以后计算proportion作准备）')

        data['total_file_lines'] = 0
        for i in range(0, len(data)):
            instance = data.iloc[i]
            sha = instance['sha']
            cur_changes = instance['changes']
            total_file_lines = 0
            file_list = os.listdir(file_download_dir)
            for file in file_list:
                if sha in file:
                    with open(file_download_dir + '/' + file, encoding='utf-8') as a:
                        total_file_lines += len(a.readline())
            instance['total_file_lines'] = total_file_lines + cur_changes
            data.iloc[i] = instance

        data.to_excel(Config.data_dir + '/PR_commit_info.xlsx', index=False)
        print('PR_commit内容提取完成')



    async def download_file(self, url, dir_name, number, sem):
        # 这里必须有这个配置connector以及trust_env, 否则爬不下来
        con = aiohttp.TCPConnector(ssl=False)
        async with sem: #控制并发数量
            async with aiohttp.ClientSession(connector = con,  trust_env = True) as session:
                file_name = dir_name + '/' + number + '.txt'
                await self.fetchData_file(url, number, file_name, session)
                print(number + " 的数据获取完成")

    async def fetchData_file(self, url, number, file_name, session):
        try:
            headers = {'User-Agent': next(self.user_iter), 'Authorization': 'token ' + next(self.token_iter)}
            async with session.get(url, ssl=False, headers=headers) as response:
                if response.status != 200:
                    raise Exception
                f = open(file_name, 'wb');
                s = await response.text();
                bytes = s.encode('utf-8')
                f.write(bytes)
                f.close()
        except Exception as e:   #爬取githubusercontent非常不稳定，此处只设置了一次重试机会。如果不希望损失文件，可设置为递归调用
            try:
                headers = {'User-Agent': next(self.user_iter), 'Authorization': 'token ' + next(self.token_iter)}
                async with session.get(url, ssl=False, headers=headers) as response:
                    if response.status != 200:
                        raise Exception
                    f = open(file_name, 'wb');
                    s = await response.text();
                    bytes = s.encode('utf-8')
                    f.write(bytes)
                    f.close()
            except Exception as e:
                print(e)


    def get_PR_comments_list(self):
        data = pd.read_excel(Config.data_dir + '/PR_info.xlsx')
        data = pd.DataFrame(data)
        numberList = data['number'].tolist()

        list_dir = Config.data_dir + '/comment'
        if not os.path.exists(list_dir):
            os.mkdir(list_dir)
        list_dir = Config.data_dir + '/comment/commentList'
        if not os.path.exists(list_dir):
            os.mkdir(list_dir)

        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()
        tasks = []
        for item in numberList:
            targetUrl = 'https://api.github.com/repos/' + Config.repoName + '/issues/' + str(item) + '/comments'
            task = asyncio.ensure_future(self.download(targetUrl, list_dir, str(item)))
            tasks.append(task)
        loop.run_until_complete(asyncio.wait(tasks))
        print('done')


    def save_PR_comment_info(self):
        data = pd.DataFrame(
            columns=['id', 'belong_to_PR', 'reviewer', 'created_at', 'updated_at', 'body'])

        dic = Config.data_dir + '/comment/commentList'  #遍历所有comment
        for file in os.listdir(dic):
            with open(dic + '/' + file, encoding='utf-8') as a:
                jsonContent_list = json.load(a)
                for jsonContent in jsonContent_list:
                    id = jsonContent['id']
                    belong_to_PR = str(file.split('.')[0])
                    reviewer = jsonContent['user']['login']
                    created_at = jsonContent['created_at']
                    updated_at = jsonContent['updated_at']
                    body = jsonContent['body']
                    data.loc[len(data)] = [id, belong_to_PR, reviewer, created_at, updated_at, body]
        data.to_excel(Config.data_dir + '/PR_comment_info.xlsx', index=False)



    def get_follow_relation(self):
        data_PR = pd.read_excel(Config.data_dir + '/PR_info.xlsx')
        data_PR = pd.DataFrame(data_PR)
        data_comment = pd.read_excel(Config.data_dir + '/PR_comment_info.xlsx')
        data_comment = pd.DataFrame(data_comment)
        data_commit = pd.read_excel(Config.data_dir + '/PR_commit_info.xlsx')
        data_commit = pd.DataFrame(data_commit)

        all_people = data_PR['author'].tolist() +  data_comment['reviewer'].tolist() + data_commit['author'].tolist()
        all_people = list(set(all_people))

        print('用户总数：' + str(len(all_people)))
        follows_list_dir = Config.data_dir + '/relation'
        if not os.path.exists(follows_list_dir):
            os.mkdir(follows_list_dir)

        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()
        sem = asyncio.Semaphore(500)
        tasks = []

        print('下载follow关系')
        for people1 in all_people:
            for people2 in all_people:
                targetUrl = 'https://api.github.com/users/' + str(people1) + '/following/' + str(people2)
                task = asyncio.ensure_future(self.download_state(targetUrl, follows_list_dir, str(people1) + '_' +  str(people2), sem))
                tasks.append(task)

        loop.run_until_complete(asyncio.wait(tasks))
        print('done')


    async def download_state(self, url, dir_name, number, sem):
        async with sem:
            async with aiohttp.ClientSession() as session:
                file_name = dir_name + '/' + number
                await self.fetch_state(url, number, file_name, session)
                print(number + " 的数据获取完成")

    async def fetch_state(self, url, number, file_name, session):
        headers = {'User-Agent': next(self.user_iter), 'Authorization': 'token ' + next(self.token_iter)}
        async with session.get(url, ssl=False, headers=headers
                               ) as response:
            print(response.status)
            if response.status == 204:
                file_name += '_true' + '.txt'
                f = open(file_name, 'wb')
                s = await response.text()
                bytes = s.encode('utf-8')
                f.write(bytes)
                f.close()
            else:
                print(file_name )
                file_name += '_false' + '.txt'
                f = open(file_name, 'wb')
                s = await response.text()
                bytes = s.encode('utf-8')
                f.write(bytes)
                f.close()


    def save_follow_relation(self):
        data_PR = pd.read_excel(Config.data_dir + '/PR_info.xlsx')
        data_PR = pd.DataFrame(data_PR)
        data_comment = pd.read_excel(Config.data_dir + '/PR_comment_info.xlsx')
        data_comment = pd.DataFrame(data_comment)
        data_commit = pd.read_excel(Config.data_dir + '/PR_commit_info.xlsx')
        data_commit = pd.DataFrame(data_commit)

        all_people = data_PR['author'].tolist() + data_comment['reviewer'].tolist() + data_commit['author'].tolist()
        all_people = list(set(all_people))


        data = pd.DataFrame(
            columns=['user1', 'user2', 'follow'])

        for people1 in all_people:
            for people2 in all_people:
                true_file_name = Config.data_dir + '/relation/' + str(people1) + '_' + str(people2) + '_' + 'true.txt'
                if os.path.exists(true_file_name):
                    data.loc[len(data)] = [people1, people2, True]
                else:
                    data.loc[len(data)] = [people1, people2, False]

        data.to_excel(Config.data_dir + '/user_relation_info.xlsx', index=False)


