###################################################################################################################################################################
# This file accesses all ".rdl" files that exist with the reports group project within Gitlab. For each step is an associated function. The program accesses Gitlab, 
# accesses the group project, looks for ".rdl" files in the root directory, then looks for files and then ".rdl" files in all subdirectories. If any files match 
# the ".rdl" file syntax the program then seeks to evaluate the subsequent xml file. Should it find that the connection string has a hard coded data source
# , the data context of the file will be changed, and uploaded on a separate branch to the gitlab repo. Should no changes be needed, the file will simply skip over
# that file.
###################################################################################################################################################################

import base64
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import gitlab
import json
import logging
from lxml import etree as ET
from pprint import pprint
import re
import tokens
import uuid



token = tokens.personal['token']
current_datetime = str(datetime.now())
rdl_transform_log_id = str(uuid.uuid4())
rdl_log_name = f'rdl_transform_{rdl_transform_log_id}.log'
print(rdl_transform_log_id)
group_id = 4942661
gl = gitlab.Gitlab(private_token=token)
group = gl.groups.get(4942661)
gprojects = group.projects.list(get_all=True)
projects_list = []
commit_actions = []


logging.basicConfig(filename=rdl_log_name, level=logging.INFO)

# Gitlab specific functions
def get_project(p_id):
    project = gl.projects.get(p_id)
    return(project)



def get_project_items(project, p_id, p_path, d_branch):
    items = project.repository_tree(all=True, recursive=True)
#    print(type(items))
#    pprint(items)
    return(items)



def create_new_branch(project, d_branch):
    branch = "rdl_transform"
    try:
        branch_value = project.branches.create({'branch': branch, 'ref': d_branch})
    except:
        logging.info("branch rdl_transform exists, moving on")
        return(branch)
    return(branch_value)



def delete_branch(new_branch):
    try:
        project.branches.delete(new_branch)
    except:
        logging.info("branch does not exist, no need to delete")
    return(0)



def prep_git_commit_actions(parameters_content, fpath, commit_actions): 
    nice_format = parameters_content.prettify()
    #print(nice_format)
    #print(dump)
    action = {
         "action": "update",
         "file_path": fpath,
         "content": nice_format
         #"content": ' '
        }
    commit_actions.append(action)



def create_commit(new_branch, commit_actions, fpath, current_datetime):
    data = {
    'branch': new_branch,
    'commit_message': "Transformed .rdl file "+ fpath + " created by JG, on " + current_datetime,
    'actions': commit_actions
    }
    return(data)

def create_merge_request(project, d_branch, new_branch):
    
   # project.mergerequests.get(mr_iid)
    mr = project.mergerequests.create(
                                      {'source_branch': new_branch,
                                      'target_branch': d_branch,
                                      'title': 'merge_rdl_file_transform'
                                      }
                                      )



def check_for_mrs(project, new_branch):
    mrs = project.mergerequests.list()
    print(f"this is the length of mrs {len(mrs)}")
    for mr in mrs:
        iid = mr.iid
        source_branch = mr.source_branch
        if source_branch == new_branch:
            return(source_branch)
########################### File retrieval and manipulation functions  ###############################################################

def get_rdl_files(items, p_path):
    rdl_items = []
    rdl_files_found = True
    iterator = 0
    for item in items:
        rdl_string = item['path'][-4:]
        if rdl_string == ".rdl":
            rdl_items.append(item)
            iterator += 1
    if iterator > 0:
        print(f"There are {iterator} .rdl files")
    else:
        print(f"There were no .rdl files in {p_path}")
    return(rdl_items)



def get_file_data(project,  file,  d_branch):
    fpath = file['path']
    fid = file['id']
    print(f"branch: {d_branch}, Path: {fpath}, fileId: {fid}")
    try:
        file_info = project.repository_blob(fid)
        content = base64.b64decode(file_info['content'])
        soup = BeautifulSoup(content, 'xml')
    except gitlab.GitlabGetError as err:
         print(err)

    return(soup)



def change_parameters(content):
    soup = content
    tags = soup.find_all('ReportParameter')
    #print(tags)
    for tag in tags:
        value_tag = tag.find('Value')
        #print(f"Found Value {value_tag}")
        if value_tag != None:
            text = value_tag.text
            if "Data Source=" in text :
                tag.clear()
                print("updated Data Source Value Tag")
                data_type_tag = soup.new_tag("DataType")
                data_type_tag.string = "String"
                tag.append(data_type_tag)
                prompt_tag = soup.new_tag("Prompt")
                prompt_tag.string = "ConnectionString"
                tag.append(prompt_tag)
    #print(soup.find_all('ReportParameter'))
    return(soup)



#Review with John and Jeff A.
#def data_source_element(parameters_content):
#    child_string_counter = 0
    #print(content)
#    insert = "<ReportParameter Name=\"ConnectionString\">\n      <DataType>String</DataType>\n      <Prompt>ConnectionString</Prompt>\n"
#    initial_tag = "<ConnectionProperties>"
#    closing_tag = "</ConnectionProperties>"
#    if "Data Source=" in content:
#        before_string = content.split(initial_tag)
#        for tag in closing_tag:
#            after_string = content.split(tag)
#            if len(after_string) > 1:
            #print(f"got values for before_string{len(before_string)}")
            #print(f"got values for after_string{len(after_string)}")
            #print(after_string[0])
#                content = before_string[0] + initial_tag + insert + tag + tag[1]

#    return(content)



num_group_projects = len(gprojects)
print(f"Found {num_group_projects} Projects")
i = 0

# uncomment for all projects metadata
#for one_proj in gprojects:
#    print(one_proj)

while i < num_group_projects:
    id = gprojects[i].id
    name = gprojects[i].name
    path = gprojects[i].path
    default_branch = gprojects[i].default_branch
    items = dict({'id': id,
                  'name': name,
                  'path': path,
                  'default_branch': default_branch})
    projects_list.append(items)
    i += 1




################################################################################       Main         ####################################################################################################################

proj_iterator = 1
retries = 3
retry_count = 0

for p in projects_list:
    print(f"Working on project {proj_iterator}, Company Name: {p['name']}")
    p_id = p['id']
    p_path = p['path']
    d_branch = p['default_branch']

    # Allows the program to get all the pertinent information about the project including the id, branch, name
    project = get_project(p_id)
    new_branch = create_new_branch(project, d_branch)
    proj_iterator += 1

    #We've got the project, but now we need to identify the items that exist within the project
    items = get_project_items(project, p_id, p_path, d_branch)
    rdl_files = get_rdl_files(items, p_path)
    #pprint(rdl_files)

    #Need to check the existence of rdl_files, we look for the ".rdl" file constructs and ignore .rdl.save
    len_rdl_files_list = len(rdl_files)
    for file in rdl_files:
        fpath = file['path']
        content = get_file_data(project, file, d_branch)
        parameters_content = change_parameters(content)
        prep = prep_git_commit_actions(parameters_content, fpath, commit_actions)
        #final_content = data_source_element(parameters_content)

    print("This is the length of commit actions", len(commit_actions))
    if len(commit_actions) > 0:
    #Finalizing Commit Actions
        data = create_commit(new_branch, commit_actions, fpath, current_datetime)
        #print(data)
        commit = project.commits.create(data)
        merge_request_check = check_for_mrs(project, new_branch)
        if merge_request_check != new_branch:
            #Creating Merge Request
            create_merge_request(project, d_branch, new_branch)
    #delete_branch(new_branch)
    commit_actions = []
    #if proj_iterator > 4:
       # exit()
