"""Read the actual XML numeric token, not a rounded intermediary binary float."""
from decimal import Decimal
import zipfile
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.parsers import parse_attachment

CAT=Catalog()

def test_excel_decimal_lexeme_survives_without_binary_float_roundtrip(tmp_path):
 from openpyxl import Workbook
 path=tmp_path/'SYNTHETIC.xlsx';w=Workbook();w.active.append(['site.total_area (m2)']);w.active.append([1]);w.save(path);w.close()
 with zipfile.ZipFile(path) as z:entries=[(i.filename,z.read(i)) for i in z.infolist()]
 with zipfile.ZipFile(path,'w') as z:
  for name,data in entries:
   if name=='xl/worksheets/sheet1.xml':data=data.replace(b'<v>1</v>',b'<v>1.000000000000000001</v>')
   z.writestr(name,data)
 result=parse_attachment(path,tmp_path,catalog=CAT,work_root=tmp_path/'work')
 assert result['status']=='PARSED',result
 assert result['candidates'][0]['value']==Decimal('1.000000000000000001')
 assert result['candidates'][0]['original_value']==Decimal('1.000000000000000001')

def test_signed_csv_literal_is_not_executable_formula(tmp_path):
 path=tmp_path/'SYNTHETIC.csv';path.write_text('site.latitude (degree)\n-25.2\n',encoding='utf8')
 result=parse_attachment(path,tmp_path,catalog=CAT,work_root=tmp_path/'work')
 assert result['status']=='PARSED',result
 assert result['candidates'][0]['value']==Decimal('-25.2')
