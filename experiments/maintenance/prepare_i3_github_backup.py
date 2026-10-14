#!/usr/bin/env python3
"""Package frozen I3 data and repository histories; verify every archived file."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

REPO=Path(__file__).resolve().parents[2]
WS=REPO.parents[1]
BACKUPS=Path('/home/zxr2/下载/CERLAB_I3_Backups')


def digest(stream):
    h=hashlib.sha256()
    for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def sha(path):
    with path.open('rb') as f:return digest(f)


def write(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')


def package(output,name,roots):
    entries=[]
    for root,prefix in roots:
        for p in sorted(root.rglob('*')):
            if p.is_symlink():raise RuntimeError('Unexpected symlink; inspect before archiving: '+str(p))
            if p.is_file():
                stat=p.stat();entries.append({'source':str(p),'name':str(Path(prefix)/p.relative_to(root)),
                                             'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,'sha256':sha(p)})
    target=output/name
    if target.exists():raise RuntimeError('Refuse to overwrite archive '+name)
    with tarfile.open(target,'w:gz',compresslevel=6) as tar:
        for row in entries:
            p=Path(row['source']);stat=p.stat()
            if stat.st_size!=row['bytes'] or stat.st_mtime_ns!=row['mtime_ns']:raise RuntimeError('Source changed before packaging')
            tar.add(p,arcname=row['name'],recursive=False)
        data=(json.dumps({'schema':'cerlab-i3-archive-v1','files':entries},indent=2)+'\n').encode()
        info=tarfile.TarInfo('ARCHIVE_FILE_MANIFEST.json');info.size=len(data);tar.addfile(info,io.BytesIO(data))
    # Verify archive contents, not just the compressed blob.
    with tarfile.open(target,'r:gz') as tar:
        recorded=json.load(tar.extractfile('ARCHIVE_FILE_MANIFEST.json'))['files']
        if len(tar.getmembers())!=len(recorded)+1:raise RuntimeError('Archive member count mismatch')
        for row in recorded:
            member=tar.getmember(row['name'])
            if not member.isfile() or member.size!=row['bytes']:raise RuntimeError('Archive member mismatch')
            if digest(tar.extractfile(member))!=row['sha256']:raise RuntimeError('Archive checksum mismatch')
    for row in entries:
        if sha(Path(row['source']))!=row['sha256']:raise RuntimeError('Source changed after packaging')
    result={'name':name,'file_count':len(entries),'source_bytes':sum(r['bytes'] for r in entries),
            'archive_bytes':target.stat().st_size,'sha256':sha(target),'verified_every_member':True,
            'source_roots':[str(p) for p,_ in roots]}
    print(name,len(entries),'files,',round(target.stat().st_size/2**20,2),'MiB, verified',flush=True)
    return result


def main(output):
    output.mkdir(parents=True,exist_ok=True)
    results=sorted(p for p in (WS/'results').glob('EXP-I3*') if p.is_dir())
    if len(results)!=12:raise RuntimeError('I3 directory inventory changed; inspect')
    dependency=WS/'results/EXP-I2-06-HELD-OUT-SEED4-V1/environment_seed_004/planner_seed_004/20261012T140548'
    # Verify all extant absolute result dependencies are contained in the supplied roots.
    references=set()
    def walk(v):
        if isinstance(v,str) and v.startswith(str(WS/'results')) and Path(v).exists():references.add(Path(v))
        elif isinstance(v,dict):
            for k,x in v.items():walk(k);walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
    for p in list((REPO/'experiments/i3').glob('*.json'))+[p for d in results for p in d.rglob('*.json')]:
        try:walk(json.loads(p.read_text()))
        except ValueError:raise RuntimeError('Invalid source JSON '+str(p))
    if any(not any(p==r or r in p.parents for r in results+[dependency]) for p in references):raise RuntimeError('Uncovered result dependency')
    bundleroot=output/'git_bundles';bundleroot.mkdir(exist_ok=False)
    modules=[line.split()[1] for line in subprocess.check_output(['git','submodule','status'],cwd=REPO,text=True).splitlines()]
    repositories=[('parent',REPO)]+[(name,REPO/name) for name in modules]
    repository_rows=[]
    for name,repo in repositories:
        if subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip():raise RuntimeError('Repository dirty: '+name)
        bundle=bundleroot/(name+'.bundle');subprocess.run(['git','bundle','create',str(bundle),'--all'],cwd=repo,check=True)
        verify=subprocess.run(['git','bundle','verify',str(bundle)],cwd=repo,text=True,capture_output=True,check=True)
        (bundleroot/(name+'_verify.txt')).write_text(verify.stdout+verify.stderr)
        row={'name':name,'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
             'branch':subprocess.check_output(['git','branch','--show-current'],cwd=repo,text=True).strip(),
             'remotes':subprocess.check_output(['git','remote','-v'],cwd=repo,text=True).strip(),'bundle_sha256':sha(bundle)}
        repository_rows.append(row)
    write(bundleroot/'repositories.json',repository_rows)
    tasks=[('I3_raw_results.tar.gz',[(p,str(Path('results')/p.name)) for p in results]),
           ('I3_local_backups.tar.gz',[(BACKUPS,'CERLAB_I3_Backups')]),
           ('I3_frozen_dependencies.tar.gz',[(dependency,str(Path('results')/dependency.relative_to(WS/'results')))]),
           ('I3_git_bundles.tar.gz',[(bundleroot,'git_bundles')])]
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures=[executor.submit(package,output,name,roots) for name,roots in tasks]
        archives=[f.result() for f in futures]
    write(output/'UPLOAD_MANIFEST.json',{'schema':'cerlab-i3-github-backup-v1','date':'2026-10-14',
                                       'repositories':repository_rows,'archives':archives,'all_result_dependencies_covered':True,
                                       'source_result_directories':[str(p) for p in results],
                                       'negative_results_retained':True,'new_experiments':0,'github_upload_complete':False})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);main(p.parse_args().output)
