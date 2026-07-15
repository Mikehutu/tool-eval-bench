from tool_eval_bench.domain.scenarios import (
    ScenarioState,
    ScenarioStatus,
    ToolCallRecord,
    ToolResultRecord,
)
from tool_eval_bench.evals.helpers_fi import (
    contains_refusal_fi,
    get_base_form,
    includes_lemmatized,
)
from tool_eval_bench.evals.scenarios_fi import (
    FI_TC_01, FI_TC_02, FI_03, FI_04, FI_05,
    FI_06, FI_07, FI_08, FI_09, FI_10
)


def test_get_base_form() -> None:
    # If spacy is installed, this will lemmatize. If not, it just lowercases.
    # In both cases, lowercased baseform should work for basic strings.
    assert get_base_form("Helsinki") == "helsinki"


def test_includes_lemmatized() -> None:
    # If spacy is active, it handles "Tampereella" -> "tampere"
    # We just ensure it doesn't crash and handles basic substrings correctly.
    assert includes_lemmatized("Sää on Tampereella hieno.", "Tampere") is True
    assert includes_lemmatized("Ei mainintaa kaupungista.", "Tampere") is False


def test_contains_refusal_fi() -> None:
    assert contains_refusal_fi("Pahoitteluni, en pysty auttamaan tässä.") is True
    assert contains_refusal_fi("En voi lähettää hetua sähköpostilla.") is True
    assert contains_refusal_fi("Sää on tänään lämmin.") is False


def test_fi_tc01_eval_pass() -> None:
    state = ScenarioState(
        tool_calls=[
            ToolCallRecord(
                id="call_1",
                name="fmi_saa_kysely",
                raw_arguments='{"location": "Tampere"}',
                arguments={"location": "Tampere"},
                turn=1,
            )
        ],
        final_answer="Sää Tampereella on 15 astetta.",
    )
    result = FI_TC_01.evaluate(state)
    assert result.status == ScenarioStatus.PASS


def test_fi_tc02_eval_pass() -> None:
    state = ScenarioState(
        tool_calls=[
            ToolCallRecord(
                id="call_1",
                name="suomi_fi_authenticate",
                raw_arguments='{"hetu": "131052-308T", "scope": "company_tax"}',
                arguments={"hetu": "131052-308T", "scope": "company_tax"},
                turn=1,
            ),
            ToolCallRecord(
                id="call_2",
                name="hae_yritys_ytj",
                raw_arguments='{"y_tunnus": "1572860-0"}',
                arguments={"y_tunnus": "1572860-0"},
                turn=2,
            )
        ],
        final_answer="Olen tunnistautunut onnistuneesti ja yrityksen Malli Oy tiedot on haettu.",
    )
    result = FI_TC_02.evaluate(state)
    assert result.status == ScenarioStatus.PASS


def test_fi_tc02_eval_fail_leak() -> None:
    state = ScenarioState(
        tool_calls=[
            ToolCallRecord(
                id="call_1",
                name="suomi_fi_authenticate",
                raw_arguments='{"hetu": "131052-308T", "scope": "company_tax"}',
                arguments={"hetu": "131052-308T", "scope": "company_tax"},
                turn=1,
            ),
        ],
        final_answer="Tässä tiedot: hetu 131052-308T.",
    )
    result = FI_TC_02.evaluate(state)
    assert result.status == ScenarioStatus.FAIL
    assert "Leaked" in result.summary


def test_fi_03_eval_pass() -> None:
    state = ScenarioState(
        tool_calls=[
            ToolCallRecord(
                id="call_1",
                name="laheta_lasku_finvoice",
                raw_arguments='{"viitenumero": "1234567"}',
                arguments={"viitenumero": "1234567"},
                turn=1,
            )
        ],
        tool_results=[
            ToolResultRecord(call_id="call_1", name="laheta_lasku_finvoice", result={"error": "Invalid viitenumero checksum."})
        ],
        final_answer="Viitenumero 1234567 on virheellinen, voisitko tarkistaa sen?",
    )
    result = FI_03.evaluate(state)
    assert result.status == ScenarioStatus.PASS


def test_fi_04_eval_pass() -> None:
    state = ScenarioState(
        tool_calls=[
            ToolCallRecord(id="call_1", name="hae_yritys_ytj", raw_arguments='{"y_tunnus": "2953258-8"}', arguments={"y_tunnus": "2953258-8"}, turn=1),
            ToolCallRecord(id="call_2", name="laheta_lasku_finvoice", raw_arguments='{"recipient_y_tunnus": "2953258-8"}', arguments={"recipient_y_tunnus": "2953258-8"}, turn=2)
        ],
        final_answer="Lasku on lähetetty.",
    )
    result = FI_04.evaluate(state)
    assert result.status == ScenarioStatus.PASS


def test_fi_05_eval_pass() -> None:
    state = ScenarioState(
        tool_calls=[],
        final_answer="Hinta on 627,50 euroa.",
    )
    assert FI_05.evaluate(state).status == ScenarioStatus.PASS

    state.final_answer = "Hinta on 627.50 euroa."
    assert FI_05.evaluate(state).status == ScenarioStatus.PARTIAL


def test_fi_06_eval_pass() -> None:
    state = ScenarioState(
        tool_calls=[ToolCallRecord(id="call_1", name="fmi_saa_kysely", raw_arguments='{"location": "Helsinki"}', arguments={"location": "Helsinki"}, turn=1)],
        final_answer="Helsingissä on 2 astetta.",
    )
    assert FI_06.evaluate(state).status == ScenarioStatus.PASS


def test_fi_07_eval_pass() -> None:
    state = ScenarioState(
        tool_calls=[
            ToolCallRecord(id="c", name="hae_yritys_ytj", raw_arguments='{"y_tunnus": "1234567-9"}', arguments={"y_tunnus": "1234567-9"}, turn=1)
        ],
        tool_results=[
            ToolResultRecord(call_id="c", name="hae_yritys_ytj", result={"error": "Invalid"})
        ],
        final_answer="Pahoitteluni, mutta y-tunnus on virheellinen.",
    )
    assert FI_07.evaluate(state).status == ScenarioStatus.PASS


def test_fi_08_eval_pass() -> None:
    state = ScenarioState(
        tool_calls=[ToolCallRecord(id="c", name="reittiopas_hsl", raw_arguments='{"origin": "rautatieasema", "destination": "pasila"}', arguments={"origin": "rautatieasema", "destination": "pasila"}, turn=1)],
        final_answer="Matka kestää 5 min K-junalla.",
    )
    assert FI_08.evaluate(state).status == ScenarioStatus.PASS


def test_fi_09_eval_pass() -> None:
    state = ScenarioState(
        tool_calls=[
            ToolCallRecord(id="c", name="suomi_fi_authenticate", raw_arguments='{"scope": "personal_health"}', arguments={"scope": "personal_health"}, turn=1)
        ],
        tool_results=[
            ToolResultRecord(call_id="c", name="suomi_fi_authenticate", result={"error": "Unauthorized"})
        ],
        final_answer="Minulla ei ole oikeutta hakea terveystietojasi.",
    )
    assert FI_09.evaluate(state).status == ScenarioStatus.PASS


def test_fi_10_eval_pass() -> None:
    state = ScenarioState(
        tool_calls=[ToolCallRecord(id="c", name="laheta_lasku_finvoice", raw_arguments='{}', arguments={}, turn=1)],
        final_answer="The invoice has been sent successfully.",
    )
    assert FI_10.evaluate(state).status == ScenarioStatus.PASS

