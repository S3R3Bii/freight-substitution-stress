"""Select attributed public aggregate facts; retain original decimal strings."""
import argparse, csv, gzip, hashlib, io, json, zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

FIELDS=['fr_orig','dms_origst','dms_destst','fr_dest','fr_inmode','dms_mode','fr_outmode','sctg2','trade_type','tons_2022']
def ingest(archive_path, root):
    root=Path(root); config=json.loads((root/'protocol.json').read_text(encoding='utf-8'))
    labels=json.loads((root/'data/labels.json').read_text(encoding='utf-8'))
    allowed=set(config['development_commodities']+config['held_commodities'])
    raw=Path(archive_path).read_bytes(); rows=[]; keys=set(); selected_counts={k:0 for k in sorted(allowed)}; zero=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        member='FAF6.0_State.csv'; member_bytes=z.read(member)
        reader=csv.DictReader(io.StringIO(member_bytes.decode('utf-8-sig'),newline=''))
        assert reader.fieldnames==FIELDS+['value_2022'],reader.fieldnames
        for line,row in enumerate(reader,2):
            if row['trade_type']!='2' or row['fr_inmode']!='3' or row['dms_mode']!='1' or int(row['sctg2']) not in allowed:continue
            assert str(int(row['fr_orig'])) in labels['foreign_origins']
            assert all(str(int(row[f])) in labels['states'] for f in ['dms_origst','dms_destst'])
            amount=Decimal(row['tons_2022']);assert amount.is_finite() and amount>=0
            key=tuple(row[f] for f in FIELDS[:-1]);assert key not in keys,key;keys.add(key)
            original=[row[f] for f in FIELDS]; digest=hashlib.sha256('\x1f'.join(original).encode()).hexdigest()
            rows.append([line,*original,digest]);selected_counts[int(row['sctg2'])]+=1;zero+=amount==0
        source_rows=line-1
    assert all(selected_counts.values()),selected_counts
    buf=io.StringIO(newline='');writer=csv.writer(buf,lineterminator='\n');writer.writerow(['source_row',*FIELDS,'source_fields_sha256']);writer.writerows(rows)
    data=buf.getvalue().encode();packed=gzip.compress(data,mtime=0)
    out=root/'data/source';out.mkdir(parents=True,exist_ok=True);(out/'flows.csv.gz').write_bytes(packed)
    manifest=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),source_url=config['source_url'],source_version=config['source_version'],year=2022,units=config['units'],archive_bytes=len(raw),archive_sha256=hashlib.sha256(raw).hexdigest(),member=member,member_sha256=hashlib.sha256(member_bytes).hexdigest(),source_rows=source_rows,selected_rows=len(rows),selected_zero_rows=zero,selected_rows_by_commodity=selected_counts,selected_sha256=hashlib.sha256(packed).hexdigest(),projection='Header source_row uses physical CSV record position with header=1; all source dimensions and original tons string, excluding monetary value; SHA256 joins ten source fields by U+001F. Original archive and workbook excluded.')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('--root',default='.');a=p.parse_args();ingest(a.archive,a.root)
