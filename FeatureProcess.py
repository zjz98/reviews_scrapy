import textstat
from datetime import timedelta
import datetime
import numpy as np
from datetime import date
import re
import networkx as nx
import pandas as pd
import openpyxl
import xlsxwriter
from Utils import Utils


from Config import Config
import shutil


class FeatureProcess:

    def process_PR_feature(self):
        utils = Utils()
        data_PR = pd.read_excel(Config.data_dir + '/PR_info.xlsx')
        data_PR = pd.DataFrame(data_PR)
        data_comment = pd.read_excel(Config.data_dir + '/PR_comment_info.xlsx')
        data_comment = pd.DataFrame(data_comment)
        data_commit = pd.read_excel(Config.data_dir + '/PR_commit_info.xlsx')
        data_commit = pd.DataFrame(data_commit)

        feature_PR = pd.DataFrame(
            columns=['number', 'directory_num', 'language_num', 'file_type', 'has_test',
                     'has_feature', 'has_bug', 'has_document', 'has_improve', 'has_refactor',
                     'title_length', 'title_readability', 'title_embedding', 'body_length',
                     'body_readability', 'body_embedding', 'lines_added', 'lines_deleted',
                     'segs_added', 'segs_deleted', 'segs_updated', 'files_added', 'files_deleted',
                     'files_updated', 'modify_proportion', 'modify_entropy', 'test_churn', 'non_test_churn',
                     'reviewer_num', 'bot_reviewer_num', 'is_reviewed', 'comment_num', 'comment_length',
                     'comment_embedding', 'last_comment_mention']) #34个特征

        for i in range(0, len(data_PR)):
            if i % 10 == 0:
                print('PR特征处理进度：' + str(i) + ' / ' + str(len(data_PR)))
            instance = data_PR.iloc[i]
            #2个可直接从PR中获取的特征
            number = instance['number']
            lines_added = instance['additions']
            lines_deleted = instance['deletions']

            #11个通过PR的title和body获取的特征
            has_feature = False
            has_bug = False
            has_document = False
            has_improve = False
            has_refactor = False
            title = instance['title']
            if 'feature' in title:
                has_feature = True
            if 'bug' in title:
                has_bug = True
            if 'document' in title:
                has_document = True
            if 'improve' in title:
                has_improve = True
            if 'has_refactor' in title:
                has_refactor = True
            title_length = len(title)
            title_readability = textstat.textstat.coleman_liau_index(title)
            title_embedding = utils.get_embedding(title)
            body = instance['body']
            if isinstance(body, str) :
                body_length = len(body)
                body_readability = textstat.textstat.coleman_liau_index(body)
                body_embedding = utils.get_embedding(body)
            else:
                body_length = 0
                body_readability = 0
                body_embedding = 0


            # 14个通过commit信息获取的特征
            has_test = False
            directory_num = 0
            segs_added = 0
            segs_deleted = 0
            segs_updated = 0
            files_added = 0
            files_deleted = 0
            files_updated = 0
            modify_entropy = 0
            test_churn = 0
            non_test_churn = 0

            languages = utils.get_languages()
            file_type_list = []
            language_list = []
            total_file_lines = 0
            lines_changed_infiles_list = []
            cur_commit_data = data_commit.loc[data_commit['belong_to_PR'] == number]
            for i in range(0, len(cur_commit_data)):
                instance = cur_commit_data.iloc[i]
                if not isinstance(instance['file_changes_list'], str):
                    instance['file_changes_list'] = '0'
                file_changes_list = instance['file_changes_list'].split(';')
                lines_changed_infiles_list.extend(file_changes_list)
                if not isinstance(instance['file_name_list'], str):
                    instance['file_name_list'] = '0'
                if 'test' in instance['file_name_list']:
                    has_test = True
                file_name_list = instance['file_name_list'].split(';')
                for j in range(0, len(file_changes_list)):
                    file = file_changes_list[j]
                    if 'test' in file:
                        test_churn += int(file_changes_list[j])
                    else:
                        non_test_churn += int(file_changes_list[j])

                directory_num += instance['directory_num']
                segs_added += instance['add_segs']
                segs_deleted += instance['del_segs']
                segs_updated += instance['segs']
                files_added += instance['file_added']
                files_deleted += instance['file_deleted']
                files_updated += instance['file_updated']
                total_file_lines += instance['total_file_lines']

                file_list = instance['file_name_list'].split(';')
                for file in file_list:
                    type = str(file.split('.')[-1]).lower()
                    file_type_list.append(type)
                    if type in languages:
                        language_list.append(type)

            language_num = len(set(language_list))
            file_type = len(set(file_type_list))
            modify_proportion = (lines_added + lines_deleted) / total_file_lines
            for item in lines_changed_infiles_list:
                lines = int(item)
                pk = float(lines) / (lines_added + lines_deleted)
                modify_entropy -= pk * np.log2(pk)



            # 7个通过commnet信息获取的特征
            bot_reviewer_num = 0
            is_reviewed = False
            last_comment_mention = False

            reviewer_list = []
            cur_comment_data = data_comment.loc[data_comment['belong_to_PR'] == number]
            total_comment = ''
            last_comment = ''
            if len(cur_comment_data) != 0:
                is_reviewed = True
            comment_num = len(cur_comment_data)
            for i in range(0, len(cur_comment_data)):
                instance = cur_comment_data.iloc[i]
                last_comment = instance['body']
                if 'bot|Bot' in instance['reviewer']:
                    bot_reviewer_num += 1
                else:
                    reviewer_list.append(instance['reviewer'])
                if not isinstance(instance['body'], str):
                    instance['body'] = ' '
                total_comment += instance['body'] + ' '

            reviewer_num = len(set(reviewer_list))
            comment_length = len(total_comment)
            comment_embedding = utils.get_embedding(total_comment)

            if '@' in last_comment:
                last_comment_mention = True

            feature_PR.loc[len(feature_PR)] = [number, directory_num, language_num, file_type, has_test,
                     has_feature, has_bug, has_document, has_improve, has_refactor,
                     title_length, title_readability, title_embedding, body_length,
                     body_readability, body_embedding, lines_added, lines_deleted,
                     segs_added, segs_deleted, segs_updated, files_added, files_deleted,
                     files_updated, modify_proportion, modify_entropy, test_churn, non_test_churn,
                     reviewer_num, bot_reviewer_num, is_reviewed, comment_num, comment_length,
                     comment_embedding, last_comment_mention]

        feature_PR.to_excel(Config.data_dir + '/PR_features.xlsx', index=False)

    def process_project_feature(self):
        utils = Utils()
        feature_project = pd.DataFrame(
            columns=['project_age', 'language_num', 'change_num', 'open_changes', 'author_num', 'reviewer_num',
                     'team_size', 'changes_per_author', 'changes_per_reviewer', 'changes_per_week',
                     'avg_lines', 'avg_segs', 'avg_files', 'add_per_week', 'del_per_week', 'merge_proportion',
                     'avg_reviewers', 'avg_comments', 'avg_rounds', 'avg_duration', 'avg_rounds_merged',
                     'avg_duration_merged', 'avg_churn_merged', 'avg_files_merged', 'avg_comments_merged',
                     'avg_rounds_abandoned', 'avg_duration_abandoned', 'avg_churn_abandoned',
                     'avg_files_abandoned', 'avg_comments_abandoned'])  # 30个特征

        data_PR = pd.read_excel(Config.data_dir + '/PR_info.xlsx')
        data_PR = pd.DataFrame(data_PR)
        data_comment = pd.read_excel(Config.data_dir + '/PR_comment_info.xlsx')
        data_comment = pd.DataFrame(data_comment)
        data_commit = pd.read_excel(Config.data_dir + '/PR_commit_info.xlsx')
        data_commit = pd.DataFrame(data_commit)

        project_age = utils.get_project_duration()
        language_num = len(utils.get_languages())
        change_num = len(data_PR)
        open_changes_data = data_PR.loc[data_PR['state'] == 'open']
        open_changes = len(open_changes_data)


        author_list = []
        total_lines = 0
        total_segs = 0
        total_files = 0
        total_adds = 0
        total_dels = 0

        for i in range(0, len(data_commit)):
            instance = data_commit.iloc[i]
            author_list.append(instance['author'])
            total_lines += instance['changes']
            total_segs += instance['segs']
            total_files += instance['file_updated']
            total_adds += instance['additions']
            total_dels += instance['deletions']
        author_num = len(set(author_list))
        changes_per_author = change_num / author_num
        avg_lines = total_lines / change_num
        avg_segs = total_segs / change_num
        avg_files = total_files / change_num
        add_per_week = total_adds / (project_age / 7)
        del_per_week = total_dels / (project_age / 7)

        reviewer_list = []
        for i in range(0, len(data_comment)):
            instance = data_comment.iloc[i]
            reviewer_list.append(instance['reviewer'])
        reviewer_num = len(set(reviewer_list))
        team_size = author_num + reviewer_num
        changes_per_reviewer = change_num / reviewer_num
        changes_per_week = change_num / (project_age / 7)
        avg_reviewers = reviewer_num / change_num
        avg_comments = len(data_comment) / change_num
        avg_rounds = len(data_commit) / change_num


        total_merges = 0
        total_duration = 0
        total_comments = 0
        total_rounds = 0
        total_duration_merged = 0
        total_churn_merged = 0
        total_round_merged = 0
        total_files_merged = 0
        total_comments_merged = 0
        total_rounds_abandoned = 0
        total_duration_abandoned = 0
        total_churn_abandoned = 0
        total_files_abandoned = 0
        total_comments_abandoned = 0
        for i in range(0, len(data_PR)):
            instance = data_PR.iloc[i]
            if instance['merged'] == True:
                total_merges += 1
                total_duration_merged += utils.cal_duration(instance['created_at'], instance['updated_at'])
                total_churn_merged += instance['additions'] + instance['deletions']
                total_round_merged += instance['commits']
                total_files_merged += instance['changed_files']
                total_comments_merged += instance['comments']
            if instance['merged'] == False and instance['state'] == 'closed':
                total_rounds_abandoned += instance['commits']
                total_duration_abandoned += utils.cal_duration(instance['created_at'], instance['updated_at'])
                total_churn_abandoned += instance['additions'] + instance['deletions']
                total_files_abandoned += instance['changed_files']
                total_comments_abandoned += instance['comments']
            total_duration += utils.cal_duration(instance['created_at'], instance['updated_at'])
        merge_proportion = total_merges / change_num
        avg_duration = total_duration / change_num
        avg_duration_merged = total_duration_merged / change_num
        avg_churn_merged = total_churn_merged / change_num
        avg_rounds_merged = total_round_merged / change_num
        avg_files_merged = total_files_merged / change_num
        avg_comments_merged = total_comments_merged / change_num
        avg_rounds_abandoned = total_rounds_abandoned / change_num
        avg_duration_abandoned = total_duration_abandoned / change_num
        avg_churn_abandoned = total_churn_abandoned / change_num
        avg_files_abandoned = total_files_abandoned / change_num
        avg_comments_abandoned = total_comments_abandoned / change_num

        feature_project.loc[len(feature_project)] = [project_age, language_num, change_num, open_changes, author_num,
                    reviewer_num, team_size, changes_per_author, changes_per_reviewer, changes_per_week,
                    avg_lines, avg_segs, avg_files, add_per_week, del_per_week, merge_proportion,
                    avg_reviewers, avg_comments, avg_rounds, avg_duration, avg_rounds_merged,
                    avg_duration_merged, avg_churn_merged, avg_files_merged, avg_comments_merged,
                    avg_rounds_abandoned, avg_duration_abandoned, avg_churn_abandoned,
                    avg_files_abandoned, avg_comments_abandoned]

        feature_project.to_excel(Config.data_dir + '/project_features.xlsx', index=False)



    def process_author_feature(self):
        utils = Utils()
        feature_author = pd.DataFrame(
            columns=['name','experience', 'is_reviewer', 'change_num', 'participation', 'changes_per_week', 'avg_round',
                     'avg_duration', 'merge_proportion', 'degree_centrality', 'closeness_centrality',
                     'betweenness_centrality', 'eigenvector_centrality', 'clustering_coefficient','k_coreness']) #14个

        data_PR = pd.read_excel(Config.data_dir + '/PR_info.xlsx')
        data_PR = pd.DataFrame(data_PR)
        data_comment = pd.read_excel(Config.data_dir + '/PR_comment_info.xlsx')
        data_comment = pd.DataFrame(data_comment)
        data_commit = pd.read_excel(Config.data_dir + '/PR_commit_info.xlsx')
        data_commit = pd.DataFrame(data_commit)


        social_network_lookback = 60
        created_at_list =  list(data_PR['created_at'])
        created_at_list.sort() #第一个PR时间
        first_PR_date = created_at_list[0]
        first_PR_date = datetime.datetime.strptime(first_PR_date, "%Y-%m-%dT%H:%M:%SZ")
        social_network_start_time = first_PR_date - timedelta(days=social_network_lookback)
        active_changes = pd.DataFrame(columns = ['author', 'created_at', 'reviewers'])
        for i in range(0, len(data_PR)):
            instance = data_PR.iloc[i]
            author = instance['author']
            created_at = datetime.datetime.strptime(instance['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            cur_comment = data_comment.loc[data_comment['belong_to_PR'] == instance['number']]
            reviewers = []
            for j in range(0, len(cur_comment)):
                instance_c = cur_comment.iloc[j]
                reviewers.append(instance_c['reviewer'])
            active_changes.loc[len(active_changes)] = [author, created_at, reviewers]

        author_list = list(set(data_PR['author']))
        for i in range(0, len(author_list)):
            if i % 10 == 0:
                print('作者特征处理进度：' + str(i) + ' / ' + str(len(author_list)))
            process_author = author_list[i]
            author_PR = data_PR.loc[data_PR['author'] == process_author]
            author_PR_time_list = list(author_PR['created_at'])
            author_PR_time_list.sort()
            author_first_PR = author_PR_time_list[0]
            cur_date = date.today().strftime('%Y-%m-%dT%H:%M:%SZ')
            experience = utils.cal_duration(author_first_PR, cur_date)
            is_reviewer = False
            if process_author in list(data_comment['reviewer']):
                is_reviewer = True
            change_num = len(author_PR)
            participation = change_num / len(data_PR)
            changes_per_week = change_num / (experience / 7)
            total_round = 0
            total_duration = 0
            total_merges = 0
            for j in range(0, len(author_PR)):
                instance = author_PR.iloc[j]
                total_round += instance['commits']
                total_duration += utils.cal_duration(instance['created_at'], instance['updated_at'])
                if instance['merged'] == True:
                    total_merges += 1
            avg_round = total_round / change_num
            avg_duration = total_duration / change_num
            merge_proportion = total_merges / change_num

            #关系
            #所有PR(author，created_at, reviewer列表)，作者...
            authors_social_features = self.cal_author_social_features(active_changes, process_author, social_network_start_time)
            degree_centrality = authors_social_features['degree_centrality']
            closeness_centrality = authors_social_features['closeness_centrality']
            betweenness_centrality = authors_social_features['betweenness_centrality']
            eigenvector_centrality = authors_social_features['eigenvector_centrality']
            clustering_coefficient = authors_social_features['clustering_coefficient']
            k_coreness = authors_social_features['k_coreness']

            feature_author.loc[len(feature_author)] = [process_author, experience, is_reviewer, change_num, participation,
                      changes_per_week, avg_round, avg_duration, merge_proportion, degree_centrality,
                      closeness_centrality, betweenness_centrality, eigenvector_centrality,
                      clustering_coefficient, k_coreness]

        feature_author.to_excel(Config.data_dir + '/author_features.xlsx', index=False)


    def process_reviewer_feature(self):
        utils = Utils()
        feature_reviewer = pd.DataFrame(
            columns=['name', 'experience', 'is_author', 'change_num', 'participation', 'avg_comments','avg_files', 'avg_round',
                     'avg_duration', 'merge_proportion', 'degree_centrality', 'closeness_centrality',
                     'betweenness_centrality', 'eigenvector_centrality', 'clustering_coefficient','k_coreness']) #15个
        data_PR = pd.read_excel(Config.data_dir + '/PR_info.xlsx')
        data_PR = pd.DataFrame(data_PR)
        data_comment = pd.read_excel(Config.data_dir + '/PR_comment_info.xlsx')
        data_comment = pd.DataFrame(data_comment)
        data_commit = pd.read_excel(Config.data_dir + '/PR_commit_info.xlsx')
        data_commit = pd.DataFrame(data_commit)

        social_network_lookback = 60
        created_at_list =  list(data_PR['created_at'])
        created_at_list.sort() #第一个PR时间
        first_PR_date = created_at_list[0]
        first_PR_date = datetime.datetime.strptime(first_PR_date, "%Y-%m-%dT%H:%M:%SZ")
        social_network_start_time = first_PR_date - timedelta(days=social_network_lookback)
        active_changes = pd.DataFrame(columns = ['author', 'created_at', 'reviewers'])
        for i in range(0, len(data_PR)):
            instance = data_PR.iloc[i]
            author = instance['author']
            created_at = datetime.datetime.strptime(instance['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            cur_comment = data_comment.loc[data_comment['belong_to_PR'] == instance['number']]
            reviewers = []
            for j in range(0, len(cur_comment)):
                instance_c = cur_comment.iloc[j]
                reviewers.append(instance_c['reviewer'])
            active_changes.loc[len(active_changes)] = [author, created_at, reviewers]

        reviewer_list = list(set(data_comment['reviewer']))
        for i in range(0, len(reviewer_list)):
            if i % 10 == 0:
                print('评审者特征处理进度：' + str(i) + ' / ' + str(len(reviewer_list)))
            process_reviewer = reviewer_list[i]
            reviewer_comments = data_comment.loc[data_comment['reviewer'] == process_reviewer]
            reviewer_comment_time_list = list(reviewer_comments['created_at'])
            reviewer_comment_time_list.sort()
            reviewer_first_comment = reviewer_comment_time_list[0]
            cur_date = date.today().strftime('%Y-%m-%dT%H:%M:%SZ')
            experience = utils.cal_duration(reviewer_first_comment, cur_date)
            is_author = False
            if process_reviewer in list(data_PR['author']):
                is_author = True
            change_num = len(set(reviewer_comments['belong_to_PR']))
            participation = change_num / len(data_PR)
            avg_comments = len(reviewer_comments) / change_num
            total_files = 0
            total_round = 0
            total_duration = 0
            total_merges = 0
            for j in range(0, len(reviewer_comments)):
                instance = reviewer_comments.iloc[j]
                PR_num = instance['belong_to_PR']
                reviewer_PR = data_PR.loc[data_PR['number'] == PR_num]
                for k in range(0, len(reviewer_PR)):
                    instance_pr = reviewer_PR.iloc[k]
                    total_files += instance_pr['changed_files']
                    total_round += instance_pr['commits']
                    if instance_pr['merged'] == True:
                        total_merges += 1
                total_duration += utils.cal_duration(instance['created_at'], instance['updated_at'])

            avg_files = total_files / change_num
            avg_round = total_round / change_num
            avg_duration = total_duration / change_num
            merge_proportion = total_merges / change_num

            #关系
            #所有PR(author，created_at, reviewer列表)，作者...
            authors_social_features = self.cal_author_social_features(active_changes, process_reviewer, social_network_start_time)
            degree_centrality = authors_social_features['degree_centrality']
            closeness_centrality = authors_social_features['closeness_centrality']
            betweenness_centrality = authors_social_features['betweenness_centrality']
            eigenvector_centrality = authors_social_features['eigenvector_centrality']
            clustering_coefficient = authors_social_features['clustering_coefficient']
            k_coreness = authors_social_features['k_coreness']

            feature_reviewer.loc[len(feature_reviewer)] = [process_reviewer, experience, is_author, change_num, participation,
                      avg_comments, avg_files, avg_round, avg_duration, merge_proportion, degree_centrality,
                      closeness_centrality, betweenness_centrality, eigenvector_centrality,
                      clustering_coefficient, k_coreness]

        feature_reviewer.to_excel(Config.data_dir + '/reviewer_features.xlsx', index=False)



    def cal_author_social_features(self, df, author, start_time):
        graph_df = df
        graph_df = graph_df[graph_df['created_at'] >= start_time]
        owners, reviewers_list = graph_df['author'].values, graph_df['reviewers'].values

        graph = nx.Graph()
        for index in range(graph_df.shape[0]):
            owner, reviewers = owners[index], reviewers_list[index]
            for reviewer in reviewers:
                if reviewer == owner:
                    continue
                try:
                    graph[owner][reviewer]['weight'] += 1
                except (KeyError, IndexError):
                    graph.add_edge(owner, reviewer, weight=1)

        network = SocialNetwork(graph, author)
        # network.show_graph()
        return {
            'degree_centrality': network.degree_centrality(),
            'closeness_centrality': network.closeness_centrality(),
            'betweenness_centrality': network.betweenness_centrality(),
            'eigenvector_centrality': network.eigenvector_centrality(),
            'clustering_coefficient': network.clustering_coefficient(),
            'k_coreness': network.k_coreness()
        }



    def cal_reviewers_social_features(self, df, reviewers, start_time):
        graph_df = df
        graph_df = graph_df[graph_df['created_at'] >= start_time]

        owners, reviewers_list = graph_df['owner'].values, graph_df['reviewers'].values
        graph = nx.Graph()
        for index in range(graph_df.shape[0]):
            owner, reviewers = owners[index], reviewers_list[index]
            for reviewer in reviewers:
                if reviewer == owner:
                    continue
                try:
                    graph[owner][reviewer]['weight'] += 1
                except (KeyError, IndexError):
                    graph.add_edge(owner, reviewer, weight=1)

        degree_centrality = 0
        closeness_centrality = 0
        betweenness_centrality = 0
        eigenvector_centrality = 0
        clustering_coefficient = 0
        k_coreness = 0

        for reviewer in reviewers:
            network = SocialNetwork(graph, reviewer)
            degree_centrality += network.degree_centrality()
            closeness_centrality += network.closeness_centrality()
            betweenness_centrality += network.betweenness_centrality()
            eigenvector_centrality += network.eigenvector_centrality()
            clustering_coefficient += network.clustering_coefficient()
            k_coreness += network.k_coreness()

        # network.show_graph()
        return {
            'degree_centrality': float(degree_centrality) / len(reviewers) if len(reviewers) > 0 else 0,
            'closeness_centrality': float(closeness_centrality) / len(reviewers) if len(reviewers) > 0 else 0,
            'betweenness_centrality': float(betweenness_centrality) / len(reviewers) if len(reviewers) > 0 else 0,
            'eigenvector_centrality': float(eigenvector_centrality) / len(reviewers) if len(reviewers) > 0 else 0,
            'clustering_coefficient': float(clustering_coefficient) / len(reviewers) if len(reviewers) > 0 else 0,
            'k_coreness': float(k_coreness) / len(reviewers) if len(reviewers) > 0 else 0
        }


    def process_final_feature(self):
        utils = Utils()
        data_PR = pd.read_excel(Config.data_dir + '/PR_info.xlsx')
        data_PR = pd.DataFrame(data_PR)
        data_project = pd.read_excel(Config.data_dir + '/project_features.xlsx')
        data_project = pd.DataFrame(data_project)
        data_author = pd.read_excel(Config.data_dir + '/author_features.xlsx')
        data_author = pd.DataFrame(data_author)
        data_reviewer = pd.read_excel(Config.data_dir + '/reviewer_features.xlsx')
        data_reviewer = pd.DataFrame(data_reviewer)


        data_project = pd.DataFrame(data_project.values.tolist(),index=np.arange(len(data_PR)),columns=data_project.columns)
        data_PR.join(data_project)

        empty_author = pd.DataFrame(data_author.values.tolist(),index=np.arange(len(data_PR)),columns=data_author.columns)
        data_PR.join(empty_author)

        empty_reviewer = pd.DataFrame(data_reviewer.values.tolist(), index=np.arange(len(data_PR)), columns=data_reviewer.columns)
        data_PR.join(empty_reviewer)

        for i in range(0, len(data_PR)):
            instance = data_PR.iloc[i]
            cur_author_info = data_author.loc[data_author['name'] == data_PR['author']].iloc[0]
            instance['experience'] = cur_author_info['experience']
            instance['is_reviewer'] = cur_author_info['is_reviewer']
            instance['change_num'] = cur_author_info['experience']
            instance['participation'] = cur_author_info['participation']
            instance['changes_per_week'] = cur_author_info['changes_per_week']
            instance['avg_round'] = cur_author_info['avg_round']
            instance['avg_duration'] = cur_author_info['avg_duration']
            instance['merge_proportion'] = cur_author_info['merge_proportion']
            instance['degree_centrality'] = cur_author_info['degree_centrality']
            instance['closeness_centrality'] = cur_author_info['closeness_centrality']
            instance['betweenness_centrality'] = cur_author_info['betweenness_centrality']
            instance['eigenvector_centrality'] = cur_author_info['eigenvector_centrality']
            instance['clustering_coefficient'] = cur_author_info['clustering_coefficient']
            instance['k_coreness'] = cur_author_info['k_coreness']







class SocialNetwork:
    def __init__(self, graph, owner):
        self.graph = graph
        self.owner = owner
        self.lcc = self.largest_connected_component()

    def show_graph(self):
        nx.draw(self.graph, with_labels=True, font_weight='bold')


    def largest_connected_component(self):
        try:
            return self.graph.subgraph(max(nx.connected_components(self.graph), key=len))
        except:
            return self.graph

    def degree_centrality(self):
        nodes_dict = nx.degree_centrality(self.lcc)
        try:
            return nodes_dict[self.owner]
        except:
            return 0

    def closeness_centrality(self):
        try:
            return nx.closeness_centrality(self.lcc, u=self.owner)
        except:
            return 0

    def betweenness_centrality(self):
        nodes_dict = nx.betweenness_centrality(self.lcc, weight='weight')
        try:
            return nodes_dict[self.owner]
        except:
            return 0

    def eigenvector_centrality(self):
        try:
            eigenvector_centrality = nx.eigenvector_centrality(self.lcc)
            try:
                return eigenvector_centrality[self.owner]
            except:
                return 0
        except:
            return 0

    def clustering_coefficient(self):
        try:
            return nx.clustering(self.lcc, nodes=self.owner, weight='weight')
        except:
            return 0

    def k_coreness(self):
        nodes_dict = nx.core_number(self.lcc)
        try:
            return nodes_dict[self.owner]
        except:
            return 0
