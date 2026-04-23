# app/utils/helpers.py
import pandas as pd
from typing import Optional

def parse_season(s) -> Optional[int]:
    """تحويل اسم الموسم لرقم سنة"""
    try:
        s = str(s)
        if '/' in s:
            part = s.split('/')[0]
            return int(part) + 2000 if len(part) == 2 else int(part)
        elif '-' in s:
            return int(s.split('-')[0])
        else:
            return int(s)
    except:
        return None

def injury_type(reason: str) -> str:
    """تصنيف نوع الإصابة"""
    if pd.isna(reason): 
        return 'unknown'
    r = reason.lower()
    if any(x in r for x in ['muscle','muscular','hamstring','thigh','calf']): 
        return 'muscle'
    elif any(x in r for x in ['knee','ligament','acl','meniscus']):           
        return 'knee'
    elif any(x in r for x in ['ankle','foot','toe']):                         
        return 'ankle'
    elif any(x in r for x in ['back','spine']):                               
        return 'back'
    elif any(x in r for x in ['ill','sick','covid','virus']):                 
        return 'illness'
    else:                                                                      
        return 'other'

def age_phase_func(age: int) -> int:
    """تقسيم العمر لمراحل"""
    if age < 23:   return 0
    elif age < 27: return 1
    elif age < 30: return 2
    elif age < 33: return 3
    else:          return 4

def final_risk(prob: float, last1_days: int, last1_injuries: int, 
               career_days: int, career_injuries: int) -> tuple:
    """حساب مستوى خطر الإصابة النهائي"""
    pct = round(prob * 100, 1)
    if last1_days >= 60:
        return '🔴 High Risk', max(pct, 72.0)
    if last1_injuries >= 3:
        return '🔴 High Risk', max(pct, 68.0)
    if last1_days >= 30 and career_injuries >= 10:
        return '🔴 High Risk', max(pct, 66.0)
    if career_days >= 250 and last1_days >= 20:
        return '🟡 Medium Risk', max(pct, 52.0)
    if last1_injuries >= 2 and career_days >= 150:
        return '🟡 Medium Risk', max(pct, 48.0)
    if prob >= 0.65:   return '🔴 High Risk',   pct
    elif prob >= 0.40: return '🟡 Medium Risk',  pct
    else:              return '🟢 Low Risk',     pct