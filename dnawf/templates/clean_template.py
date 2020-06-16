#!/usr/bin/env python
# -*- coding: utf-

import json
from argparse import ArgumentParser
import glob
import os
import pprint

def clean_template(template):
    pprint.pprint(t)
    
#     template.pop('id')
    template.pop('createTime')
    template.pop('lastUpdateTime')
    template.pop('parentTemplateId')
    template.pop("projectId")
    template.pop("projectName")
    # need to clean vars.
    for var in template['templateParams']:
        var.pop('id')
    return template


def remove_dict_key(key, var):
    if hasattr(var, 'iteritems'):
        if key in var.keys():
            var.pop(key)
        
        for k, v in var.iteritems():
            if isinstance(v, dict):
                for result in remove_dict_key(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in remove_dict_key(key, d):
                        yield result

def saveTemplate(template, orig_filename):
    dir_name = os.path.dirname(orig_filename)
    filename_extension = os.path.basename(orig_filename)
    (basename, extension) = os.path.splitext(filename_extension)
    
    out_f = open(dir_name + "/" + basename + "_clean" + extension, "a")
    out_f.write(json.dumps(template, indent=4, sort_keys=True))
    
    out_f.close()

def printTemplateContent(template):
    print(100 * "#")
    pprint.pprint(template)
    print(100 * "#")

def removePreviousVersion(dir_name):
    file_list = glob.glob(dir_name + "/*clean*")
    
 
    # Iterate over the list of filepaths & remove each file.
    for filePath in file_list:
        try:
            print("Deleting file : ", filePath)
            os.remove(filePath)
        except:
            print("Error while deleting file : ", filePath)
    
        
if __name__ == "__main__":
    parser = ArgumentParser(description='Select options.')
    parser.add_argument('dir', help="directory where input json files are ")
    args = parser.parse_args()
    
    removePreviousVersion(args.dir)
    
    for file_name in glob.glob(args.dir + "/*.json"):
        print(file_name)
        with open(file_name) as f:
            template = json.load(f)
            c_template = clean_template(template)
            
            printTemplateContent(c_template)
            saveTemplate(c_template, file_name)
    