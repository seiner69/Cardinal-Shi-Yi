import pytest

from fastapi import HTTPException

from src.api import PhysicsRequest, PhysicsUncertainty, build_physics_seed, node, physics, simulate
from src.fsm_kernel import (
    FSMState,
    HEXAGRAM_LOOKUP,
    HEX_STATES,
    e_dimension,
    get_hex_state,
    get_hexagram_name,
    monte_carlo_state_distribution,
    path2_hidden_core_exposure,
    physics_snapshot,
    raw_physics_step,
    tensor_for_bit,
    uncertainty_confidence,
)
from src.models.schema import FSMOutput
from src.data.hexagrams import HEXAGRAM_DATA


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
            {"bit_position": 2, "value": "0", "description": "补给断供，燃料耗尽，压力集中"},
            {"bit_position": 5, "value": "1", "description": "外部监管挤压，存在资源支撑"},
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
