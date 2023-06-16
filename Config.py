import pymongo
import argparse
import os




#配置类，包括数据爬取参数设置 和 模型参数配置

class Config:

    ############################
    #
    # 在此配置主要参数
    #
    ###########################

    name = 'laravel'

    repoName = 'laravel/laravel'

    repoMetaApi = 'https://api.github.com/repos/' + repoName

    repoLanguageApi = 'https://api.github.com/repos/' + repoName + '/languages'

    repoPRListApi = 'https://api.github.com/repos/' + repoName + '/pulls'

    repoPRDetailApi = 'https://api.github.com/repos/' + repoName + '/pulls/'  # prNumber

    repoCommentApi = 'https://api.github.com/repos/' + repoName + '/issues/xxx/comments'

    repoCommitListApi = 'https://api.github.com/repos/' + repoName + '/pulls/xxxx/commits'

    repoCommitDetailApi = 'https://api.github.com/repos/' + repoName + '/commits/' # commitSHA



    # 文件存储位置（当前目录下data文件夹下）

    data_dir = 'data/' + name


    #测试开关（测试时减少数据量）,运行时务必设置为False
    test = True


    # 需要参与模型训练的列（当前纳入的特征）
    train_col = ['message_len', 'code_change', 'additions', 'deletions', 'file_count',
                            'sensitive_file_count',	'sensitive_file_rows', 'author_commit_counts',
                             'author_commit_frequency', 'message_deviation', 'match_score_wordnet']

    train_col_without = ['message_len', 'code_change', 'additions', 'deletions', 'file_count',
                            'sensitive_file_count',	'sensitive_file_rows']

    train_col_with = ['message_len', 'code_change', 'additions', 'deletions', 'file_count',
                         'sensitive_file_count', 'sensitive_file_rows', 'message_deviation', 'match_score_wordnet']


    ############################
    #
    # 其他配置
    #
    ###########################


    #github restapi访问速率限制为5000 per hour
    #当一小时内需要下载数据量超过5000时可以使用代理，但速度会较慢
    openProxy = False


    # token库，用来访问restapi
    # 每个token在一小时内可访问5000次，可进行配置叠加性能
    # token有过期时间，过期后在github账号里重新生成
    # 注意，由于review数据过多，运行代码前一定要多注册一些github账号并生成token添加在这里
    token_list = [
         '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', #1940752402@qq.com
         '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', #forScrapy1@outlook.com
         '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', #forScrapy2@outlook.com
         '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' #forScrapy3@outlook.com
    ]



    user_list = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 ",
        "(KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 ",
        "(KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 ",
        "(KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 ",
        "(KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 ",
        "(KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 ",
        "(KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 ",
        "(KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 ",
        "(KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 ",
        "(KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 ",
        "(KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 ",
        "(KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 ",
        "(KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 ",
        "(KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 ",
        "(KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 ",
        "(KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 ",
        "(KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 ",
        "(KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 ",
        "(KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    ]

