"""Import reviewed converter tables as data. Uploaded Lua is NEVER executed."""
import hashlib,json,math,re,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from publish import require,data_file,KEY,HEX,lua,verify_merge
LIMITS={2:75,3:100,4:150,5:200,6:250,7:300}
TOKEN=re.compile(r'\s+|--\[\[.*?\]\]|--[^\n]*|[{},;]|true\b|false\b|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?',re.S)
def table(source,name,required=False):
    found=list(re.finditer(r'\blocal\s+'+name+r'\s*=\s*\{',source))
    require(len(found)<=1,'Duplicate '+name+' table')
    if not found:
        require(not required,'Missing local '+name+' table');return []
    position=found[0].end()-1
    def token():
        nonlocal position
        while True:
            match=TOKEN.match(source,position)
            require(match is not None,'Only literal numeric/boolean arrays are allowed in '+name)
            value=match.group();position=match.end()
            if value.isspace()or value.startswith('--'):continue
            return value
    def array(depth=0):
        require(depth<=1,'Nested object fields are not supported')
        result=[];value=token()
        while value!='}':
            if value=='{':result.append(array(depth+1))
            elif value in ('true','false'):result.append(value=='true')
            else:
                require(value not in (',',';','}'),'Malformed table')
                n=float(value);require(math.isfinite(n),'Non-finite map coordinate')
                result.append(int(n)if n.is_integer()else n)
            value=token()
            if value in (',',';'):value=token()
            else:require(value=='}','Missing table separator')
        return result
    require(token()=='{','Malformed table')
    return array()
def number(v,low,high,integer=False):
    return type(v)in(int,float)and math.isfinite(v)and low<=v<=high and(not integer or v%1==0)
def parse_map(content):
    source=content.decode('utf-8-sig')
    objects=table(source,'objects',True);removals=table(source,'removals')
    require(0<len(objects)<=4000 and len(removals)<=512,'Use 1-4000 objects and at most 512 removals')
    for row in objects:
        require(isinstance(row,list)and 7<=len(row)<=15,'Invalid object columns')
        require(number(row[0],1,19999,True),'Invalid object model')
        require(all(number(row[i],-3000,3000)for i in(1,2))and number(row[3],-100,2000),'Invalid object position')
        require(all(number(row[i],-360,360)for i in(4,5,6)),'Invalid object rotation')
        if len(row)>7:require(number(row[7],.05,10),'Invalid scale')
        for i in(8,9,10,14):
            if len(row)>i:require(type(row[i])is bool,'Object flags must be booleans')
        for i,maximum in((11,255),(12,255),(13,65535)):
            if len(row)>i:require(number(row[i],0,maximum,True),'Invalid alpha/world')
    for row in removals:
        require(isinstance(row,list)and len(row)==6,'Invalid removal columns')
        require(number(row[0],1,19999,True)and number(row[1],.01,150),'Removal radius must be at most 150m')
        require(all(number(row[i],-3000,3000)for i in(2,3))and number(row[4],-100,2000)and number(row[5],-1,255,True),'Invalid removal coordinates')
    return dict(objects=objects,removals=removals)
def validate_maps(world):
    root=Path(world)/'bases';result={}
    if not root.exists():return result
    require(root.is_dir()and not root.is_symlink(),'Invalid bases directory')
    for folder in sorted(root.iterdir()):
        if folder.name=='README.md':continue
        # Old documentation-only organization folders are not releases.
        require(folder.is_dir()and not folder.is_symlink()and KEY.fullmatch(folder.name),'Use bases/<immutable-release-key> folders')
        spec=json.loads(data_file(folder,'request.json',{'.json'},16384))
        require(isinstance(spec,dict)and set(spec)=={'organization','github','level','map'},'Invalid base request schema')
        require(isinstance(spec['organization'],str)and re.fullmatch(r"[A-Za-z0-9 _.'-]{1,64}",spec['organization']),'Invalid organization name')
        require(type(spec['level'])is int and spec['level']in LIMITS,'Base level must be 2-7')
        require(isinstance(spec['github'],str)and re.fullmatch(r'https://github\.com/InfinityPR/SAFG-World/pull/[1-9][0-9]*',spec['github']),'Use the SAFG-World submission PR URL')
        content=data_file(folder,spec['map'],{'.lua'},LIMITS[spec['level']]*1024)
        data=parse_map(content)
        metadata={**spec,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}
        fingerprint=hashlib.sha256(json.dumps(metadata,sort_keys=True).encode()).hexdigest()
        result[folder.name]=(metadata,data,content,fingerprint)
    require(len(result)<=256,'Too many base releases')
    return result
def publish_maps(world,resource,verify_github=False):
    resource=Path(resource);statefile=resource/'world-bases.json'
    previous=json.loads(statefile.read_text())if statefile.exists()else {}
    releases=validate_maps(world);require(set(previous)<=set(releases),'Base releases cannot be deleted')
    catalog={};state={};assets={}
    for key,(meta,data,content,fingerprint)in releases.items():
        old=previous.get(key);require(not old or old['fingerprint']==fingerprint,'Base release keys are immutable: '+key)
        if old:commit=old['commit']
        else:
            if verify_github:verify_merge(Path(world),key,meta,{meta['map']:content},'bases')
            commit=subprocess.check_output(['git','-C',str(world),'log','-1','--format=%H','--','bases/'+key],text=True).strip()
        require(HEX.fullmatch(commit),'Commit base source first')
        path='world_bases/'+key+'.json';payload=json.dumps(data,separators=(',',':')).encode()
        catalog[key]={**meta,'path':path,'commit':commit,'dataHash':hashlib.sha256(payload).hexdigest()}
        state[key]={'fingerprint':fingerprint,'commit':commit};assets[path]=payload
    tree=ET.parse(resource/'meta.xml')
    for node in list(tree.getroot().findall('file')):
        if(node.get('src')or'').startswith('world_bases/'):tree.getroot().remove(node)
    for path,content in assets.items():
        destination=resource/path
        require(not destination.is_symlink()and not destination.parent.is_symlink(),'No output symlinks')
        destination.parent.mkdir(exist_ok=True);destination.write_bytes(content)
        ET.SubElement(tree.getroot(),'file',{'src':path,'download':'false'})
    (resource/'world_bases_catalog.lua').write_text('-- Generated reviewed map data only.\nSAFGWorldBases='+lua(catalog)+'\n',encoding='utf-8')
    statefile.write_text(json.dumps(state,sort_keys=True,indent=2)+'\n')
    ET.indent(tree,space=' ');tree.write(resource/'meta.xml',encoding='unicode')
    print('Imported',len(catalog),'reviewed base data releases (no uploaded code executed).')
