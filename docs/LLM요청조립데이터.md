## 1. 기획·전략 (STRATEGY_PLANNING)

```
{
  "session": {
    "session_id":201,
    "candidate_id":301,
    "target_job":"STRATEGY_PLANNING",
    "difficulty_level":"JUNIOR",
    "prompt_profile_id":2001,
    "created_at":"2026-04-24T09:00:00Z"
  },
  "candidate": {
    "candidate_id":301,
    "name":"김유진",
    "email":"yujin.kim@example.com",
    "phone":"010-1234-1111",
    "birth_date":"1995-06-12",
    "job_position":"STRATEGY_PLANNING",
    "apply_status":"APPLIED"
  },
  "prompt_profile": {
    "id":2001,
    "profile_key":"SP_FULL_01",
    "target_job":"STRATEGY_PLANNING",
    "system_prompt":"기획·전략 직무 면접 질문 생성. 문제 정의, 시장 분석, 데이터 기반 의사결정 능력을 평가.",
    "output_schema": {
      "questions": [
        {
          "question_text":"string",
          "competency":"analytical_thinking",
          "rationale":"string"
        }
      ]
    }
  },
  "candidate_documents_summary": {
    "count":1,
    "total_extracted_text_length":2500,
    "items": [
      {
        "document_id":401,
        "document_type":"ROLE_PROFILE",
        "title":"전략기획_김유진",
        "extract_status":"SUCCESS",
        "extracted_text_preview":"시장 분석 프로젝트 수행. 고객 세분화 및 경쟁사 비교 분석을 통해 신규 서비스 방향 제안 경험 보유. 데이터 기반 문제 정의와 개선안 도출 경험이 있음."
      }
    ]
  }
}
```

---

## 2. 인사·HR (HR)

```
{
  "session": {
    "session_id":202,
    "candidate_id":302,
    "target_job":"HR",
    "difficulty_level":"JUNIOR",
    "prompt_profile_id":2002,
    "created_at":"2026-04-24T09:00:00Z"
  },
  "candidate": {
    "candidate_id":302,
    "name":"박소연",
    "email":"soyeon.park@example.com",
    "phone":"010-2222-1111",
    "birth_date":"1996-04-22",
    "job_position":"HR",
    "apply_status":"APPLIED"
  },
  "prompt_profile": {
    "id":2002,
    "profile_key":"HR_FULL_01",
    "target_job":"HR",
    "system_prompt":"HR 직무 면접 질문 생성. 조직 커뮤니케이션, 갈등 관리, 인재 이해 능력 평가.",
    "output_schema": {
      "questions": [
        {
          "question_text":"string",
          "competency":"communication",
          "rationale":"string"
        }
      ]
    }
  },
  "candidate_documents_summary": {
    "count":1,
    "total_extracted_text_length":2200,
    "items": [
      {
        "document_id":402,
        "document_type":"ROLE_PROFILE",
        "title":"HR_박소연",
        "extract_status":"SUCCESS",
        "extracted_text_preview":"동아리 운영 및 팀 프로젝트에서 갈등 중재 경험. 구성원 간 의견 차이를 조율하고 조직 분위기 개선에 기여한 경험 보유."
      }
    ]
  }
}
```

---

## 3. 마케팅·광고·MD (MARKETING)

```
{
  "session": {
    "session_id":203,
    "candidate_id":303,
    "target_job":"MARKETING",
    "difficulty_level":"JUNIOR",
    "prompt_profile_id":2003,
    "created_at":"2026-04-24T09:00:00Z"
  },
  "candidate": {
    "candidate_id":303,
    "name":"이민호",
    "email":"minho.lee@example.com",
    "phone":"010-3333-1111",
    "birth_date":"1997-08-10",
    "job_position":"MARKETING",
    "apply_status":"APPLIED"
  },
  "prompt_profile": {
    "id":2003,
    "profile_key":"MK_FULL_01",
    "target_job":"MARKETING",
    "system_prompt":"마케팅 직무 면접 질문 생성. 고객 이해, 콘텐츠 기획, 데이터 기반 성과 분석 능력 평가.",
    "output_schema": {
      "questions": [
        {
          "question_text":"string",
          "competency":"customer_insight",
          "rationale":"string"
        }
      ]
    }
  },
  "candidate_documents_summary": {
    "count":1,
    "total_extracted_text_length":2400,
    "items": [
      {
        "document_id":403,
        "document_type":"ROLE_PROFILE",
        "title":"마케팅_이민호",
        "extract_status":"SUCCESS",
        "extracted_text_preview":"SNS 광고 캠페인 운영 경험. 클릭률 및 전환율 데이터를 분석하여 광고 성과 개선. 타겟 고객 정의 및 콘텐츠 전략 수립 경험."
      }
    ]
  }
}
```

---

## 4. AI·개발·데이터 (AI_DEV_DATA)

```
{
  "session": {
    "session_id":204,
    "candidate_id":304,
    "target_job":"AI_DEV_DATA",
    "difficulty_level":"INTERMEDIATE",
    "prompt_profile_id":2004,
    "created_at":"2026-04-24T09:00:00Z"
  },
  "candidate": {
    "candidate_id":304,
    "name":"최지훈",
    "email":"jihun.choi@example.com",
    "phone":"010-4444-1111",
    "birth_date":"1998-01-05",
    "job_position":"AI_DEV_DATA",
    "apply_status":"APPLIED"
  },
  "prompt_profile": {
    "id":2004,
    "profile_key":"AI_FULL_01",
    "target_job":"AI_DEV_DATA",
    "system_prompt":"AI/개발 직무 면접 질문 생성. 알고리즘, 데이터 처리, 문제 해결 능력 평가.",
    "output_schema": {
      "questions": [
        {
          "question_text":"string",
          "competency":"coding",
          "rationale":"string"
        }
      ]
    }
  },
  "candidate_documents_summary": {
    "count":1,
    "total_extracted_text_length":3000,
    "items": [
      {
        "document_id":404,
        "document_type":"ROLE_PROFILE",
        "title":"AI개발_최지훈",
        "extract_status":"SUCCESS",
        "extracted_text_preview":"Python 기반 데이터 분석 및 머신러닝 모델 개발 경험. 분류 모델 성능 개선 및 데이터 전처리 경험 보유."
      }
    ]
  }
}
```

---

## 5. 영업 (SALES)

```
{
  "session": {
    "session_id":205,
    "candidate_id":305,
    "target_job":"SALES",
    "difficulty_level":"JUNIOR",
    "prompt_profile_id":2005,
    "created_at":"2026-04-24T09:00:00Z"
  },
  "candidate": {
    "candidate_id":305,
    "name":"정수민",
    "email":"sumin.jung@example.com",
    "phone":"010-5555-1111",
    "birth_date":"1994-12-03",
    "job_position":"SALES",
    "apply_status":"APPLIED"
  },
  "prompt_profile": {
    "id":2005,
    "profile_key":"SALES_FULL_01",
    "target_job":"SALES",
    "system_prompt":"영업 직무 면접 질문 생성. 고객 설득, 관계 형성, 목표 달성 경험 평가.",
    "output_schema": {
      "questions": [
        {
          "question_text":"string",
          "competency":"persuasion",
          "rationale":"string"
        }
      ]
    }
  },
  "candidate_documents_summary": {
    "count":1,
    "total_extracted_text_length":2100,
    "items": [
      {
        "document_id":405,
        "document_type":"ROLE_PROFILE",
        "title":"영업_정수민",
        "extract_status":"SUCCESS",
        "extracted_text_preview":"B2C 영업 경험. 고객 니즈 파악 및 제품 추천을 통해 매출 목표 초과 달성. 고객 관계 유지 및 재구매 유도 경험 보유."
      }
    ]
  }
}
```

참고
각 payload는 LangGraph / LLM 입력용으로 설계됨
직무별 competency 설계가 핵심 품질 요소
system_prompt는 사실상 면접 평가 기준 정의서 역할 수행