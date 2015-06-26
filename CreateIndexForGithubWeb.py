import urllib.request
import json
import re

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
        except:
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

if __name__ == '__main__':
    #Please use your own path of 'index_for_web.json'
    index_for_web_path = r'C:\Users\wujz\Desktop\index_for_web.json'
    createIndexForWeb(index_for_web_path)
