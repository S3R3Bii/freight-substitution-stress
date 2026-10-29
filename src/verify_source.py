"""Independent positional parsing, exact SQL grouping and source-locator checks."""
import argparse,csv,gzip,hashlib,io,json,sqlite3,zipfile
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

class ExactSum:
    def __init__(self):self.value=Fraction(0)
    def step(self,value):self.value+=Fraction(value)
    def finalize(self):return str(self.value)

def verify(root='.',archive=None):
    root=Path(root);m=json.loads((root/'data/source/manifest.json').read_text(encoding='utf-8'))
    cfg=json.loads((root/'protocol.json').read_text(encoding='utf-8'));labels=json.loads((root/'data/labels.json').read_text(encoding='utf-8'))
    raw=(root/'data/source/flows.csv.gz').read_bytes();assert hashlib.sha256(raw).hexdigest()==m['selected_sha256']
    rows=list(csv.reader(io.StringIO(gzip.decompress(raw).decode(),newline='')))
    assert rows.pop(0)==['source_row','fr_orig','dms_origst','dms_destst','fr_dest','fr_inmode','dms_mode','fr_outmode','sctg2','trade_type','tons_2022','source_fields_sha256']
    con=sqlite3.connect(':memory:');con.create_aggregate('exact_sum',1,ExactSum)
    con.execute('CREATE TABLE facts (k INTEGER,o INTEGER,g INTEGER,d INTEGER,tons TEXT,locator INTEGER UNIQUE)')
    allowed=set(cfg['development_commodities']+cfg['held_commodities']);keys=set();counts={k:0 for k in allowed};checks=0
    for row in rows:
        line,*fields,digest=row;assert hashlib.sha256('\x1f'.join(fields).encode()).hexdigest()==digest;checks+=1
        o,g,d,fd,im,dm,om,k,trade,t=fields
        assert (int(im),int(dm),int(trade))==(3,1,2) and int(k) in allowed;checks+=4
        assert o in labels['foreign_origins'] and str(int(g)) in labels['states'] and str(int(d)) in labels['states'];checks+=3
        q=Decimal(t);assert q.is_finite() and q>=0;checks+=1
        key=tuple(fields[:9]);assert key not in keys;keys.add(key);checks+=1
        con.execute('INSERT INTO facts VALUES (?,?,?,?,?,?)',(int(k),int(o),int(g),int(d),t,int(line)));counts[int(k)]+=1
    assert len(rows)==m['selected_rows'] and counts=={int(k):v for k,v in m['selected_rows_by_commodity'].items()};checks+=2
    con.commit();cells=con.execute('SELECT k,o,g,d,exact_sum(tons),COUNT(*) FROM facts GROUP BY k,o,g,d ORDER BY k,o,g,d').fetchall()
    duplicate_aggregates=sum(n>1 for *rest,n in cells)
    raw_checks=0
    if archive:
        original=Path(archive).read_bytes();assert hashlib.sha256(original).hexdigest()==m['archive_sha256']
        with zipfile.ZipFile(io.BytesIO(original)) as z:member=z.read(m['member'])
        assert hashlib.sha256(member).hexdigest()==m['member_sha256']
        parsed=csv.reader(io.StringIO(member.decode('utf-8-sig'),newline=''));header=next(parsed)
        indices=[header.index(n) for n in ['fr_orig','dms_origst','dms_destst','fr_dest','fr_inmode','dms_mode','fr_outmode','sctg2','trade_type','tons_2022']]
        expected=[]
        for line,values in enumerate(parsed,2):
            if values[header.index('trade_type')]=='2' and values[header.index('fr_inmode')]=='3' and values[header.index('dms_mode')]=='1' and int(values[header.index('sctg2')]) in allowed:
                fields=[values[i] for i in indices];expected.append([str(line),*fields,hashlib.sha256('\x1f'.join(fields).encode()).hexdigest()])
        assert line-1==m['source_rows'] and expected==rows;raw_checks=len(rows)*12
    payload=dict(status='PASS',selected_rows=len(rows),aggregate_cells=len(cells),duplicate_aggregate_cells=duplicate_aggregates,projection_checks=checks,raw_field_checks=raw_checks,raw_archive='PASS' if archive else 'Not re-downloaded in replay; original-to-projection evidence retained separately',units=m['units'])
    return payload,cells
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--archive');p.add_argument('--output');a=p.parse_args();result,_=verify(a.root,a.archive)
    if a.output:Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))
