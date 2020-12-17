import re
import json
import requests
import argparse
from requests_html import HTMLSession
from os.path import join as path_join
from urllib.parse import urlparse
from functools import reduce

# parses enr.clarityelections.com json

def parse_precinct(precinct,office_list,office_key,congress_data):
    p=precinct
    curr_precinct = p["A"]
    office_ind=p["C"].index(office_key) # should always exist
    office_votes=p["V"][office_ind] # the votes for the office
    ret_precincts=[]
    tot_districts=0
    tot_congress_votes=0
    # first sum through the house votes
    for c in congress_data:
        if c["K"] in p["C"]:
            cong_ind=p["C"].index(c["K"]) #
            tot_districts+=1
            tot_congress_votes=tot_congress_votes+reduce(lambda x,y:x+y,p["V"][cong_ind],0)
    for c in congress_data:
        print(f"c={c},p={p}")
        if c["K"] in p["C"]:
            cong_ind=p["C"].index(c["K"]) #
            distnum=c["C"]#re.sub(r"[^\d]","",c["C"])
            dist_votes=reduce(lambda x,y:x+y,p["V"][cong_ind],0)
            pres_votes_in_dist=list(map(lambda x:round(x*1.*dist_votes/tot_congress_votes),office_votes)) if tot_congress_votes>0 else list(map(lambda x:0,office_votes))
            precinct_entry={"Precinct":curr_precinct,"District":distnum,"Votes":pres_votes_in_dist}
            ret_precincts.append(precinct_entry)
    return ret_precincts


def parse_enr(resultfile,sumfile,office_name,district_name,outfilename,allocate_precincts):
    top_dir='./data'
    #filename=path_join(top_dir,filename)
    #sumfilename=path_join(top_dir,sumfilename)
    #resultfile=json.load(open(filename,'r'))
    precinct_map={}
    electiondata=resultfile["Contests"]
    #sumfile=json.load(open(sumfilename,'r'))
    contests=[x["C"] for x in sumfile]
    #print(contests)
    office_data=list(filter(lambda x:office_name in x["C"],sumfile))[0]
    office_list=office_data["CH"]
    office_key=office_data["K"]
    nonse=lambda x:re.search(district_name,x["C"],re.I) is not None
    congress_data=list(filter(nonse,sumfile))

    print(congress_data)
    #print(contests)
    precinct_list=[]
    counter=0
    for p in electiondata:
        counter+=1
        #if counter>=100:
        #    return
        if p["A"]!="-1":
            result=parse_precinct(p,office_list,office_key,congress_data)
            #print(result)
            precinct_list.extend(result)

    with open(outfilename,'w') as f:
        header_line='Precinct,District,'+','.join(office_list)
        f.write(header_line+'\n')
        for p in precinct_list:
            outline=f"{p['Precinct']},{p['District']},{','.join(map(lambda x:str(x),p['Votes']))}\n"
            #print(outline)
            f.write(outline)


def get_version(state,county,param1):
    version_url=f"https://results.enr.clarityelections.com/{state}/{county}/{param1}/current_ver.txt"
    r=requests.get(version_url)
#    print(r.text)
    return r.text

def get_json(state,county,param1,param2,suffix):
    json_url=f"https://results.enr.clarityelections.com/{state}/{county}/{param1}/{param2}/{suffix}"
    r=requests.get(json_url)
    return r.json()
def parse_enr_full(url,officename,district,outputfile,allocate_precincts):
    parsed_url=urlparse(url)
    url_parts=list(filter(lambda x:x!='',parsed_url.path.split('/')))
    state=url_parts[0]
    county=url_parts[1]
    param1=url_parts[2]
    param2=get_version(state,county,param1)
    all_json=get_json(state,county,param1,param2,"json/ALL.json")
    summary_json=get_json(state,county,param1,param2,"json/en/summary.json")
    parse_enr(all_json, summary_json, officename, district, outputfile,allocate_precincts)
    #print(all_json)
    #print(summary_json)

if __name__ == "__main__":
    import sys

    #https://results.enr.clarityelections.com//GA/Gwinnett/105437/current_ver.txt

    parser = argparse.ArgumentParser(description='Get ENR precinct data given the summary page url')
    parser.add_argument('-u', dest='url', help='summary page url')
    parser.add_argument('-o', dest='output', help='output CSV file location',default="temp.csv")
    parser.add_argument('-a',dest='allocate_precincts',action='store_true',
                        help='Automatically allocate precincts (right now it only automatically allocates split precincts so this is not functional)')
    parser.add_argument('-d', dest='district', default='Congress',help='part of district level office name '+
    'to use for RegExp (i.e. \"US Representative\", \"Congress\", \"United States Representative\",'+
    +'\"State Assembly\". Make sure it\'s a part common to all such districts and ONLY to such districts '+
                                                                       'based on what is displayed on the summary website'")
    parser.add_argument('--office', dest='officename', default='President',
                        help='Part of the office name to compile precinct data for (e.g. President of the United States).'+
                             'Make sure it is sufficient to identify that office alone via RegExp')
    args = parser.parse_args()
    parse_enr_full(args.url,args.officename,args.district,args.output,args.allocate_precincts)


    #parse_enr("./data/luzernePA2020.json","./data/luzernePA2020summary.json","President","./outdata/luzernePApres2020.csv")

    #https://results.enr.clarityelections.com//GA/107231/273078/json/en/electionsettings.json
    #https://results.enr.clarityelections.com//GA/Atkinson/107234/272788/json/en/electionsettings.json