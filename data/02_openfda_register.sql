-- Register openFDA device 510(k) clearances (AI-named) as a Lightning REST source.
-- Public API, no key. Same pattern as the CT.gov recipe.

CREATE LIGHTNING DATABASE OPENFDA_REST DESCRIBE BY "openFDA device 510k clearances REST source";

CREATE SCHEMASTORE CONTAINER openfda;

CREATE LIGHTNING REST TABLE ai_510k FROM OPENFDA_REST REQUEST(
    endpoint "https://api.fda.gov/device/510k.json?search=device_name:artificial+intelligence&limit=100",
    method "get",
    response_type "json",
    http_encoding "URLENCODED"
) HEADER (
) BODY ();

CREATE SCHEMASTORE VIEW ai_devices WITH CONTAINER openfda AS
SELECT
    r.k_number,
    r.device_name,
    r.applicant,
    r.decision_date,
    r.decision_description,
    r.product_code,
    r.clearance_type,
    r.advisory_committee_description AS specialty,
    r.state
FROM openfda_rest.ai_510k
LATERAL VIEW explode(results) AS r;
