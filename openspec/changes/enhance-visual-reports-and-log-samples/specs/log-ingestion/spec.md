## ADDED Requirements

### Requirement: Provide representative bundled sample logs
The log ingestion capability SHALL include representative bundled sample logs that exercise web access, authentication, and application-security analysis paths.

#### Scenario: Sample listing includes representative logs
- **WHEN** the local web app lists bundled samples
- **THEN** the list includes sample logs covering access-log attacks, authentication failures, and application security events
- **AND** each listed sample can be selected for local analysis

#### Scenario: Access sample supports visual reporting
- **WHEN** the user analyzes the bundled access-log sample set
- **THEN** the resulting findings include enough source-address and timestamp diversity to populate source IP and time distribution charts

#### Scenario: Samples remain inert text
- **WHEN** bundled samples contain exploit-like payload strings
- **THEN** the payloads remain inert log text
- **AND** analyzing them does not send requests to the payload domains or addresses

### Requirement: Generate access-log variants from local seed data
The log ingestion capability SHALL support creating curated access-log sample variants from the existing `access1.log` seed data.

#### Scenario: Generated variants preserve parseable format
- **WHEN** access-log variants are generated from `access1.log`
- **THEN** the generated lines preserve a parser-supported access-log format
- **AND** timestamps, source addresses, paths, status codes, and user agents remain available for analysis

#### Scenario: Temporary generation artifacts stay in worktmp
- **WHEN** scripts or intermediate files are used to create sample variants
- **THEN** temporary artifacts are stored under `worktmp/` by default
- **AND** only curated final sample logs are promoted into `samples/`

#### Scenario: Sample generation is deterministic enough for tests
- **WHEN** tests analyze curated generated samples
- **THEN** the expected source-address and time-distribution characteristics are stable across test runs
