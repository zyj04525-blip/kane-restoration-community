"""Local-only paths shared by historical research scripts."""
import os
from pathlib import Path

PROJECT_ROOT=Path(__file__).resolve().parents[2]
WORK_ROOT=Path(os.environ.get('KANE_RESEARCH_WORK_DIR',PROJECT_ROOT/'private-work')).resolve()
INPUT_DIR=Path(os.environ.get('KANE_RESEARCH_INPUT_DIR',PROJECT_ROOT/'private-input')).resolve()

def load_font(size):
 from PIL import ImageFont
 configured=os.environ.get('KANE_QA_FONT')
 for name in [configured,'DejaVuSans.ttf']:
  if not name:continue
  try:return ImageFont.truetype(name,size)
  except OSError:pass
 return ImageFont.load_default()
