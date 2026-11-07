"""Replay the existing QA error-path assertions against the new extracted candidate."""
from pathlib import Path

qa = Path(__file__).with_name('qa-audit-r1-new-026-errors-probe.py')
source = qa.read_text(encoding='utf-8')
source = source.replace('C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_independent_026_rerun1', 'C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch/q06_preqa_027_final')
exec(compile(source, str(qa), 'exec'), {'__name__': '__main__'})
