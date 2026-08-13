from webapp.grounded_llm import GroundedLLM


def test_evidence_only_mode_uses_professional_source_wording():
    answerer = GroundedLLM()

    assert answerer.configured is False
    answer = answerer.answer(question="Quy định là gì?", citations=[])

    assert "Chế độ truy xuất bằng chứng" in answer
    assert "Chưa cấu hình chatbot" not in answer
    answerer.close()
