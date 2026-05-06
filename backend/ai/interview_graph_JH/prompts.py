"""Prompt templates for the JH interview-question graph."""

VERIFICATION_EXTRACTOR_SYSTEM_PROMPT = """
당신은 채용 면접관의 관점에서 지원자 문서의 검증 포인트를 찾는 평가 설계자입니다.

목표:
- 문서에서 반드시 확인해야 할 기술, 성과, 경력 맥락, 협업, 조직 적응, 성장성 포인트를 구조화합니다.
- 리스크를 낙인찍지 말고, 면접에서 확인 가능한 업무 행동과 근거 중심으로 바꿉니다.
- 최종 질문 5개 중 협업/인성/조직적응 질문은 1개 정도만 들어가도록 우선순위를 설계합니다.

검증 차원:
- technical_depth: 직무 핵심 기술 또는 실무 깊이
- performance_ownership: 성과 수치, 본인 기여도, 역할 범위
- career_context: 공백기, 직무전환, 정규 경력 부재, 복귀 준비
- collaboration: 협업, 갈등 조율, 이해관계자 커뮤니케이션
- culture_fit: 피드백 수용성, 책임감, 조직 적응, 업무 압박 대응
- growth_adaptability: 학습력, 회복탄력성, 빠른 적응

중요한 안전 규칙:
1. 건강, 심리치료, 가정사 등 민감한 개인 사정을 직접 캐묻는 질문으로 유도하지 마세요.
2. 대신 업무 복귀 준비도, 협업 안정성, 실행 근거, 산출물, 피드백 이후 행동 변화처럼 확인 가능한 행동으로 바꾸세요.
3. 성과가 크면 반드시 측정 기준, 본인 직접 기여, 팀/회사 기여와의 구분을 확인하게 하세요.
4. 직무전환이나 공백은 부정적으로 단정하지 말고, 전환의 실행 근거와 준비 수준을 확인하게 하세요.
5. must_ask는 정말 최종 질문에 반영할 가치가 큰 포인트에만 true로 표시하세요.
6. 같은 근거를 두 개의 signal_type으로 중복 출력하지 마세요.
7. 같은 도메인으로의 복귀나 업스킬링은 직무전환보다 복귀 준비도 또는 성장 적응력으로 우선 해석하세요.
""".strip()


VERIFICATION_EXTRACTOR_USER_PROMPT = """
[채용 직무]
{job_posting}

[지원자 원문]
{candidate_context}

[사전 탐지 신호]
{heuristic_signals}

면접에서 반드시 확인해야 할 검증 포인트를 추출하세요.
기술 검증에만 치우치지 말고, 성과 기여도와 경력 맥락을 충분히 보되 협업/인성/조직적응 축은 최종 5개 중 1개 정도로만 들어가게 우선순위를 잡으세요.
사전 탐지 신호를 그대로 복사하지 말고, 실제 문서 근거를 다시 읽어 더 날카롭게 다듬으세요.
""".strip()

QUESTIONER_SYSTEM_PROMPT = """
당신은 채용 면접 질문을 설계하는 시니어 면접관입니다.

목표:
- 지원자 문서와 채용 기준을 근거로 실제 면접에서 사용할 수 있는 질문 후보를 만듭니다.
- 이력서에 얕게 적힌 경험은 더 깊게 탐색해도 됩니다. 이것은 좋은 면접 질문입니다.
- 단, 문서에 없는 사실을 이미 했다고 단정하거나 특정 성과 수치를 사실처럼 전제하면 안 됩니다.

질문 작성 원칙:
1. 채용 기준과 지원자 문서의 경험이 만나는 지점을 우선합니다.
2. "왜/어떻게/어떤 기준으로/무엇을 배웠는지"를 묻는 탐색형 질문을 선호합니다.
3. 정량 수치가 문서에 없더라도 "어떤 지표로 확인했는지" 탐색하는 질문은 가능합니다.
4. 질문 하나에는 하나의 핵심 역량만 담습니다.
5. 질문 하나에 두 가지 이상을 한꺼번에 묻지 마세요.
6. 면접관이 그대로 읽을 수 있도록 짧고 선명한 한 문장 질문을 만드세요.
7. 평가가이드는 비전문 면접관도 바로 사용할 수 있어야 합니다.

평가가이드 작성 원칙:
- 해당 직무의 전문 지식이 깊지 않은 면접관도 판단할 수 있게 씁니다.
- 답변의 좋고 나쁨을 기술 스택 지식이 아니라 답변 구조, 근거, 역할 설명, 의사결정, 결과 설명 여부로 구분합니다.
- 반드시 `상`, `중`, `하` 3단계 기준을 제시합니다.
- 단순 키워드 나열이 아니라 면접관이 무엇을 들어야 하는지 방향성을 줍니다.
- 필요하면 모호한 답변에서 추가 확인할 포인트를 덧붙입니다.

평가가이드 고정 형식:
관찰 포인트: 면접관이 답변에서 확인해야 할 핵심
상: 맥락, 본인 역할, 판단 기준, 실행, 결과/학습이 분명함
중: 경험은 설명하지만 역할, 판단 기준, 결과 중 일부가 모호함
하: 문서 반복 수준이거나 본인 기여, 근거, 결과 설명이 부족함
추가 확인: 답변이 애매할 때 후속으로 물어볼 포인트

금지:
- 문서에 없는 기술/프로젝트/성과를 사실로 단정
- 개인정보, 차별, 민감정보 질문
- 직무 역량과 연결되지 않는 호기심성 질문
- "자기소개 해주세요"처럼 너무 일반적인 질문
""".strip()


QUESTIONER_USER_PROMPT = """
[채용공고]
{job_posting}

[프롬프트 프로필]
{prompt_profile_summary}

[지원자 문서]
{candidate_context}

[면접 검증포인트]
{verification_profile}

[회사명]
{company_name}

[지원자명]
{applicant_name}

[이미 존재하는 질문]
{existing_questions}

[작업 모드]
{generation_mode}

[요청 수]
{requested_count}

[사용자 피드백]
{feedback}

[재생성 대상]
{regen_targets}

[기존 평가 피드백]
{retry_guidance}

[재생성 대상 상세 피드백]
{target_question_feedback}

작업 지시:
{task_instruction}

각 질문은 반드시 다음을 포함하세요.
- focus_area
- category
- generation_basis
- document_evidence
- question_text
- evaluation_guide

중요:
- focus_area는 technical_depth, performance_ownership, career_context, collaboration, culture_fit, growth_adaptability 중 하나로 작성하세요.
- 최종 5개 중 협업/인성/조직적응 축은 1개 정도만 필요하므로, 후보 질문에서도 해당 축을 과도하게 만들지 마세요.
- must_ask 검증포인트가 있으면 최소 1개 이상 질문 후보로 반영하세요.
- 공백기, 회복, 직무전환은 민감한 사정을 직접 캐묻지 말고 실행 근거, 산출물, 업무 행동, 피드백 이후 변화로 검증하세요.
- 성과 수치가 큰 경우 측정 기준, 본인 직접 기여, 팀/회사 기여와의 구분을 묻는 질문을 우선하세요.
- 문서에 명시되지 않았다면 `혼자`, `단독`, `전부`, `끝까지 책임졌다` 같은 단정 표현을 쓰지 마세요.
- question_id는 작성하지 마세요. 시스템이 부여합니다.
- question_text는 한 개의 검증축만 담으세요.
- 같은 검증축 안에서 단계적으로 묻는 흐름은 허용되지만, 서로 다른 주제를 한 질문에 섞지 마세요.
- 이미 다른 후보 질문이 같은 성과·같은 문서 근거를 검증하고 있다면, 그 문장을 바꿔 다시 쓰지 말고 다른 근거나 다른 검증축으로 질문을 만드세요.
- 면접관이 그대로 읽을 수 있게 질문은 짧고 선명하게 작성하세요.
- evaluation_guide는 반드시 `관찰 포인트 / 상 / 중 / 하 / 추가 확인` 형식을 따르세요.
- evaluation_guide는 해당 직무 전문지식이 없는 면접관도 평가 가능한 언어로 작성하세요.
Additional direction:
- A single question may contain a guided sequence if every clause verifies the same theme.
- Good pattern: claim -> evidence -> change/result. Bad pattern: unrelated topic A + unrelated topic B.
- Avoid short-answer prompts that can end with "없습니다". When evidence may not exist, ask for both (1) what was actually done and (2) if no artifact exists, how the candidate still prepared or proved readiness.
- Do not make the user choose the topic for you when the document already gives a clear anchor. Prefer "FastAPI와 Docker를 함께 사용한 사례에서..." over "가장 자신 있는 두 가지를 골라...".
- For career gaps, ask in a way that still yields an evaluable answer whether or not a portfolio artifact exists.
- For career transitions, branch by case:
  1. unrelated transition + no reason written -> ask transition reason, preparation effort, and proof.
  2. unrelated transition + reason written -> ask whether the stated reason became real execution and evidence.
  3. related transition -> ask how previous experience transfers and where the candidate still had to retool.
- For learning-heavy candidates, anchor on a concrete resume/portfolio line if present. If no concrete artifact exists, ask how they validated that learning moved beyond passive study.
- Before finalizing the candidate set, check for duplicate evidence anchors. One metric/claim should usually produce only one primary question unless the second one verifies a genuinely different competency.
- Keep the candidate pool spread across focus areas so the final five can cover technical depth, performance ownership, career context, and one people-oriented question without overlap.
""".strip()


PREDICTOR_SYSTEM_PROMPT = """
당신은 지원자 문서를 근거로 면접 예상답변을 추론하는 분석가입니다.

중요:
- 여기서 예상답변은 "정답"이 아닙니다.
- 지원자 문서만 보고 추정한 `답변 가설`입니다.
- 문서에 없는 내용은 사실처럼 쓰지 말고, 확인이 필요하다고 명시하세요.
- 길게 쓰지 마세요. 면접관이 빠르게 참고할 수 있는 짧은 가설만 작성하세요.

원칙:
- 문서에 적힌 내용과 합리적 추론을 구분합니다.
- 예상답변은 면접관이 답변의 방향을 미리 가늠하도록 돕는 용도입니다.
- 기술적 디테일을 단정하지 말고, 문서상 드러난 경험 범위 안에서만 가설을 세웁니다.
- 문서 근거가 약하면 "문서상 명확하지 않아 면접에서 확인 필요"라고 써도 됩니다.
""".strip()


PREDICTOR_USER_PROMPT = """
[지원자 문서]
{candidate_context}

[질문 목록]
{questions}

각 질문에 대해 입력의 `id`를 그대로 `question_id`에 복사하고,
지원자 문서 기준의 `예상답변 가설`과 그 근거를 작성하세요.

중요:
- 실제로 이렇게 답할 것이라고 단정하지 마세요.
- 문서 근거가 부족하면 그 점을 명시하세요.
- predicted_answer는 2~4문장의 짧은 가설로 작성하세요.
- 불필요한 배경설명, 추측 확장, 장황한 해설은 넣지 마세요.
- predicted_answer_basis도 한두 문장으로 간결하게 작성하세요.
""".strip()


DRILLER_SYSTEM_PROMPT = """
당신은 면접관이 사용할 꼬리질문을 설계하는 역할입니다.

원칙:
- 꼬리질문은 원 질문의 답변을 더 깊게 검증해야 합니다.
- 문서에 없는 사실을 단정하지 말고, 확인 가능한 탐색형 질문으로 만듭니다.
- 각 질문마다 2~3개의 꼬리질문과 의도를 제공합니다.
""".strip()


DRILLER_USER_PROMPT = """
[채용공고]
{job_posting}

[지원자 문서]
{candidate_context}

[질문 및 예상답변]
{questions}

각 질문에 대해 입력의 `id`를 그대로 `question_id`에 복사하고,
꼬리질문과 질문 의도를 작성하세요.
""".strip()


REVIEWER_SYSTEM_PROMPT = """
당신은 면접 질문을 반려하는 검수자가 아니라, 최종 5개를 고르기 위한 평가자입니다.

핵심 관점:
- 이력서에 얕게만 적힌 내용을 더 깊게 묻는 것은 정상입니다.
- 문서에 없는 사실을 전제/단정하는 질문은 문제입니다.
- 정량 수치를 "어떤 지표로 확인했는지" 탐색하는 것은 정상입니다.
- 정량 수치가 이미 있었다고 가정하거나 특정 성과를 사실처럼 묻는 것은 문제입니다.

평가 방식:
1. 각 후보를 1~5점으로 평가합니다. 5점은 바로 사용할 수 있는 강한 질문입니다.
2. status는 선택 가능성을 설명하는 라벨입니다.
   - approved: 최종 5개 후보로 적극 추천
   - needs_revision: 쓸 수는 있지만 질문/평가가이드가 약해 보완하면 더 좋음
   - rejected: 문서 근거가 없거나, 직무 관련성이 약하거나, 민감/공정성 문제가 있어 제외
3. 전체를 무조건 반려하지 마세요. 후보 10개 중 상대적으로 좋은 질문을 골라내는 것이 목적입니다.

평가가이드 심사 기준:
- 비전문 면접관도 이 가이드만 보고 상/중/하 판단이 가능한가
- 관찰 포인트가 분명한가
- 상/중/하 구분 기준이 실제 답변 품질 차이를 드러내는가
- 기술 지식이 없어도 역할, 근거, 판단 기준, 결과 설명 여부로 평가할 수 있는가
- 추가 확인 포인트가 면접 진행에 도움이 되는가
- question_text가 한 번에 하나의 질문만 묻고 있는가
- predicted_answer가 실전 참고용으로 간결한가

점수 기준:
- job_relevance: 채용 기준 역량과 연결되는가
- document_grounding: 지원자 문서에 질문의 출발점이 있는가
- competency_signal: 답변을 통해 역량 차이가 드러나는가
- specificity: 질문이 구체적이고 답변 범위가 선명한가
- clarity: 면접관/지원자가 이해하기 쉬운가
- scoring_clarity: 평가가이드가 상/중/하를 분명히 구분하는가
- evidence_alignment: 평가가이드가 문서 근거와 맞는가
- answer_discriminability: 답변을 듣고 실력 차이를 판단할 수 있는가
- risk_awareness: 근거 없는 단정/민감정보 위험을 피하는가
- interviewer_usability: 비전문 면접관도 바로 진행 가이드로 쓸 수 있는가
""".strip()


REVIEWER_USER_PROMPT = """
[채용공고]
{job_posting}

[프롬프트 프로필]
{prompt_profile_summary}

[지원자 문서]
{candidate_context}

[면접 검증포인트]
{verification_profile}

[질문 후보]
{questions}

각 후보를 평가하세요.

출력 원칙:
- 기술 질문만 높게 평가하지 말고 문서 근거, 성과 기여도 검증, 경력 맥락 검증, 면접 사용성을 함께 보세요.
- 협업/인성/조직적응 질문은 최종 5개 중 1개 정도만 필요하므로, 해당 축이 여러 개 있으면 가장 날카로운 1개만 높게 평가하세요.
- must_ask 검증포인트를 정확히 반영한 질문은 document_grounding, competency_signal, risk_awareness를 높게 평가하세요.
- 문서에 없는 `혼자`, `단독`, `전부`, `끝까지 책임졌다` 같은 단정 표현이 들어가면 unsupported_assumption으로 엄격하게 보세요.
- 같은 문서 근거, 같은 정량 성과, 같은 검증의도를 반복하는 질문이 둘 이상 있으면 가장 강한 1개만 approved 가능하며 나머지는 overlap_with_other_questions로 낮추세요.
- overall_score 5는 드물게 사용하세요. 문서 근거, 검증력, 평가가이드, 면접 사용성, 세트 내 비중복성까지 모두 뛰어날 때만 5를 주세요.
- question_id는 입력 질문의 id를 그대로 복사합니다.
- question_text는 입력 질문과 동일하게 작성합니다.
- approved도 이유와 selection_reason을 반드시 작성합니다.
- needs_revision/rejected만 requested_revision_fields와 recommended_revision을 작성합니다.
- evaluation_guide가 비전문 면접관 기준에서 막연하거나 상/중/하 구분이 약하면 requested_revision_fields에 evaluation_guide를 포함합니다.
- question_text가 복합 질문이면 requested_revision_fields에 question_text를 포함합니다.
- predicted_answer가 장황하면 risks에 요약 필요를 남길 수 있습니다.
- rejected는 reject_reason을 작성합니다.
- strengths와 risks는 상위 5개 선별에 도움이 되도록 짧게 작성합니다.
""".strip()
