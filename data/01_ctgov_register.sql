-- Register ClinicalTrials.gov v2 (anorexia nervosa) as a Lightning REST source.
-- Pattern copied from Zetaris getting-started PokeAPI recipe.
-- Run one statement at a time (the runner handles this).

CREATE LIGHTNING DATABASE CTGOV_REST DESCRIBE BY "ClinicalTrials.gov v2 REST source";

CREATE SCHEMASTORE CONTAINER ctgov;

CREATE LIGHTNING REST TABLE an_studies FROM CTGOV_REST REQUEST(
    endpoint "https://clinicaltrials.gov/api/v2/studies?query.cond=anorexia+nervosa&pageSize=100&fields=protocolSection",
    method "get",
    response_type "json",
    http_encoding "URLENCODED"
) HEADER (
) BODY ();

CREATE SCHEMASTORE VIEW trials WITH CONTAINER ctgov AS
SELECT
    s.protocolSection.identificationModule.nctId AS nct_id,
    s.protocolSection.identificationModule.briefTitle AS title,
    s.protocolSection.statusModule.overallStatus AS status,
    s.protocolSection.designModule.phases AS phases,
    s.protocolSection.conditionsModule.conditions AS conditions,
    s.protocolSection.sponsorCollaboratorsModule.leadSponsor.name AS lead_sponsor,
    s.protocolSection.descriptionModule.briefSummary AS summary
FROM ctgov_rest.an_studies
LATERAL VIEW explode(studies) AS s;

CREATE SCHEMASTORE VIEW interventions WITH CONTAINER ctgov AS
SELECT
    s.protocolSection.identificationModule.nctId AS nct_id,
    i.type AS intervention_type,
    i.name AS intervention_name
FROM ctgov_rest.an_studies
LATERAL VIEW explode(studies) AS s
LATERAL VIEW explode(s.protocolSection.armsInterventionsModule.interventions) AS i;
