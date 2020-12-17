import re
import json
import os
from os.path import dirname
import requests
import argparse
from requests_html import HTMLSession
from os.path import join as path_join
from functools import reduce

# parses enr.clarityelections.com json




def parse_arcgis(infilename,distpostfix,officename,outfilename):
    infileprefix=re.sub(r'\.[^\.]*$','',infilename)
    pathsplit=os.path.split(infileprefix)
    print(f"infileprefix={infileprefix}")
    precinct_dict={}
    distlist=[f for f in os.listdir(pathsplit[0]) if (pathsplit[1]+distpostfix) in f]

    officedata=json.load(open(infilename,"r"))['features']
    distdata_lst=[json.load(open(os.path.join(pathsplit[0],f),"r"))['features'] for f in distlist]
    for o in officedata:
        a=o['attributes']
        if a['Precinct_name'] not in precinct_dict:
            #print(a['Precinct_name'])
            precinct_dict[a['Precinct_name']]={officename:{},"district":{}}

        #print("at else?")
        precinct_dict[a['Precinct_name']][officename][a['candidate_name']]=a['Votes']
    for dist in distdata_lst:
        for d in dist:
            a=d['attributes']
            distnum=re.sub(r'[^\d]','',a['Contest_title'])
            if distnum not in precinct_dict[a['Precinct_name']]['district']:
                precinct_dict[a['Precinct_name']]['district'][distnum]={'DistrictBallots':a['Ballots']}
    done_office_list=False
    office_list=[]
    result_list=[]
    for pname in precinct_dict:
        p=precinct_dict[pname]
        print(f"p={p}")
        total_ballots=0
        for d in p['district']:
            total_ballots+=p['district'][d]['DistrictBallots']
        if not done_office_list:
            office_list=p[officename].keys()
            done_office_list=True
        for d in p['district']:
            to_append = {'Precinct':pname,'District':d}
            for o in p[officename].keys():
                to_append[o]=round(1.*p[officename][o]*p['district'][d]['DistrictBallots']/total_ballots)
            result_list.append(to_append)




#    print(file2)

    with open(outfilename,'w') as f:
        header_line='Precinct,District,'+','.join(office_list)
        f.write(header_line+'\n')
        for p in result_list:
            #print(f"p={p}")
            result_str=''
            temp_list=[]
            for o in office_list:
                temp_list.append(p[o])
            outline=f"{p['Precinct']},{p['District']},{','.join(map(lambda x:str(x),temp_list))}\n"
            #print(outline)
            f.write(outline)

if __name__ == "__main__":
    import sys

    parser = argparse.ArgumentParser(description='Process ENR')
    parser.add_argument('-i', dest='input', help='input file name')
    parser.add_argument('-d',dest='districtpostfix',default='CD',help='District append to prefix')
    parser.add_argument('-o', dest='output', help='output file location')
    parser.add_argument('--office', dest='officename', default='President', help='Office to split')
    args = parser.parse_args()
    parse_arcgis(args.input,args.districtpostfix,args.officename,args.output)


    #parse_enr("./data/luzernePA2020.json","./data/luzernePA2020summary.json","President","./outdata/luzernePApres2020.csv")

    #https://results.enr.clarityelections.com//GA/107231/273078/json/en/electionsettings.json
    #https://results.enr.clarityelections.com//GA/Atkinson/107234/272788/json/en/electionsettings.json