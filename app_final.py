import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
from search_engine import PrescriptionSearchEngine, SpecificCommentAnalyzer, DeletionRiskAnalyzer
from ai_analyzer import MultiAIAnalyzer, PrescriptionQualityChecker, CaseRecommendationEngine

DATA_FILE = 'sample_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 페이지 설정
st.set_page_config(
    page_title="병원 청구심사 전문가 시스템",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# 스타일 설정
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stAlert {
        border-radius: 10px;
    }
    .report-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .ai-diagnostic {
        background-color: #f0f8ff;
        padding: 15px;
        border-radius: 8px;
        border: 1px dashed #007bff;
    }
    .warning-card {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #ffc107;
    }
    .quality-score {
        font-size: 24px;
        font-weight: bold;
        padding: 10px;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# 사이드바 내비게이션
def sidebar():
    with st.sidebar:
        st.title("🏥 청구심사 솔루션")
        st.info("전문적인 병원 경영 컨설팅을 위한 청구 가이드 시스템")
        
        if not st.session_state.logged_in:
            st.subheader("로그인")
            user_id = st.text_input("아이디")
            password = st.text_input("비밀번호", type="password")
            if st.button("로그인"):
                if user_id == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.session_state.user_role = "admin"
                    st.rerun()
                elif user_id == "user" and password == "user123":
                    st.session_state.logged_in = True
                    st.session_state.user_role = "user"
                    st.rerun()
                else:
                    st.error("잘못된 정보입니다.")
        else:
            st.success(f"{st.session_state.user_role}님 환영합니다.")
            if st.button("로그아웃"):
                st.session_state.logged_in = False
                st.rerun()
            
            st.divider()
            menu = st.radio(
                "메뉴 선택",
                ["처방 가이드 검색", "심사 사례 라이브러리", "AI 진단 및 분석", "관리자 설정"]
            )
            return menu

def main():
    menu = sidebar()
    
    if not st.session_state.logged_in:
        st.warning("서비스 이용을 위해 로그인이 필요합니다.")
        st.info("테스트 계정: admin / admin123 또는 user / user123")
        return

    if menu == "처방 가이드 검색":
        st.header("🔍 처방 가이드 및 심사기준 검색")
        
        data = load_data()
        search_engine = PrescriptionSearchEngine(data)
        
        # 검색 옵션
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_query = st.text_input("약품명, 처방코드 또는 시술명을 입력하세요.", placeholder="예: 씨엠쿨산, 케이캡, 648602750")
        with col2:
            search_field = st.selectbox("검색 범위", ["전체", "약품명", "처방코드", "카테고리"])
        with col3:
            dept = st.selectbox("진료과목", ["전체"] + search_engine.get_all_depts())
        
        # 고급 검색 옵션
        with st.expander("🔎 고급 검색 옵션"):
            search_type = st.radio("검색 유형", ["일반 검색", "특정내역 검색", "심사기준 검색"])
        
        if search_query:
            # 검색 필드 매핑
            field_map = {"전체": "all", "약품명": "name", "처방코드": "code", "카테고리": "category"}
            field = field_map.get(search_field, "all")
            
            # 검색 유형별 처리
            if search_type == "특정내역 검색":
                results = search_engine.search_specific_comments(search_query)
            elif search_type == "심사기준 검색":
                results = search_engine.search_hira_criteria(search_query)
            else:
                results = search_engine.search_with_filters(search_query, dept)
            
            if results:
                st.info(f"검색 결과: {len(results)}개")
                
                for idx, res in enumerate(results):
                    # 품질 검사
                    quality_check = PrescriptionQualityChecker.check_quality(res)
                    
                    # 삭감 위험도 분석
                    risk_analysis = DeletionRiskAnalyzer.analyze_risk(res)
                    
                    st.markdown(f"""
                    <div class="report-card">
                        <h2 style='color: #007bff;'>[{res['code']}] {res['name']}</h2>
                        <p><b>진료과목:</b> {res['dept']} | <b>분류:</b> {res['category']}</p>
                        <hr>
                        <h4>✅ 권장 처방 리스트</h4>
                        <ul>
                            {"".join([f"<li>{p}</li>" for p in res['prescriptions']])}
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 품질 점수 표시
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.subheader("📊 처방 품질 평가")
                    with col2:
                        score = quality_check['quality_score']
                        if score >= 80:
                            st.markdown(f"<div class='quality-score' style='background-color: #d4edda; color: #155724;'>{score}점</div>", unsafe_allow_html=True)
                        elif score >= 50:
                            st.markdown(f"<div class='quality-score' style='background-color: #fff3cd; color: #856404;'>{score}점</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='quality-score' style='background-color: #f8d7da; color: #721c24;'>{score}점</div>", unsafe_allow_html=True)
                    
                    if quality_check['issue_descriptions']:
                        st.write("**주의 항목:**")
                        for issue in quality_check['issue_descriptions']:
                            st.write(f"- ⚠️ {issue}")
                    
                    # 삭감 위험도 표시
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader("⚠️ 삭감 위험도 분석")
                    with col2:
                        if risk_analysis['level'] == '높음':
                            st.error(f"위험도: {risk_analysis['level']} ({risk_analysis['score']}점)")
                        elif risk_analysis['level'] == '중간':
                            st.warning(f"위험도: {risk_analysis['level']} ({risk_analysis['score']}점)")
                        else:
                            st.success(f"위험도: {risk_analysis['level']} ({risk_analysis['score']}점)")
                    
                    if risk_analysis['factors']:
                        st.write("**주요 위험 요인:**")
                        for factor in risk_analysis['factors']:
                            st.write(f"- {factor}")
                    
                    st.subheader("📋 심평원 심사기준 (HIRA Criteria)")
                    st.info(res['hira_criteria'])
                    
                    st.subheader("🔔 특정내역 입력 알림 (Specific Comments)")
                    st.warning(res['specific_comments'])
                    
                    # 필요한 특정내역 코드 분석
                    specific_codes = SpecificCommentAnalyzer.analyze_prescription(res)
                    if specific_codes:
                        st.subheader("📌 필수 특정내역 코드")
                        for code_info in specific_codes:
                            with st.expander(f"[{code_info['code']}] {code_info['info']['name']}"):
                                st.write(f"**형식:** {code_info['info']['format']}")
                                st.write(f"**설명:** {code_info['info']['description']}")
                                st.warning(code_info['alert'])
                    
                    st.subheader("🤖 AI 진단 및 주의사항")
                    st.markdown(f"""
                    <div class="ai-diagnostic">
                        <b>[Multi-AI 종합 분석 결과]</b><br>
                        {res['ai_diagnosis']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.subheader("📝 관련 심사/삭감 사례")
                    for case in res['cases']:
                        st.write(f"- {case}")
                    st.divider()
            else:
                st.error("검색 결과가 없습니다. 다른 검색어를 시도하거나 관리자에게 데이터 추가를 요청하세요.")

    elif menu == "심사 사례 라이브러리":
        st.header("📚 심사 및 삭감 사례 검색")
        case_search = st.text_input("사례 키워드 검색", placeholder="예: 중복처방, 삭감, 이의신청")
        
        # 샘플 사례 데이터
        cases_db = [
            {"title": "대장내시경 전처치용 세장제 삭감 사례", "content": "단순 검진 목적 청구로 인한 삭감. 특정내역 MT001 미기재.", "tag": "내과", "resolution": "진료기록부에 '혈변' 등 질환 증상 명시 후 보완청구 승인됨", "deletion_rate": "100%"},
            {"title": "골다공증 약제 중복 처방 삭감", "content": "타 기관 처방 내역 미확인으로 인한 중복 청구.", "tag": "정형외과", "resolution": "타 기관 처방 확인 후 재청구 시 인정됨", "deletion_rate": "50%"},
            {"title": "당뇨병 약제 급여 기준 초과", "content": "3제 요법 인정 기준 미달 환자에게 처방.", "tag": "내과", "resolution": "2제 요법으로 수정 청구 후 인정됨", "deletion_rate": "30%"}
        ]
        
        for case in cases_db:
            if not case_search or case_search in case['title'] or case_search in case['content']:
                with st.expander(f"[{case['tag']}] {case['title']}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**사례 내용:** {case['content']}")
                        st.write(f"**해결 방법:** {case['resolution']}")
                    with col2:
                        st.error(f"삭감률: {case['deletion_rate']}")

    elif menu == "AI 진단 및 분석":
        st.header("🧠 AI 청구 진단 서비스")
        st.write("처방 내역을 입력하면 GPT-4와 Gemini 모델이 협력하여 삭감 위험을 분석합니다.")
        
        prescription_text = st.text_area(
            "처방 내역 또는 텍스트를 입력하세요.", 
            height=200, 
            placeholder="예: [648602750] 씨엠쿨산 1포, [AL300] 외래환자의약품관리료 처방함. 환자 75세, 단순 검진 목적."
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            use_ai = st.checkbox("실제 AI 모델 사용 (OpenAI API 필요)", value=False)
        with col2:
            if st.button("AI 종합 진단 시작"):
                if prescription_text:
                    with st.spinner("다중 AI 모델이 처방 내역을 정밀 분석 중입니다..."):
                        if use_ai:
                            # 실제 AI 분석 (API 키 필요)
                            analyzer = MultiAIAnalyzer()
                            gpt4_result = analyzer.analyze_prescription_gpt4(prescription_text)
                            gemini_result = analyzer.analyze_prescription_gemini(prescription_text)
                            synthesis = analyzer.synthesize_analysis(gpt4_result, gemini_result)
                            
                            st.subheader("📊 AI 종합 진단 보고서")
                            st.json(synthesis)
                        else:
                            # 시뮬레이션 분석
                            import time
                            time.sleep(2)
                            
                            st.subheader("📊 AI 종합 진단 보고서 (시뮬레이션)")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("""
                                <div class="ai-diagnostic">
                                <b>🤖 GPT-4 분석</b><br>
                                - <b>삭감 위험도:</b> <span style='color:red;'>높음 (80%)</span><br>
                                - <b>사유:</b> 단순 검진 목적의 장정결제 처방은 급여 대상이 아닙니다. 비급여 처리가 필요합니다.<br>
                                - <b>권고:</b> 특정내역에 '혈변' 또는 '복통' 등 급여 인정 상병에 대한 증상을 기재하지 않을 경우 100% 삭감 대상입니다.
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown("""
                                <div class="ai-diagnostic">
                                <b>🤖 Gemini 분석</b><br>
                                - <b>주의사항:</b> 75세 고령 환자의 경우 신기능 저하 가능성이 있으므로 전해질 수치 확인이 필요합니다.<br>
                                - <b>특정내역:</b> MT001 코드 사용 시 '검사 전처치' 사유를 구체화하십시오.<br>
                                - <b>대안:</b> 환자 상태가 불안정할 경우 입원 처방(AL010) 고려 가능.
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown("""
                            <div class="warning-card" style="margin-top: 20px;">
                            <b>💡 컨설턴트 최종 제언:</b><br>
                            해당 건은 단순 검진으로 청구 시 삭감될 확률이 매우 높습니다. 
                            진료기록부에 환자의 호소 증상을 명확히 기록하고, 특정내역 기재 요령을 준수하십시오.
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("분석할 텍스트를 입력해 주세요.")

    elif menu == "관리자 설정":
        if st.session_state.user_role == "admin":
            st.header("⚙️ 관리자 데이터 관리")
            
            tab1, tab2, tab3 = st.tabs(["데이터 업로드", "현재 데이터 조회", "시스템 정보"])
            
            with tab1:
                st.subheader("신규 처방 가이드 등록")
                
                with st.form("new_data_form"):
                    st.write("직접 입력 추가")
                    new_code = st.text_input("처방코드", key="new_code")
                    new_name = st.text_input("약품/시술명", key="new_name")
                    new_category = st.text_input("분류 (예: 장정결제, 소화성궤양용제)", key="new_category")
                    new_dept = st.selectbox("진료과", ["내과", "외과", "정형외과", "이비인후과", "피부과", "기타"], key="new_dept")
                    new_prescriptions = st.text_area("권장 처방 리스트 (각 항목을 줄바꿈으로 구분)", key="new_prescriptions")
                    new_hira_criteria = st.text_area("심평원 심사기준", key="new_hira_criteria")
                    new_specific_comments = st.text_area("특정내역 입력 알림", key="new_specific_comments")
                    new_ai_diagnosis = st.text_area("AI 진단 및 주의사항", key="new_ai_diagnosis")
                    new_cases = st.text_area("관련 심사/삭감 사례 (각 항목을 줄바꿈으로 구분)", key="new_cases")
                    
                    submit_add = st.form_submit_button("새 처방 가이드 저장")
                    
                    if submit_add:
                        if new_code and new_name:
                            current_data = load_data()
                            new_entry = {
                                "code": new_code,
                                "name": new_name,
                                "category": new_category,
                                "dept": new_dept,
                                "prescriptions": [p.strip() for p in new_prescriptions.split("\n") if p.strip()],
                                "hira_criteria": new_hira_criteria,
                                "specific_comments": new_specific_comments,
                                "ai_diagnosis": new_ai_diagnosis,
                                "cases": [c.strip() for c in new_cases.split("\n") if c.strip()]
                            }
                            current_data.append(new_entry)
                            save_data(current_data)
                            st.success(f"새로운 처방 가이드 '{new_name}'이(가) 성공적으로 추가되었습니다.")
                            st.rerun()
                        else:
                            st.error("처방코드와 약품/시술명은 필수 입력 항목입니다.")

            with tab2:
                current_data = load_data()
                if current_data:
                    st.subheader("현재 저장된 처방 가이드")
                    df = pd.DataFrame(current_data)
                    st.dataframe(df[["code", "name", "category", "dept"]], use_container_width=True)
                    st.info(f"총 {len(current_data)}개의 처방 가이드가 저장되어 있습니다.")
                else:
                    st.info("현재 저장된 처방 가이드 데이터가 없습니다.")
            
            with tab3:
                st.subheader("시스템 정보")
                st.write(f"**마지막 업데이트:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**저장된 처방 가이드 수:** {len(load_data())}")
                st.write(f"**데이터 파일:** {DATA_FILE}")
        else:
            st.error("관리자 권한이 없습니다. 관리자 계정으로 로그인해 주세요.")

if __name__ == "__main__":
    main()
