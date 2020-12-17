import re
import argparse
from functools import reduce

# maybe el30?
def parse_line(line,current_state,office,district):
    if re.search(r'OFFICIAL RESULTS',line):
        return '','OFFICIAL'
    if current_state=='OFFICIAL' and not re.match('^[A-Z\s]+$',line):
        return line,'COUNTY'
    if current_state=='COUNTY':
        return line.strip(),'PRECINCT'
    if re.match(r'Vote For [\d]+',line):
        return '','VOTEFOR'
    if current_state=='VOTEFOR' and re.search(office,line):
        return '','OFFICE'
    elif current_state=='VOTEFOR' and re.search(district,line,re.I):
        return re.sub(r'[^\d]','',line),'CONGRESS'
    if (current_state=='OFFICE' or current_state=='CONGRESS') and re.search(r'Contest Totals',line):
        return '','TOTALS'
    if current_state=='OFFICE' and re.search(r'[\d,]+',line):
        office_name=re.sub(r'[\s\d]+$','',line)
        return (office_name,re.sub(',','',re.search(r'[\d][\d,]*',line).group(0))),'OFFICE'
    elif current_state=='CONGRESS' and re.search(r'[\d]+',line):
        office_name=re.sub(r'[\s\d]+$','',line)
        return (office_name,re.sub(',','',re.search(r'[\d][\d,]*',line).group(0))),'CONGRESS'
    return '',current_state

def parseelectionware(filename,outfilename,officenamebegin,districtname='Congress'):
    state='NONE'
    print(filename)
    precinct_map={}
    done_office=False
    office_list=[]
    curr_precinct=''
    curr_district=''
    counter=0
    with open(filename,'r') as f:
        for line in f:
            counter+=1
            #if counter>=1000:
            #    break

            old_precinct=curr_precinct
            line=line.strip()
            line_data,new_state=parse_line(line.strip(),state,officenamebegin,districtname)
            if state=='OFFICE' and new_state=='TOTALS':
                done_office=True
                state = new_state
            if new_state=='CONGRESS' and state=='VOTEFOR':
                curr_district=line_data
                precinct_map[curr_precinct]["districts"][curr_district]=0
                state = new_state
            elif new_state=='CONGRESS' and line_data!='':
                precinct_map[curr_precinct]["districts"][curr_district] += int(line_data[1].strip())
                state = new_state
            if new_state=='PRECINCT' and state!='PRECINCT':
                if line_data!=curr_precinct:
                    state = new_state
                    print(f"curr_precinct={curr_precinct}")

                    curr_precinct=line_data
                    precinct_map[curr_precinct]={officenamebegin:[],"districts":{}}
            if new_state=='OFFICE' and line_data!='':
                if not done_office:
                    office_list.append(line_data[0])

                precinct_map[curr_precinct][officenamebegin].append(line_data[1])
                state = new_state
            print(f'{curr_precinct:40},{new_state:12},{state:12},line={line},line_data={line_data}')
            state=new_state

    with open(outfilename,'w') as f:
        header_line='Precinct,District,'+','.join(office_list)
        f.write(header_line+'\n')

        for precinct in precinct_map:
            #print(precinct_map[precinct])
            data=precinct_map[precinct][officenamebegin]
            dists=precinct_map[precinct]["districts"]
            dist_sum=0
            for dist in dists:
                dist_sum+=dists[dist]
            for dist in dists:
                print(dist)
                data=list(map(lambda x:str(round(int(x)*dists[dist]*1./dist_sum)),data))
                outline=precinct.strip()+','+f'{dist}'+',' +','.join(data)+'\n'
            #print(outline)
                f.write(outline)


if __name__ == "__main__":
    import sys
    parser=argparse.ArgumentParser(description='Process ElectionWare by district type.')
    parser.add_argument('-i',dest='input',help='input file location')
    parser.add_argument('-o',dest='output',help='output file location')
    parser.add_argument('--office',dest='officename',default='President',help='Office to split')
    parser.add_argument('-d',dest='district',default='Congress',help='District to split')
    args=parser.parse_args()
    parseelectionware(filename=args.input,officenamebegin=args.officename,districtname=args.district,
                      outfilename=args.output)