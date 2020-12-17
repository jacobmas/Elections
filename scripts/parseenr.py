import re
import json
import requests
import argparse
from requests_html import HTMLSession
from os.path import join as path_join
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
            distnum=re.sub(r"[^\d]","",c["C"])
            dist_votes=reduce(lambda x,y:x+y,p["V"][cong_ind],0)
            pres_votes_in_dist=list(map(lambda x:round(x*1.*dist_votes/tot_congress_votes),office_votes)) if tot_congress_votes>0 else list(map(lambda x:0,office_votes))
            precinct_entry={"Precinct":curr_precinct,"District":distnum,"Votes":pres_votes_in_dist}
            ret_precincts.append(precinct_entry)
    return ret_precincts


def parse_enr(filename,sumfilename,office_name,district_name,outfilename):
    top_dir='./data'
    #filename=path_join(top_dir,filename)
    #sumfilename=path_join(top_dir,sumfilename)
    resultfile=json.load(open(filename,'r'))
    precinct_map={}
    electiondata=resultfile["Contests"]
    sumfile=json.load(open(sumfilename,'r'))
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

def scrape_clarity_settings(state,param1,param2):
    initial_url = f"https://results.enr.clarityelections.com/{state}/{param1}/{param2}/json/en/electionsettings.json"
    r=requests.get(initial_url)
    c=r.json()
    county_data={}
    for county in c['settings']['electiondetails']['participatingcounties']:
        d=county.split("|")
        print(d)

#    print(file2)

if __name__ == "__main__":
    import sys

    #https://results.enr.clarityelections.com//GA/Gwinnett/105437/current_ver.txt

    parser = argparse.ArgumentParser(description='Process ENR')
    parser.add_argument('-i', dest='input', help='input file location')
    parser.add_argument('-s',dest='summary',help='summary file location')
    parser.add_argument('-o', dest='output', help='output file location')
    parser.add_argument('-d', dest='district', default='Congress',help='district name')
    parser.add_argument('--office', dest='officename', default='President', help='Office to split')
    args = parser.parse_args()
    parse_enr(args.input,args.summary,args.officename,args.district,args.output)


    #parse_enr("./data/luzernePA2020.json","./data/luzernePA2020summary.json","President","./outdata/luzernePApres2020.csv")

    #https://results.enr.clarityelections.com//GA/107231/273078/json/en/electionsettings.json
    #https://results.enr.clarityelections.com//GA/Atkinson/107234/272788/json/en/electionsettings.json