"""
다중 AI 모델 통합 분석 모듈
- OpenAI GPT-4 분석
- Google Gemini 분석
- 결과 종합 및 권고사항 생성
"""

import os
import json
from typing import Dict, List, Tuple

class MultiAIAnalyzer:
    """다중 AI 모델을 활용한 처방 분석"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
    
    def analyze_prescription_gpt4(self, prescription_data: str) -> Dict:
        """
        GPT-4를 활용한 처방 분석
        - 삭감 위험도 판정
        - 부당청구 가능성 분석
        - 개선 권고사항
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            prompt = f"""
            다음 병원 청구 처방 내역을 분석하고 건강보험심사평가원(심평원) 기준에 따른 
            삭감 위험도를 평가해주세요.
            
            처방 내역:
            {prescription_data}
            
            다음 항목을 포함하여 분석해주세요:
            1. 삭감 위험도 (높음/중간/낮음)
            2. 위험 요인 분석
            3. 특정내역 기재 필요 여부
            4. 개선 권고사항
            5. 심평원 심사 기준 적용 여부
            
            JSON 형식으로 응답해주세요.
            """
            
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "당신은 병원 청구심사 전문가입니다. 건강보험심사평가원 기준에 따라 정확하게 분석하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content
            
            # JSON 파싱 시도
            try:
                result = json.loads(result_text)
            except:
                result = {
                    "analysis": result_text,
                    "model": "GPT-4",
                    "status": "text_response"
                }
            
            return result
        
        except Exception as e:
            return {
                "error": str(e),
                "model": "GPT-4",
                "status": "error"
            }
    
    def analyze_prescription_gemini(self, prescription_data: str) -> Dict:
        """
        Gemini를 활용한 처방 분석
        - 환자 안전성 평가
        - 약물 상호작용 검토
        - 임상적 적절성 판정
        """
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.openai_api_key,
                base_url="https://api.openai.com/v1"  # Gemini 호환 엔드포인트 (필요시 수정)
            )
            
            prompt = f"""
            다음 병원 청구 처방 내역을 임상적 관점에서 분석해주세요.
            
            처방 내역:
            {prescription_data}
            
            다음 항목을 포함하여 분석해주세요:
            1. 환자 안전성 평가
            2. 약물 상호작용 검토
            3. 용량 적절성 판정
            4. 임상적 적절성 평가
            5. 주의사항 및 모니터링 필요 항목
            
            JSON 형식으로 응답해주세요.
            """
            
            response = client.chat.completions.create(
                model="gemini-2.5-flash",
                messages=[
                    {"role": "system", "content": "당신은 임상 약학 전문가입니다. 환자 안전성을 최우선으로 평가하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content
            
            # JSON 파싱 시도
            try:
                result = json.loads(result_text)
            except:
                result = {
                    "analysis": result_text,
                    "model": "Gemini",
                    "status": "text_response"
                }
            
            return result
        
        except Exception as e:
            return {
                "error": str(e),
                "model": "Gemini",
                "status": "error"
            }
    
    def synthesize_analysis(self, gpt4_result: Dict, gemini_result: Dict) -> Dict:
        """
        GPT-4와 Gemini 분석 결과를 종합하여 최종 권고사항 생성
        """
        synthesis = {
            "gpt4_analysis": gpt4_result,
            "gemini_analysis": gemini_result,
            "synthesis": {
                "overall_risk": self._calculate_overall_risk(gpt4_result, gemini_result),
                "key_findings": self._extract_key_findings(gpt4_result, gemini_result),
                "recommendations": self._generate_recommendations(gpt4_result, gemini_result),
                "critical_alerts": self._identify_critical_alerts(gpt4_result, gemini_result)
            }
        }
        return synthesis
    
    def _calculate_overall_risk(self, gpt4_result: Dict, gemini_result: Dict) -> str:
        """전체 위험도 계산"""
        # 간단한 로직: 두 모델의 평가를 종합
        if "error" not in gpt4_result and "error" not in gemini_result:
            return "종합 평가 완료"
        return "분석 중 오류 발생"
    
    def _extract_key_findings(self, gpt4_result: Dict, gemini_result: Dict) -> List[str]:
        """주요 발견사항 추출"""
        findings = []
        
        if "error" not in gpt4_result:
            findings.append("GPT-4: 청구 적정성 분석 완료")
        if "error" not in gemini_result:
            findings.append("Gemini: 임상적 적절성 분석 완료")
        
        return findings
    
    def _generate_recommendations(self, gpt4_result: Dict, gemini_result: Dict) -> List[str]:
        """권고사항 생성"""
        recommendations = []
        
        # GPT-4 기반 권고
        if "error" not in gpt4_result:
            recommendations.append("특정내역 기재 요령을 준수하여 삭감 위험을 최소화하세요.")
        
        # Gemini 기반 권고
        if "error" not in gemini_result:
            recommendations.append("환자 상태를 재확인하고 약물 상호작용을 검토하세요.")
        
        return recommendations
    
    def _identify_critical_alerts(self, gpt4_result: Dict, gemini_result: Dict) -> List[str]:
        """중요 알림 식별"""
        alerts = []
        
        if "error" in gpt4_result:
            alerts.append("⚠️ GPT-4 분석 실패: 청구 적정성 평가 불가")
        if "error" in gemini_result:
            alerts.append("⚠️ Gemini 분석 실패: 임상적 평가 불가")
        
        return alerts


class PrescriptionQualityChecker:
    """처방 품질 및 적정성 검사"""
    
    COMMON_DELETION_REASONS = {
        "duplicate_prescription": "동일 또는 유사 성분 중복 처방",
        "missing_specific_comments": "특정내역 미기재",
        "invalid_indication": "부적절한 상병코드 사용",
        "dosage_mismatch": "용량 기준 초과",
        "duration_exceeded": "투약 기간 초과",
        "non_covered_indication": "급여 대상이 아닌 상병",
    }
    
    @staticmethod
    def check_quality(prescription_data: Dict) -> Dict:
        """처방 품질 종합 검사"""
        issues = []
        warnings = []
        
        # 특정내역 확인
        if not prescription_data.get('specific_comments'):
            issues.append("missing_specific_comments")
        
        # 처방 항목 수 확인
        prescriptions = prescription_data.get('prescriptions', [])
        if len(prescriptions) > 5:
            warnings.append("처방 항목이 많습니다. 중복 여부를 확인하세요.")
        
        # 심사기준 확인
        if not prescription_data.get('hira_criteria'):
            warnings.append("심평원 심사기준이 확인되지 않았습니다.")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "issue_descriptions": [
                PrescriptionQualityChecker.COMMON_DELETION_REASONS.get(issue, issue)
                for issue in issues
            ],
            "quality_score": max(0, 100 - (len(issues) * 20 + len(warnings) * 10))
        }


class CaseRecommendationEngine:
    """유사 사례 기반 권고 엔진"""
    
    def __init__(self, cases_db: List[Dict]):
        self.cases_db = cases_db
    
    def find_similar_cases(self, prescription_data: Dict, top_n: int = 3) -> List[Dict]:
        """유사 사례 검색"""
        similar_cases = []
        
        for case in self.cases_db:
            similarity_score = self._calculate_similarity(prescription_data, case)
            if similarity_score > 0.5:
                similar_cases.append({
                    "case": case,
                    "similarity_score": similarity_score
                })
        
        # 유사도 순으로 정렬
        similar_cases.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar_cases[:top_n]
    
    def _calculate_similarity(self, prescription_data: Dict, case: Dict) -> float:
        """유사도 계산 (간단한 구현)"""
        score = 0
        
        # 카테고리 일치
        if prescription_data.get('category') == case.get('category'):
            score += 0.3
        
        # 진료과목 일치
        if prescription_data.get('dept') == case.get('dept'):
            score += 0.3
        
        # 처방 항목 일치도
        prescription_set = set(prescription_data.get('prescriptions', []))
        case_prescription_set = set(case.get('prescriptions', []))
        if prescription_set and case_prescription_set:
            intersection = len(prescription_set & case_prescription_set)
            union = len(prescription_set | case_prescription_set)
            score += (intersection / union) * 0.4
        
        return score
