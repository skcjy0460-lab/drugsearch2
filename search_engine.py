"""
고급 검색 및 필터링 엔진
- 약품명, 처방코드, 시술명 통합 검색
- 진료과목별 필터링
- 심사 기준 및 특정내역 검색
"""

import json
import re
from typing import List, Dict

class PrescriptionSearchEngine:
    def __init__(self, data: List[Dict]):
        self.data = data
    
    def search_by_keyword(self, keyword: str, field: str = None) -> List[Dict]:
        """
        키워드 기반 검색
        field: 'code', 'name', 'category', 'dept', 'all' (기본값)
        """
        if not keyword:
            return []
        
        keyword_lower = keyword.lower()
        results = []
        
        for item in self.data:
            if field == 'code':
                if keyword in item.get('code', ''):
                    results.append(item)
            elif field == 'name':
                if keyword_lower in item.get('name', '').lower():
                    results.append(item)
            elif field == 'category':
                if keyword_lower in item.get('category', '').lower():
                    results.append(item)
            elif field == 'dept':
                if keyword_lower in item.get('dept', '').lower():
                    results.append(item)
            else:  # 'all' - 전체 필드 검색
                if (keyword in item.get('code', '') or
                    keyword_lower in item.get('name', '').lower() or
                    keyword_lower in item.get('category', '').lower()):
                    results.append(item)
        
        return results
    
    def filter_by_dept(self, dept: str) -> List[Dict]:
        """진료과목별 필터링"""
        if dept == "전체":
            return self.data
        return [item for item in self.data if item.get('dept') == dept]
    
    def search_with_filters(self, keyword: str, dept: str = "전체") -> List[Dict]:
        """키워드 + 진료과목 복합 검색"""
        keyword_results = self.search_by_keyword(keyword)
        if dept == "전체":
            return keyword_results
        return [item for item in keyword_results if item.get('dept') == dept]
    
    def search_specific_comments(self, keyword: str) -> List[Dict]:
        """특정내역 기재 요령 검색"""
        keyword_lower = keyword.lower()
        results = []
        for item in self.data:
            if keyword_lower in item.get('specific_comments', '').lower():
                results.append(item)
        return results
    
    def search_hira_criteria(self, keyword: str) -> List[Dict]:
        """심평원 심사기준 검색"""
        keyword_lower = keyword.lower()
        results = []
        for item in self.data:
            if keyword_lower in item.get('hira_criteria', '').lower():
                results.append(item)
        return results
    
    def get_related_items(self, category: str) -> List[Dict]:
        """같은 카테고리의 관련 항목 조회"""
        return [item for item in self.data if item.get('category') == category]
    
    def get_dept_categories(self, dept: str) -> List[str]:
        """진료과목별 카테고리 목록"""
        categories = set()
        for item in self.data:
            if item.get('dept') == dept:
                categories.add(item.get('category', ''))
        return sorted(list(categories))
    
    def get_all_depts(self) -> List[str]:
        """모든 진료과목 목록"""
        depts = set()
        for item in self.data:
            depts.add(item.get('dept', ''))
        return sorted(list(depts))
    
    def get_all_categories(self) -> List[str]:
        """모든 카테고리 목록"""
        categories = set()
        for item in self.data:
            categories.add(item.get('category', ''))
        return sorted(list(categories))


class SpecificCommentAnalyzer:
    """특정내역 구분코드 분석 및 알림"""
    
    SPECIFIC_CODES = {
        'MS001': {'name': '원내투약일수 (경구/외용)', 'format': '9(3)', 'description': '의약분업 예외사항 발생 시 기재'},
        'MS002': {'name': '원내투약일수 (주사제)', 'format': '9(3)', 'description': '주사제 원내 조제/투약 시 기재'},
        'MS003': {'name': '의약분업 예외구분코드', 'format': 'X', 'description': '의약분업 예외사항 구분'},
        'MT001': {'name': '상해외인', 'format': 'X', 'description': '상해 외인 관련 기재'},
        'MT002': {'name': '질병분류', 'format': 'X(5)', 'description': '질병코드 기재'},
        'AL010': {'name': '입원료', 'format': '9(3)', 'description': '입원 관련 기재'},
        'AL300': {'name': '외래환자의약품관리료', 'format': '9(3)', 'description': '외래 약품 관리료'},
    }
    
    @staticmethod
    def get_code_info(code: str) -> Dict:
        """특정내역 코드 정보 조회"""
        return SpecificCommentAnalyzer.SPECIFIC_CODES.get(code, None)
    
    @staticmethod
    def analyze_prescription(prescription_data: Dict) -> List[Dict]:
        """처방 데이터에서 필요한 특정내역 코드 분석"""
        required_codes = []
        
        # 처방 내용 분석
        prescriptions = prescription_data.get('prescriptions', [])
        for p in prescriptions:
            if '원내투약' in p or '경구' in p:
                required_codes.append('MS001')
            if '주사' in p:
                required_codes.append('MS002')
            if '외래' in p or '관리료' in p:
                required_codes.append('AL300')
        
        # 중복 제거
        required_codes = list(set(required_codes))
        
        return [
            {
                'code': code,
                'info': SpecificCommentAnalyzer.get_code_info(code),
                'alert': f"⚠️ 이 처방에는 특정내역 [{code}] 기재가 필요합니다."
            }
            for code in required_codes
        ]


class DeletionRiskAnalyzer:
    """삭감 위험도 분석"""
    
    @staticmethod
    def analyze_risk(prescription_data: Dict) -> Dict:
        """처방의 삭감 위험도 분석"""
        risk_score = 0
        risk_factors = []
        
        # 특정내역 미기재 확인
        if not prescription_data.get('specific_comments'):
            risk_score += 30
            risk_factors.append("특정내역 기재 요령 부재")
        
        # 심사기준 확인
        if not prescription_data.get('hira_criteria'):
            risk_score += 20
            risk_factors.append("심평원 심사기준 미확인")
        
        # 중복 처방 가능성
        prescriptions = prescription_data.get('prescriptions', [])
        if len(prescriptions) > 3:
            risk_score += 15
            risk_factors.append("처방 항목 다수 (중복 가능성)")
        
        # 위험도 판정
        if risk_score >= 70:
            risk_level = "높음"
            color = "red"
        elif risk_score >= 40:
            risk_level = "중간"
            color = "orange"
        else:
            risk_level = "낮음"
            color = "green"
        
        return {
            'score': risk_score,
            'level': risk_level,
            'color': color,
            'factors': risk_factors
        }
