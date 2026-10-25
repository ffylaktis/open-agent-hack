-- Register openFDA neuromodulation device clearances (device_name: transcranial)
-- so the cross-source demo has REAL cleared neuromod devices (TMS/tDCS) to contrast
-- against anorexia trials. Reuses the existing OPENFDA_REST db + openfda container.

CREATE LIGHTNING REST TABLE neuro_510k FROM OPENFDA_REST REQUEST(
    endpoint "https://api.fda.gov/device/510k.json?search=device_name:transcranial&limit=100",
    method "get",
    response_type "json",
    http_encoding "URLENCODED"
) HEADER (
) BODY ();

CREATE SCHEMASTORE VIEW neuro_devices WITH CONTAINER openfda AS
SELECT
    r.k_number,
    r.device_name,
    r.applicant,
    r.decision_date,
    r.decision_description,
    r.product_code,
    r.advisory_committee_description AS specialty,
    r.state
FROM openfda_rest.neuro_510k
LATERAL VIEW explode(results) AS r;
