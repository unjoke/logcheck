## ADDED Requirements

### Requirement: Rebuild the workbench around adjacent finding and evidence review
The web frontend SHALL make finding selection and selected log detail the primary adjacent investigation workflow.

#### Scenario: Desktop keeps queue and detail adjacent
- **WHEN** the dashboard is displayed on a desktop-width viewport
- **THEN** the finding queue and selected log detail are visible as adjacent regions in the primary investigation lane
- **AND** the visual report does not sit between the queue and the selected log detail

#### Scenario: Mobile keeps queue and detail sequential
- **WHEN** the dashboard is displayed on a mobile-width viewport
- **THEN** the finding queue appears directly before the selected log detail in reading order
- **AND** charts, exports, and secondary insights do not separate the selected finding from its raw evidence

#### Scenario: Visual report supports investigation instead of displacing it
- **WHEN** the visual report is rendered
- **THEN** it appears as a supporting summary surface below or beside the primary investigation lane
- **AND** it does not push the finding queue below the first-screen evidence workflow on desktop layouts

### Requirement: Paginate local finding queue
The web frontend SHALL paginate the local finding queue when analysis results contain more findings than the configured page size.

#### Scenario: Finding queue shows first page
- **WHEN** a local analysis result contains more findings than fit on one page
- **THEN** the finding queue displays only the first page of findings
- **AND** pagination controls show the current page and total pages

#### Scenario: Changing finding page updates visible findings
- **WHEN** the user moves to another finding page
- **THEN** the queue updates to show findings for that page
- **AND** the selected finding is either preserved when still visible or reset to the first finding on the new page

#### Scenario: Pagination respects filtered results
- **WHEN** a keyword or facet filter is active
- **THEN** pagination is calculated from the filtered finding set
- **AND** clearing the filter restores pagination for the full local result

### Requirement: Switch workbench language between Chinese and English
The web frontend SHALL provide a visible language control that switches core workbench interface text between English and Chinese without re-running local analysis.

#### Scenario: Switch to Chinese
- **WHEN** the user chooses Chinese from the language control
- **THEN** navigation labels, analysis status, finding queue labels, filter labels, chart labels, empty states, and export/status messages render in Chinese

#### Scenario: Switch to English
- **WHEN** the user chooses English from the language control
- **THEN** navigation labels, analysis status, finding queue labels, filter labels, chart labels, empty states, and export/status messages render in English

#### Scenario: Analysis data remains unchanged by language switch
- **WHEN** the user changes the interface language after analysis has completed
- **THEN** the selected local result, findings, evidence, charts, and filters remain available
- **AND** only display labels and helper text change language

### Requirement: Show explicit time distribution chart
The web frontend SHALL display an explicit time-distribution chart in the visual report for the latest local analysis result.

#### Scenario: Time chart uses parsed timestamps
- **WHEN** findings include parsed timestamps
- **THEN** the visual report shows a time-distribution chart bucketed by timestamp
- **AND** each bucket shows the number of local findings in that time range

#### Scenario: Time chart falls back to evidence order
- **WHEN** findings do not include parsed timestamps
- **THEN** the visual report still shows a time-distribution chart using deterministic evidence or source order
- **AND** the chart label clearly indicates that the distribution is based on evidence order rather than actual timestamps

#### Scenario: Time chart empty state
- **WHEN** no analysis has run or the latest analysis has no findings
- **THEN** the time-distribution chart area shows a localized empty state instead of stale or broken chart content

### Requirement: Display detailed attacker IP statistics
The web frontend SHALL display detailed local attacker IP statistics derived from findings with source addresses.

#### Scenario: Attacker IP table includes investigation fields
- **WHEN** local findings include source addresses
- **THEN** the attacker IP statistics show each source address with finding count, severity mix, related rules, top target or actor values, first and last observed time or source reference, and representative evidence access

#### Scenario: Selecting attacker IP narrows review context
- **WHEN** the user selects an attacker IP statistic row or chart item
- **THEN** the finding queue can be filtered or focused to findings associated with that source address
- **AND** the selected finding detail remains tied to local source evidence

#### Scenario: Attacker IP statistics are not generic entity frequency
- **WHEN** local findings include source addresses
- **THEN** attacker IP statistics are displayed in a dedicated area labeled for attacker/source IP review
- **AND** the area includes investigation fields rather than only a bar count

#### Scenario: No source addresses are available
- **WHEN** local findings do not include source addresses
- **THEN** the attacker IP statistics area shows a localized empty state
- **AND** it does not invent remote enrichment or external lookup data

### Requirement: Filter findings by keyword and facets
The web frontend SHALL let users filter local findings by keyword text and common structured facets.

#### Scenario: Keyword searches structured and evidence fields
- **WHEN** the user enters a keyword filter
- **THEN** the finding queue filters across rule id, severity, source file, source address, actor, target, matched keyword, explanation, and evidence text
- **AND** matching remains local to the current analysis result

#### Scenario: Filter supports normalized log text
- **WHEN** evidence contains variable tokens such as addresses, numbers, paths, or timestamps
- **THEN** keyword filtering can still match useful normalized message text where implemented
- **AND** raw evidence remains visible in the selected finding detail

#### Scenario: Facets combine with keyword search
- **WHEN** the user chooses severity, rule, source address, or similar local facets together with a keyword
- **THEN** the displayed findings satisfy all active filters
- **AND** pagination updates to the filtered result count

### Requirement: Adapt external project strengths without runtime dependency or copying
The web frontend SHALL adapt useful investigation patterns from FastWLAT and MaaLogAnalyzer only as original Logcheck behavior.

#### Scenario: FastWLAT-style strengths are adapted locally
- **WHEN** the redesigned workbench presents summaries, filters, and source analysis
- **THEN** it may use multi-dimensional local filters, rule-category review, and dashboard-level summaries inspired by FastWLAT
- **AND** it does not copy FastWLAT source code, visual styling, maps, GeoIP behavior, or Electron/Vue architecture

#### Scenario: MaaLogAnalyzer-style strengths are adapted locally
- **WHEN** the redesigned workbench presents finding details and evidence context
- **THEN** it may use master-detail review, split evidence comparison, search result context jumps, and parser/projection separation ideas inspired by MaaLogAnalyzer
- **AND** it does not copy MaaLogAnalyzer source code, package structure, UI components, or framework architecture

### Requirement: Preserve local-only workbench safety during analytics enhancements
The web frontend MUST keep all pagination, localization, charting, IP statistics, and filtering behavior local-only.

#### Scenario: No remote controls are added
- **WHEN** the enhanced workbench is displayed
- **THEN** it does not show URL inputs, domain inputs, remote upload controls, network scan buttons, blocking controls, exploitation actions, GeoIP/map controls, external lookup buttons, or external reporting controls

#### Scenario: No runtime research fetch is required
- **WHEN** the user filters findings or views chart/statistic panels
- **THEN** the workbench does not fetch papers, GitHub projects, CDNs, threat intelligence, or external enrichment services
