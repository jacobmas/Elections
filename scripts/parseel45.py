import re
from functools import reduce

# maybe el30?
def parse_line(line,current_state,office):
    if re.match(r'[\d]+ ', line):
        #print(f'PRECINCT:{len(line)}:{line}')
        return line,'PRECINCT'
    elif len(line)<2:
        return '','BLANK'
    elif current_state=='BLANK' and re.match(office,line):
        return '','OFFICE'
    elif current_state=='BLANK' and re.search('Congress',line,re.I):
        return re.sub(r'[^\d]','',line),'CONGRESS'
    elif current_state=='OFFICE' and re.match(r'\s[^\s]',line):
        office_name=re.sub(r'\s{0,2}\.(\s\s\.)*','',line[0:43])
        return (office_name,re.sub(r'\,','',line[43:51].strip())),'OFFICE'
    elif current_state=='CONGRESS' and re.match(r'\s[^\s]',line):
        office_name=re.sub(r'\s{0,2}\.(\s\s\.)*','',line[0:43])
        return (office_name,re.sub(r'\,','',line[43:51].strip())),'CONGRESS'
    else:
        return '',current_state

def parseel45(filename,officenamebegin,outfilename):
    state='NONE'
    print(filename)
    precinct_map={}
    done_office=False
    office_list=[]
    curr_precinct=''
    curr_district=''
    with open(filename,'r') as f:
        for line in f:
            old_precinct=curr_precinct
            line_data,new_state=parse_line(line,state,officenamebegin)

            if state=='OFFICE' and new_state=='BLANK':
                done_office=True
                state = new_state
            if new_state=='CONGRESS' and state=='BLANK':
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
            else:
                state=new_state
            #print(f'curr_precinct={curr_precinct},line={line},line_data={line_data},state={state}')
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
    parseel45(sys.argv[1],sys.argv[2],sys.argv[3])