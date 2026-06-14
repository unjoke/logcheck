## ADDED Requirements

### Requirement: Demonstrate realistic access-log attack detection
The project SHALL include coursework evidence that the supplied middleware access-log example is handled as a realistic local attack fixture.

#### Scenario: Access1 is covered by automated verification
- **WHEN** automated verification for detection rules is run
- **THEN** tests cover `samples/access1.log` or an equivalent fixture derived from it and assert that repeated SQL injection behavior is detected

#### Scenario: Access1 remains local-only evidence
- **WHEN** the access-log detection example is demonstrated
- **THEN** the evidence shows local file analysis and does not add URL/domain inputs, remote fetching, scanning, exploitation, blocking, or external reporting controls

#### Scenario: Example log intent is documented
- **WHEN** coursework documentation or sample listings describe bundled logs
- **THEN** `access1.log` is identified as a middleware access-log SQL injection enumeration example rather than a generic access log
