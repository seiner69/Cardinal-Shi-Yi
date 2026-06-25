import pytest

from fastapi import HTTPException

import src.api as api_module
from src.api import InferRequest, PhysicsRequest, PhysicsUncertainty, build_physics_seed, hexagram_text, infer, node, physics, simulate
from src.fsm_kernel import (
    FSMState,
    HEXAGRAM_LOOKUP,
    HEX_STATES,
    e_dimension,
    from_display_bits,
    get_hex_state,
    get_hexagram_name,
    monte_carlo_state_distribution,
    path2_hidden_core_exposure,
    physics_snapshot,
    raw_physics_step,
    tensor_for_bit,
    to_display_bits,
    uncertainty_confidence,
)
from src.models.schema import FSMOutput
from src.data.hexagrams import HEXAGRAM_DATA
from src.llm.chain import FSMAnalysisParseError, IChingChain, derive_target_hexagram


def test_from_physics_defaults_baselines_to_current_values():
    state = FSMState.from_physics(
        bits="101010",
        E=[1000, 900, 800, 700, 600, 500],
        P=[10, 20, 30, 40, 50, 60],
        R=[80, 70, 60, 50, 40, 30],
        tau=[100, 100, 100, 100, 100, 100],
    )

    assert state.E_initial == state.E
    assert state.R_base == state.R
    assert tensor_for_bit(state, 1)["t"] == 0
    assert tensor_for_bit(state, 1)["e"] == 1


def test_bottom_layer_has_absolute_base_support():
    state = FSMState.from_physics(
        bits="100000",
        E=[1, 1, 1, 1, 1, 1],
        P=[0, 0, 0, 0, 0, 0],
        R=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
        tau=[1, 1, 1, 1, 1, 1],
    )

    stepped = raw_physics_step(state)

    assert stepped.E[0] == pytest.approx(0.9)


def test_trigram_and_hexagram_mapping_matches_principle_layer():
    assert get_hexagram_name("100", "010") == "屯"
    assert get_hexagram_name("010", "001") == "蒙"
    assert get_hexagram_name("111", "000") == "泰"
    assert get_hexagram_name("000", "111") == "否"
    assert get_hexagram_name("011", "101") == "鼎"
    assert get_hexagram_name("000", "100") == "豫"
    assert get_hexagram_name("100", "000") == "复"
    assert get_hexagram_name("100", "110") == "随"
    assert get_hexagram_name("011", "110") == "大过"
    assert get_hexagram_name("101", "110") == "革"
    assert "遁" in HEXAGRAM_DATA
    assert HEXAGRAM_DATA["遁"]["index"] == HEXAGRAM_DATA["遯"]["index"]


def test_display_bits_are_not_confused_with_internal_bits():
    internal_tai = FSMState.from_bits("111000")
    assert get_hexagram_name(internal_tai.inner_bits(), internal_tai.outer_bits()) == "泰"
    assert to_display_bits(internal_tai.full_bits()) == "000111"

    internal_from_user_display = FSMState.from_bits(from_display_bits("111000"))
    assert internal_from_user_display.full_bits() == "000111"
    assert get_hexagram_name(
        internal_from_user_display.inner_bits(),
        internal_from_user_display.outer_bits(),
    ) == "否"

    node_result = node("111000", code_order="display")
    assert node_result["bits"] == "000111"
    assert node_result["display_bits"] == "111000"
    assert node_result["hexagram"] == "否"


def test_hexagram_text_api_returns_gua_and_six_yao():
    result = hexagram_text("泰")

    assert result["name"] == "泰"
    assert result["gua_ci"]
    assert len(result["yao"]) == 6
    assert result["yao"][0]["position"]
    assert result["yao"][0]["text"]


def test_hexagram_text_api_sorts_yao_from_bottom_to_top():
    result = hexagram_text("屯")

    assert [line["position"] for line in result["yao"]] == ["初九", "六二", "六三", "六四", "九五", "上六"]


def test_infer_returns_422_when_fsm_json_parse_fails(monkeypatch):
    class BrokenChain:
        def run(self, query: str):
            raise FSMAnalysisParseError("broken json")

    monkeypatch.setattr(api_module, "IChingChain", BrokenChain)

    with pytest.raises(HTTPException) as exc_info:
        infer(InferRequest(query="bad model response"))

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["code"] == "FSM_ANALYSIS_PARSE_FAILED"


def test_empty_fsm_model_response_raises_without_local_takeover(monkeypatch):
    chain = IChingChain()
    monkeypatch.setattr(chain, "_call_llm", lambda *args, **kwargs: "")

    with pytest.raises(FSMAnalysisParseError) as exc_info:
        chain.generate_fsm_analysis(
            "李充家贫，后立精舍讲授，不就太守署功曹。和帝公车征不行，贵戚邓骘设宴，充抵肉于地径去。",
            "未检索到相关内容",
        )

    assert "未进行本地规则接管" in str(exc_info.value)


def test_broken_fsm_json_uses_model_repair_not_local_rules(monkeypatch):
    chain = IChingChain()
    responses = iter([
        '{"inner_system": "李充"',
        """
        {
          "inner_system": "李充自身",
          "outer_system": "官府与贵戚权势",
          "inner_bits": "001",
          "outer_bits": "110",
          "bit_analysis": [
            {"bit_position": 1, "value": "0", "description": "家贫"},
            {"bit_position": 2, "value": "0", "description": "初无官位"},
            {"bit_position": 3, "value": "1", "description": "高节不屈"},
            {"bit_position": 4, "value": "1", "description": "地方冲突"},
            {"bit_position": 5, "value": "1", "description": "官制征辟"},
            {"bit_position": 6, "value": "0", "description": "天子礼遇非压制"}
          ],
          "energy_focus": {"focus_bit": 3, "focus_description": "高节意志硬抗权势"},
          "stress_analysis": {"stress_type": "向上撞墙", "analysis": "上层权势压制"},
          "mutation_suggestion": "降低正面折冲",
          "target_hexagram": "",
          "hexagram_reason": "",
          "referenced_yao": "",
          "yao_interpretation": ""
        }
        """,
    ])
    monkeypatch.setattr(chain, "_call_llm", lambda *args, **kwargs: next(responses))

    result = chain.generate_fsm_analysis(
        "李充家贫，后立精舍讲授，不就太守署功曹。和帝公车征不行，贵戚邓骘设宴，充抵肉于地径去。",
        "未检索到相关内容",
    )

    assert result.inner_bits == "001"
    assert result.outer_bits == "110"
    assert result.energy_focus.focus_bit == 3


def test_repaired_fsm_json_uses_same_stress_normalization(monkeypatch):
    chain = IChingChain()
    responses = iter([
        '{"inner_system": "李充"',
        """
        {
          "inner_system": "李充自身",
          "outer_system": "官府与贵戚权势",
          "inner_bits": "001",
          "outer_bits": "110",
          "bit_analysis": [
            {"bit_position": 1, "value": "0", "description": "家贫"},
            {"bit_position": 2, "value": "0", "description": "初无官位"},
            {"bit_position": 3, "value": "1", "description": "高节不屈"},
            {"bit_position": 4, "value": "1", "description": "地方冲突"},
            {"bit_position": 5, "value": "1", "description": "官制征辟"},
            {"bit_position": 6, "value": "0", "description": "天子礼遇非压制"}
          ],
          "energy_focus": {"focus_bit": 3, "focus_description": "高节意志硬抗权势"},
          "stress_analysis": {"stress_type": "压强挤压", "analysis": "上层权势压制"},
          "mutation_suggestion": "降低正面折冲",
          "target_hexagram": "",
          "hexagram_reason": "",
          "referenced_yao": "",
          "yao_interpretation": ""
        }
        """,
    ])
    monkeypatch.setattr(chain, "_call_llm", lambda *args, **kwargs: next(responses))

    result = chain.generate_fsm_analysis(
        "李充抵肉于地径去。",
        "未检索到相关内容",
    )

    assert result.stress_analysis.stress_type == "向上撞墙"


def test_invalid_target_derivation_does_not_default_to_qian():
    result = derive_target_hexagram("000", "000", "稳定", 0)

    assert result["hexagram"] == ""
    assert "参数错误" in result["reason"]


def test_all_64_physical_nodes_are_defined_without_silent_overwrite():
    assert len(HEX_STATES) == 64
    assert {value[0] for value in HEX_STATES.values()} == set(range(1, 65))

    state = FSMState.from_bits("100010")
    assert get_hex_state(state)[0] == 3
    assert get_hex_state(state)[1] == "受限爆发态"

    expected_by_index = {
        16: "豫",
        17: "随",
        24: "复",
        28: "大过",
        49: "革",
    }
    for key, (index, _, _) in HEX_STATES.items():
        if index in expected_by_index:
            assert HEXAGRAM_LOOKUP[key] == expected_by_index[index]


def test_e_dimension_follows_principle_formula():
    assert e_dimension(0.05, 0.1) == 1
    assert e_dimension(0.1, 0.1) == 1
    assert e_dimension(0.15, 0.1) == pytest.approx(0)
    assert e_dimension(0.2, 0.1) == -1
    assert e_dimension(0.3, 0.1) == -1


def test_uncertainty_requires_four_values_when_list_is_used():
    state = FSMState.from_bits("101010")

    with pytest.raises(ValueError, match="exactly 4"):
        uncertainty_confidence([0.1, 0.2])

    with pytest.raises(ValueError, match="exactly 4"):
        monte_carlo_state_distribution(state, U=[0.1], N=2)


def test_from_physics_rejects_invalid_physical_ranges():
    with pytest.raises(ValueError, match="non-negative"):
        FSMState.from_physics(
            bits="101010",
            E=[1, -1, 1, 1, 1, 1],
            P=[0, 0, 0, 0, 0, 0],
            R=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
            tau=[1, 1, 1, 1, 1, 1],
        )

    with pytest.raises(ValueError, match="positive"):
        FSMState.from_physics(
            bits="101010",
            E=[1, 1, 1, 1, 1, 1],
            P=[0, 0, 0, 0, 0, 0],
            R=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
            tau=[1, 1, 0, 1, 1, 1],
        )


def test_physics_snapshot_uses_route_context():
    state = FSMState.from_physics(
        bits="100001",
        E=[1, 1, 1, 1, 1, 1],
        P=[0, 0, 0, 0, 0, 0],
        R=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
        tau=[1, 1, 1, 1, 1, 1],
    )

    default_snapshot = physics_snapshot(state)
    masked_snapshot = physics_snapshot(state, time_in_state=6)

    assert default_snapshot["route"]["path_number"] == 1
    assert masked_snapshot["route"]["path_number"] == 2
    assert masked_snapshot["route"]["next_bits"] == "000000"
    assert masked_snapshot["selected_next_bits"] == "000000"


def test_hidden_core_uses_middle_four_lines():
    state = FSMState.from_bits("101101")
    result = path2_hidden_core_exposure(state)

    assert result["next_bits"] == "011110"


def test_legacy_api_invalid_bits_raise_http_400():
    with pytest.raises(HTTPException) as simulate_error:
        simulate("abc")
    assert simulate_error.value.status_code == 400

    with pytest.raises(HTTPException) as node_error:
        node("101")
    assert node_error.value.status_code == 400


def test_api_physics_uses_named_uncertainty_model():
    body = PhysicsRequest(
        bits="101010",
        E=[1.0, 0.8, 0.15, 0.7, 0.4, 0.9],
        P=[0.1, 0.2, 0.3, 0.95, 0.2, 0.1],
        R=[0.1, 0.1, 0.12, 0.1, 0.1, 0.1],
        tau=[1, 1, 1, 1, 1, 1],
        C=[0.15, 0.15, 0.15, 0.15, 0.15, 0.15],
        U=PhysicsUncertainty(U_E=0.05, U_P=0.25, U_R=0.05, U_tau=0.05),
        monte_carlo_N=5,
    )

    result = physics(body)

    assert result["confidence"]["conf_input"] == 0.75
    assert result["focus_bit"] == 4
    assert result["event"] == "explosion"
    assert result["next_bits"] == "101110"
    assert result["route"]["next_bits"] == "101110"
    assert result["selected_next_bits"] == "101110"
    assert result["monte_carlo"]


def test_infer_physics_seed_translates_analysis_material_to_raw_inputs():
    fsm_result = FSMOutput(
        inner_system="城内粮道",
        outer_system="围城压力",
        inner_bits="100",
        outer_bits="010",
        bit_analysis=[
            {"bit_position": 1, "value": "1", "description": "城内仍有最低生存资源"},
            {"bit_position": 2, "value": "0", "description": "补给断供，燃料耗尽，压力集中"},
            {"bit_position": 3, "value": "0", "description": "守城意志被消耗，难以继续扩张"},
            {"bit_position": 4, "value": "0", "description": "外部基层接口暂未打开通道"},
            {"bit_position": 5, "value": "1", "description": "外部监管挤压，存在资源支撑"},
            {"bit_position": 6, "value": "0", "description": "宏观天花板未直接注能"},
        ],
        energy_focus={"focus_bit": 2, "focus_description": "补给层成为瓶颈"},
        stress_analysis={"stress_type": "向上撞墙", "analysis": "压强爆破，系统闭塞"},
    )

    seed = build_physics_seed(fsm_result, "围城闭塞，债务压力升高")
    snapshot = physics(PhysicsRequest(**{**seed, "monte_carlo_N": 5}))

    assert seed["bits"] == "100010"
    assert all(len(seed[key]) == 6 for key in ["E", "P", "R", "tau", "C", "E_initial", "R_base"])
    assert seed["P"][1] >= 0.86
    assert seed["C"][1] >= 0.2
    assert seed["deadlock_flag"] is True
    assert snapshot["bits"] == seed["bits"]
    assert snapshot["layers"][1]["P"] == seed["P"][1]


def test_fsm_output_requires_all_six_bit_analyses():
    with pytest.raises(ValueError):
        FSMOutput(
            inner_system="城内粮道",
            outer_system="围城压力",
            inner_bits="100",
            outer_bits="010",
            bit_analysis=[
                {"bit_position": 2, "value": "0", "description": "补给断供"},
                {"bit_position": 5, "value": "1", "description": "外部监管"},
            ],
            energy_focus={"focus_bit": 2, "focus_description": "补给层成为瓶颈"},
            stress_analysis={"stress_type": "向上撞墙", "analysis": "压强爆破"},
        )


def test_fsm_output_rejects_duplicate_bit_analysis_positions():
    with pytest.raises(ValueError, match="B1-B6"):
        FSMOutput(
            inner_system="inner",
            outer_system="outer",
            inner_bits="100",
            outer_bits="010",
            bit_analysis=[
                {"bit_position": 1, "value": "1", "description": "B1"},
                {"bit_position": 1, "value": "1", "description": "B1 duplicate"},
                {"bit_position": 2, "value": "0", "description": "B2"},
                {"bit_position": 3, "value": "0", "description": "B3"},
                {"bit_position": 4, "value": "0", "description": "B4"},
                {"bit_position": 5, "value": "1", "description": "B5"},
            ],
            energy_focus={"focus_bit": 2, "focus_description": "B2 focus"},
            stress_analysis={"stress_type": "向上撞墙", "analysis": "pressure"},
        )


def test_fsm_output_bit_analysis_values_must_match_final_bits():
    with pytest.raises(ValueError, match="must match"):
        FSMOutput(
            inner_system="inner",
            outer_system="outer",
            inner_bits="100",
            outer_bits="010",
            bit_analysis=[
                {"bit_position": 1, "value": "0", "description": "B1 mismatch"},
                {"bit_position": 2, "value": "0", "description": "B2"},
                {"bit_position": 3, "value": "0", "description": "B3"},
                {"bit_position": 4, "value": "0", "description": "B4"},
                {"bit_position": 5, "value": "1", "description": "B5"},
                {"bit_position": 6, "value": "0", "description": "B6"},
            ],
            energy_focus={"focus_bit": 2, "focus_description": "B2 focus"},
            stress_analysis={"stress_type": "向上撞墙", "analysis": "pressure"},
        )


def test_path1_route_uses_first_hard_interrupt_not_max_stress_only():
    state = FSMState.from_physics(
        bits="101010",
        E=[1.0, 0.8, 0.15, 0.7, 0.4, 0.9],
        P=[0.1, 0.2, 0.3, 0.95, 0.2, 0.1],
        R=[0.1, 0.1, 0.12, 0.1, 0.1, 0.1],
        tau=[1, 1, 1, 1, 1, 1],
        C=[0.15, 0.15, 0.15, 0.15, 0.15, 0.15],
    )

    snapshot = physics_snapshot(state)

    assert snapshot["route"]["path_number"] == 1
    assert snapshot["interrupt"]["next_bits"] == snapshot["route"]["next_bits"]
    assert snapshot["selected_next_bits"] == snapshot["interrupt"]["next_bits"]
    assert snapshot["route"]["result"]["next_state"].R == state.R


def test_path4_meta_reset_exposes_alternatives_without_single_selected_next():
    state = FSMState.from_physics(
        bits="100001",
        E=[1, 1, 1, 1, 1, 1],
        P=[0, 0, 0, 0, 0, 0],
        R=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
        tau=[1, 1, 1, 1, 1, 1],
    )

    snapshot = physics_snapshot(state, deadlock_flag=True)

    assert snapshot["route"]["path_number"] == 4
    assert snapshot["route"]["next_bits"] is None
    assert snapshot["selected_next_bits"] is None
    assert {item["operation"] for item in snapshot["route"]["alternatives"]} == {"错卦（全翻）", "综卦（倒置）"}
