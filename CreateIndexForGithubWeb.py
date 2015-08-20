import urllib.request
import urllib.error
import json
import re

UNICODE_ERROR_LIST = []
HTTP_ERROR_LIST = []
VALUE_ERROR_LIST = []
OTHER_ERROR_LIST = []

def createIndexForWeb(index_for_web_path):
    #read name and desc info from api.github.com
    api_url = "https://api.github.com/orgs/ibmpredictiveanalytics/repos?per_page=1000"
    raw_info_json_url = 'https://raw.githubusercontent.com/IBMPredictiveAnalytics/repos_name/master/info.json'

    #key_list for repository info.json
    key_list = ['type', 'provider', 'software', 'language', 'category', 'promotion']
    indent_space = '    '

    api_json_data = json.loads(urllib.request.urlopen(api_url).read().decode('utf-8'))
    index_for_web_json = "{\n\"repository_index\":[\n"
    index_for_web = open(index_for_web_path,'w')

    for item in api_json_data:
        repo_name = item['name']
        #ignore .io repository
        if('IBMPredictiveAnalytics.github.io' == repo_name):
            continue
        
        repo_desc = item['description']
        repo_push_time = item['pushed_at']
        repo_info_json_url = re.sub('repos_name', repo_name, raw_info_json_url)
        try:
            repo_info_json = json.loads(urllib.request.urlopen(repo_info_json_url).read().decode('utf-8'))
        except UnicodeDecodeError as e:
            UNICODE_ERROR_LIST.append(repo_name+"  "+repo_push_time)
            continue
        except urllib.error.HTTPError as e:
            HTTP_ERROR_LIST.append(repo_name+"  "+repo_push_time)
            continue
        except ValueError as e:
            VALUE_ERROR_LIST.append(repo_name+"  "+repo_push_time)
            continue
        except Exception as e:
            OTHER_ERROR_LIST.append(repo_name+"  "+repo_push_time)
            continue
        
        json_item = indent_space+'{\n'
        json_item += indent_space + indent_space + "\"repository\":" +"\"" + repo_name +"\",\n" 
        json_item += indent_space + indent_space + "\"description\":" +"\"" + repo_desc +"\",\n"
        json_item += indent_space + indent_space + "\"pushed_at\":" +"\"" + repo_push_time +"\",\n" 
        
        for key in key_list:
            if type(repo_info_json[key]) == list:
                val = repo_info_json[key][0]
            else:
                val = repo_info_json[key]
            json_item += indent_space + indent_space + "\"" + key + "\":" + "\"" + val + "\",\n"
        json_item = json_item[0:-2]+'\n'
        json_item += indent_space + "},\n"  
        index_for_web_json += json_item
    index_for_web_json = index_for_web_json[0:-2]
    index_for_web_json += '\n]\n}'
    index_for_web.write(index_for_web_json)  
    index_for_web.close()

def printError(error_list, error_msg):
    for repo_name in error_list:
        print(error_msg+": "+repo_name)

if __name__ == '__main__':
    #Please use your own path of 'index_for_web.json'
    index_for_web_path = r'C:\Users\wujz\Desktop\index_for_web.json'
    createIndexForWeb(index_for_web_path)
    printError(UNICODE_ERROR_LIST, "UnicodeDecodeError")
    printError(HTTP_ERROR_LIST, "HTTPError")
    printError(VALUE_ERROR_LIST, "ValueError")
    printError(OTHER_ERROR_LIST, "Other exception")
