# -*- coding: utf-8 -*-  
import urllib.request
import zipfile
import os
import re
import json
from optparse import OptionParser 
import time 
import math

#"https://github.com/IBMPredictiveAnalytics/repos_name/blob/master/repos_name.spe?raw=true"
SPE_DOWNLOAD_URL = "https://github.com/IBMPredictiveAnalytics/repos_name/raw/master/repos_name.spe"
IMG_DOWNLOAD_URL = "https://raw.githubusercontent.com/IBMPredictiveAnalytics/repos_name/master/default.png"
FILE_NAME= "MANIFEST.MF"
INDEX_FILE = 'index.json'
INDENT = '\t'
LOG_INFO = "log.txt"
META_DIR = 'META-INF'

class JSONObj:
    def __init__(self, key, val):
        self.key, self.val = key, val
    
    def getJSONStr(self):
        return "\""+self.key+"\":\""+ self.val +"\",\n"

class GithubApiInfoObj:
    INDENT = '\t'
    GITHUB_API_URL = "https://api.github.com/orgs/ibmpredictiveanalytics/repos?page={0}&per_page={1}"
    MAX_REPO_NUM = 1000
    PER_PAGE = 100 
    KEY_LIST = ['repository','description','pushed_at']
    REPOSITORY, DESCRIPTION, PUSHED_AT = 0,1,2
    
    def __init__(self):
        self.item_list = []
        for page_index in range(1, math.floor(GithubApiInfoObj.MAX_REPO_NUM/GithubApiInfoObj.PER_PAGE)+1):  
            try:
                api_json_data = json.loads(urllib.request.urlopen(GithubApiInfoObj.GITHUB_API_URL.format(page_index,GithubApiInfoObj.PER_PAGE)).read().decode('utf-8'))
            except:
                raise Exception("Cannot request data from github api: '"+GithubApiInfoObj.GITHUB_API_URL+"'.\n")
            
            if len(api_json_data) == 0:
                break
                        
            for item in api_json_data:  
                temp_json_list = []
                #ignore .io repository
                if('IBMPredictiveAnalytics.github.io' == item['name']):
                    continue 
                  
                for key in GithubApiInfoObj.KEY_LIST:
                    if key == 'repository':
                        key_name_in_api = 'name'
                    else:
                        key_name_in_api= key
        
                    try:
                        temp_json_list.append(JSONObj(key,item[key_name_in_api].strip())) 
                    except:
                        raise Exception("Github api ("+GithubApiInfoObj.GITHUB_API_URL+") does not provide information of "+key+". Please check!\n")
                
                self.item_list.append(temp_json_list)       

class InfoJSONObj:
    KEY_LIST = ['type', 'provider', 'software', 'language', 'category', 'promotion']
    TYPE, PROVIDER, SOFTWARE, LANGUAGE, CATEGORY, PROMOTION = 0,1,2,3,4,5
    RAW_INFO_JSON_URL = 'https://raw.githubusercontent.com/IBMPredictiveAnalytics/repos_name/master/info.json'

    def __init__(self, repo_name):       
        repo_info_json_url = re.sub('repos_name', repo_name, InfoJSONObj.RAW_INFO_JSON_URL)
        try:
            self.repo_info_json = json.loads(urllib.request.urlopen(repo_info_json_url).read().decode('utf-8'))
        except UnicodeDecodeError:
            raise Exception("UnicodeDecodeError: "+repo_name+"'s info.json has non-unicode character. Please check!"+"\nSwitch to next repo.\n\n")
        except urllib.error.HTTPError:
            raise Exception("HTTPError: "+repo_name+"'s info.json does not have info.json, but this may not be a problem. Please check!"+"\nSwitch to next repo.\n\n") 
        except ValueError:
            raise Exception("ValueError: "+repo_name+"'s info.json has an illegal format. Please check!"+"\nSwitch to next repo.\n\n") 
        except Exception:
            raise Exception("Exception: "+repo_name+"'s info.json has an unknown error. Please check!"+"\nSwitch to next repo.\n\n")
        
        self.item_list = []
        for key in InfoJSONObj.KEY_LIST:
            try:
                if type(self.repo_info_json[key]) == list:
                    val = self.repo_info_json[key][0]
                else:
                    val = self.repo_info_json[key]
                self.item_list.append(JSONObj(key,val.strip()))
            except:
                raise ValueError("info.json missed some of the items below:\n"
                                "type, provider, software, language, category, promotion.")       
 
class MetaObj:        
    INDENT = '\t'
    EXTENSION_JSON_TITLE = "extension_detail_info"
    '''
    initialize a MeatObj to save manifest content 
    Input: raw content in MANIFEST.MF
    Output: none
    '''
    def __init__(self,meta_file):  
        self.key_list = []
        meta_content = '' 
        try:
            meta_content, self.key_list = self.parseMetaContent(meta_file)
        except IOError as e:
            print("Manifest file open error: "+str(e))
            raise e
        except Exception as e:
            print("Manifest file format error: "+str(e))
            raise e
        
        self.meta_list = []    
            
        for key in self.key_list:
            val = re.findall(key+"\s*:\s*(.+?)\n",meta_content,re.S)
            if len(val) == 0:
                continue
            self.meta_list.append(JSONObj(key,val[0]))
        
    
    '''
    parse content in manifest file, eliminate extra '\n' and space
    Input: manifest file path
    Output: A string eliminated space and \n in one item 
    '''
    def parseMetaContent(self,meta_file):
        try:
            fp = open(meta_file, 'r')
            meta_content = fp.read()
        except IOError as err:
            raise err
        
        if meta_content != '':
            line_list = meta_content.split('\n')
            modified_str, temp, key_list = '', '', []

            for item in line_list:  
                item = item.replace("\"", "\'")         
                if item[0:1] == ' ':
                    temp = temp+item[1:]            
                else:
                    if len(temp) != 0:
                        modified_str += temp+'\n'
                    temp = item
                    
                    key = re.findall("(.+?)\s*:",item)
                    if len(key) != 0:
                        key_list.append(key[0])
                    elif item != '':
                        raise Exception("Error format of MANIFEST file. One line must only have one ':'")
        return modified_str, key_list
    
    def generateExtensionJSON(self):
        try:
            if len(self.meta_list) == 0:
                raise Exception("Error format of MANIFEST file.")
        except Exception as e:
            raise e
        
        extension_json = INDENT*2+"\""+MetaObj.EXTENSION_JSON_TITLE+"\": {\n"    
        for item in  self.meta_list:
            extension_json += INDENT*3 + item.getJSONStr()
        
        extension_json = extension_json[0:-2]+'\n'
        extension_json += INDENT*2 + "}\n"  
        return extension_json        
            
def getWholeProductName(product_name):
    if(product_name == "stats"):
        return "SPSS Statistics"
    else:
        return "SPSS Modeler"

def generateJSONStr(json_obj_list):
    json_item_str =''
    for item in json_obj_list:            
        json_item_str += INDENT*2 + item.getJSONStr() 
    return json_item_str

if __name__ == '__main__':    
    usage = "usage: %prog [options] arg1 arg2 arg3"  
    parser = OptionParser(usage)  
    parser.add_option("-s", "--spedir", dest="spedir", action='store', help="Directory to save spe.")
    parser.add_option("-o", "--output", dest="outdir", action='store', help="Choose a dir to save index file.")
    parser.add_option("-p", "--product", dest="productName", action='store', help="Choose index for which product: 1. SPSS Modeler 2. SPSS Statistics.")
    (options, args) = parser.parse_args() 

    if not os.path.isdir(options.spedir):
        print(options.spedir)
        parser.error("Please input a valid directory to save spe.")  
    if not os.path.isdir(options.outdir):
        parser.error("Please input a valid directory to create index file.")   
    if options.productName != "modeler" and options.productName != "stats":  
        parser.error("Please input valid product name modeler or stats (casesensitive) for your index file")
    
    #downloadFile(options.spedir,options.outdir, options.productName)
    START_WORDS = "{\n\"productname_extension_index\":[\n"
    index_for_extension = re.sub('productname', options.productName, START_WORDS)
    whole_product_name = getWholeProductName(options.productName)
    
    cur_time = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
    log_fp = open(os.path.join(options.outdir,'log.txt'),'w')
    log_fp.write("Script start: "+cur_time+'\n')
    root_spe_dir = os.path.join(options.spedir,"spe"+cur_time)
    os.mkdir(root_spe_dir)
    
    print("start to get repo data from github ...")
    log_fp.write("start to get repo data from github ...\n\n")
    
    i=0
    ok_repo_num = 0
    try:        
        githubApiInfo_obj = GithubApiInfoObj()
        for item in githubApiInfo_obj.item_list:
            i+=1
            print(i) 
            
            index_for_extension_item = INDENT+"{\n"
            index_for_extension_item += generateJSONStr(item)
            
            repo_name = item[GithubApiInfoObj.REPOSITORY].val
            log_fp.write(str(i)+"th repo: "+repo_name+'\n') 
            print(repo_name)

            try:
                info_json = InfoJSONObj(repo_name)
            except ValueError as e:
                raise e
            except Exception as e:
                print(str(e))
                log_fp.write(str(e))
                continue
                
            index_for_extension_item += generateJSONStr(info_json.item_list)
            repo_software = info_json.item_list[InfoJSONObj.SOFTWARE].val
            index_for_extension_item += INDENT*2 + "\"download_link\":" +"\"" + re.sub('repos_name', repo_name, SPE_DOWNLOAD_URL) +"\",\n"
            index_for_extension_item += INDENT*2 + "\"image_link\":" +"\"" + re.sub('repos_name', repo_name, IMG_DOWNLOAD_URL) +"\",\n"
            
            if repo_software != whole_product_name:
                print("This is not a " + whole_product_name + " repo.\nSwitch to next repo.\n\n\n")
                log_fp.write("This is not a " + whole_product_name + " repo.\nSwitch to next repo.\n\n\n")
                continue
            
            repo_spe_url = re.sub('repos_name', repo_name, SPE_DOWNLOAD_URL)
            spe_name = repo_name+".spe"
            
            spe_saving_path = os.path.join(root_spe_dir,repo_name)
            os.mkdir(spe_saving_path)
            
            try:
                urllib.request.urlretrieve(repo_spe_url, os.path.join(spe_saving_path,spe_name))
                srcZip = zipfile.ZipFile(os.path.join(spe_saving_path,spe_name), "r", zipfile.ZIP_DEFLATED)
            except:
                print("This repo '"+repo_name+"' does not have spe package. Please check!"+"\nSwitch to next repo.\n\n\n")
                log_fp.write("This repo '"+repo_name+"' does not have spe package. Please check!"+"\nSwitch to next repo.\n\n")
                continue
            
            for file in srcZip.namelist():
                if not os.path.isdir(spe_saving_path):     
                    os.mkdir(spe_saving_path)
                if FILE_NAME in file:
                    srcZip.extract(file, spe_saving_path)
            srcZip.close()
            
            meta_path = os.path.join(spe_saving_path, META_DIR, FILE_NAME)
            metaObj = MetaObj(meta_path)
            index_for_extension_item += metaObj.generateExtensionJSON()
            index_for_extension_item += INDENT + "},\n" 
            index_for_extension += index_for_extension_item
            print("Successfully get data!\n\n")
            ok_repo_num += 1
            log_fp.write("Successfully get data!\n\n")

        index_for_extension = index_for_extension[0:-2]
        index_for_extension += '\n]\n}'
        index_for_extension_fp = open(os.path.join(options.outdir, INDEX_FILE),'w')
        index_for_extension_fp.write(index_for_extension)  
        index_for_extension_fp.close()   
            
    except Exception as e:        
        print(str(e))
        log_fp.write(str(e))
    finally:
        print("Totally get "+str(ok_repo_num)+" repo data successfully!\n\n")
        log_fp.write("Totally get "+str(ok_repo_num)+" repo data successfully!\n")
        log_fp.close()
